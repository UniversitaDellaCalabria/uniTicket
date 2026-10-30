import importlib
import os
import sys
import tempfile
import types
import zipfile
import io

from unittest import mock

from django import forms
from django.conf import settings
from django.contrib import admin as django_admin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import clear_url_caches, reverse
from django.utils import timezone

from uni_ticket import admin_actions, jwts, pdf_utils
from uni_ticket.admin import TaskAdmin
from uni_ticket.dynamic_form import serialize_form
from uni_ticket.forms import (
    AssignTicketToOperatorForm,
    TicketDependenceForm,
)
from uni_ticket.models import (
    Log,
    Task,
    Ticket,
    TicketAssignment,
    TicketCategory,
    TicketCategoryCondition,
    TicketReply,
)
from uni_ticket.statistics import uniTicketStats
from uni_ticket.templatetags import uni_ticket_tags as tags
from uni_ticket.validators import (
    validate_file_extension,
    validate_file_length,
    validate_file_size,
)
from uni_ticket_bootstrap_italia_template.templatetags import (
    uni_ticket_bootstrap_italia_tags as bi_tags,
)

from .test_16_models import ORMFixtureMixin


class Test_Validators(TestCase):

    def _file(self, name="f.pdf", size=10, content_type="application/pdf"):
        f = mock.Mock()
        f.name = name
        f.size = size
        f.file = mock.Mock(content_type=content_type)
        return f

    def test_validate_file_extension(self):
        validate_file_extension(self._file())
        with self.assertRaises(ValidationError):
            validate_file_extension(self._file(content_type="application/x-evil"))
        # files without content_type are not checked
        f = self._file()
        f.file = object()
        validate_file_extension(f)

    def test_validate_file_size(self):
        validate_file_size(self._file())
        with self.assertRaises(ValidationError):
            validate_file_size(self._file(size=int(settings.MAX_UPLOAD_SIZE) + 1))

    def test_validate_file_length(self):
        validate_file_length(self._file())
        with self.assertRaises(ValidationError):
            validate_file_length(
                self._file(name="a" * (settings.ATTACH_NAME_MAX_LEN + 1))
            )


class Test_Jwts(TestCase):

    def test_encrypt_decrypt(self):
        for content in ({"a": 1}, "text", b"bytes"):
            jwe = jwts.encrypt_to_jwe(content)
            self.assertTrue(jwts.decrypt_from_jwe(jwe))
        self.assertEqual(jwts.decrypt_from_jwe(jwts.encrypt_to_jwe("text")), b"text")

    def test_encrypt_wrong_type(self):
        with self.assertRaises(Exception):
            jwts.encrypt_to_jwe(123)


class Test_PdfUtils(TestCase):

    def _fake_html(self, captured):
        class FakeHTML:
            def __init__(self, string):
                captured["html"] = string

            def write_pdf(self, target):
                with open(target, "wb") as f:
                    f.write(b"%PDF")

        return FakeHTML

    def test_response_as_pdf(self):
        captured = {}
        tmp = tempfile.mkdtemp()
        response = HttpResponse(
            '<link href="{}css/style.css">'.format(settings.STATIC_URL)
        )
        with mock.patch.object(pdf_utils, "HTML", self._fake_html(captured)), \
                override_settings(TMP_DIR=tmp, DEBUG=False):
            pdf = pdf_utils.response_as_pdf(response, "file.pdf")
        self.assertEqual(pdf.content, b"%PDF")
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertIn(
            "https://{}{}css/style.css".format(settings.HOSTNAME, settings.STATIC_URL),
            captured["html"],
        )
        # temporary file has been removed
        self.assertEqual(os.listdir(tmp), [])
        os.rmdir(tmp)

    def test_weasyprint_not_installed(self):
        # reload() keeps the old module globals: remove HTML first
        del pdf_utils.HTML
        try:
            with mock.patch.dict(sys.modules, {"weasyprint": None}), \
                    self.assertLogs("uni_ticket.pdf_utils", level="WARNING"):
                importlib.reload(pdf_utils)
            self.assertFalse(hasattr(pdf_utils, "HTML"))
        finally:
            importlib.reload(pdf_utils)
        self.assertTrue(hasattr(pdf_utils, "HTML"))

    def test_response_as_pdf_asgi_debug(self):
        captured = {}
        tmp = tempfile.mkdtemp()
        html = '<link href="{}css/style.css">'.format(settings.STATIC_URL)
        with mock.patch.object(pdf_utils, "HTML", self._fake_html(captured)), \
                override_settings(TMP_DIR=tmp, DEBUG=True, ASGI_APPLICATION="x"):
            pdf_utils.response_as_pdf(HttpResponse(html), "file.pdf")
        # static urls are not changed
        self.assertEqual(captured["html"], html)
        os.rmdir(tmp)


class Test_BootstrapItaliaTags(TestCase):

    def test_tags(self):
        self.assertTrue(bi_tags.is_list([]))
        self.assertFalse(bi_tags.is_list("a"))
        self.assertEqual(bi_tags.settings_value("HOSTNAME"), settings.HOSTNAME)
        with override_settings(TEST_TEMPLATE="hello {who}"):
            self.assertEqual(
                bi_tags.settings_value("TEST_TEMPLATE", who="world"), "hello world"
            )


class Test_UniTicketTags(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_filename(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            value = mock.Mock(path=f.name)
            value.file.name = f.name
            self.assertEqual(tags.filename(value), os.path.basename(f.name))
        value = mock.Mock(path="/not/existent/file.txt")
        self.assertEqual(str(tags.filename(value)), "Risorsa non più disponibile")

    def test_simple_tags(self):
        self.assertEqual(tags.no_slugged("a_b"), "A b")
        self.assertIn(timezone.localdate().year, tags.year_list())
        self.assertEqual(tags.current_date(), timezone.localtime().date())
        self.assertTrue(tags.simple_user_context_name())
        self.assertFalse(tags.not_a_simple_user(self.user))
        self.assertTrue(tags.user_operator_chat(self.manager, self.structure))
        self.assertTrue(tags.app_is_installed("uni_ticket"))
        self.assertEqual(tags.obj_get_attr({"a": 1}, "a"), 1)
        self.assertEqual(tags.obj_get_attr(self.user, "username"), self.user.username)
        self.assertIn("<strong>", tags.markdown("**a**"))
        self.assertEqual(
            tags.uni_ticket_settings_value("CONTEXT_SIMPLE_USER"),
            tags.simple_user_context_name(),
        )
        with mock.patch.object(tags.uni_ticket_settings, "TEST_VALUE", "{a}", create=True):
            self.assertEqual(tags.uni_ticket_settings_value("TEST_VALUE", a="b"), "b")

    def test_categories_list(self):
        self.assertIn(
            self.category, tags.categories_list(self.structure, self.manager)
        )
        self.assertEqual(
            tags.categories_list(self.structure, self.operator), [self.category]
        )

    def test_get_usertype(self):
        value = tags.get_usertype(self.manager, self.structure)
        self.assertEqual(
            tags.get_usertype(self.manager, self.structure, label_value_tuple=True),
            ("manager", value),
        )

    def test_get_label_from_form(self):
        form = forms.Form()
        form.fields["name"] = forms.CharField(label="Name")
        self.assertEqual(tags.get_label_from_form(form, "name"), ("Name", False))

        # django_form_builder formset fields store columns as plain strings
        table = forms.Field()
        table.choices = ["col1"]
        table.pre_text = "pre"
        form.fields["table"] = table
        self.assertEqual(
            tags.get_label_from_form(form, "table-0-col1"), (False, "pre")
        )
        self.assertFalse(tags.get_label_from_form(form, "table-0-other"))
        self.assertFalse(tags.get_label_from_form(form, "missing"))

    def test_get_dyn_field_name(self):
        self.assertEqual(tags.get_dyn_field_name("unknown"), "unknown")
        self.assertNotEqual(tags.get_dyn_field_name("CustomCharField"), "CustomCharField")

    def test_user_from_pk(self):
        self.assertFalse(tags.user_from_pk(None))
        self.assertEqual(tags.user_from_pk(self.user.pk), self.user)

    def test_ticket_tags(self):
        self.assertFalse(tags.ticket_has_been_taken(self.ticket))
        self.assertFalse(tags.ticket_is_open(self.ticket))

    def test_ticket_can_be_deleted(self):
        assignments = TicketAssignment.objects.filter(ticket=self.ticket)
        t = self.ticket
        self.assertTrue(tags.ticket_can_be_deleted(t, False, assignments, self.user))
        self.assertFalse(tags.ticket_can_be_deleted(t, False, assignments, self.operator))
        self.assertFalse(tags.ticket_can_be_deleted(t, True, assignments, self.user))
        t.is_closed = True
        self.assertFalse(tags.ticket_can_be_deleted(t, False, assignments, self.user))
        t.compiled_by = self.operator
        self.assertFalse(tags.ticket_can_be_deleted(t, False, assignments, self.user))

    def test_ticket_can_be_deleted_multiple_assignments(self):
        TicketAssignment.objects.create(ticket=self.ticket, office=self.default_office)
        assignments = TicketAssignment.objects.filter(ticket=self.ticket)
        self.assertFalse(
            tags.ticket_can_be_deleted(self.ticket, False, assignments, self.user)
        )

    def test_ticket_can_be_edited(self):
        t = self.ticket
        self.assertTrue(tags.ticket_can_be_edited(t, False, self.user))
        self.assertFalse(tags.ticket_can_be_edited(t, False, self.operator))
        self.assertFalse(tags.ticket_can_be_edited(t, True, self.user))
        t.is_closed = True
        self.assertFalse(tags.ticket_can_be_edited(t, False, self.user))

    def test_ticket_can_be_closed_from_user(self):
        t = self.ticket
        self.assertTrue(tags.ticket_can_be_closed_from_user(t, self.user))
        self.assertFalse(tags.ticket_can_be_closed_from_user(t, self.operator))
        t.draft = True
        self.assertFalse(tags.ticket_can_be_closed_from_user(t, self.user))
        t.compiled_by = self.operator
        self.assertTrue(tags.ticket_can_be_closed_from_user(t, self.user))
        t.is_closed = True
        self.assertFalse(tags.ticket_can_be_closed_from_user(t, self.user))


class Test_Signals(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    @mock.patch("uni_ticket.signals.delete_file")
    @mock.patch("uni_ticket.signals.delete_directory")
    def test_delete_attachments(self, mocked_dir, mocked_file):
        reply = TicketReply.objects.create(
            ticket=self.ticket, owner=self.user, subject="s", text="t"
        )
        reply.delete()
        mocked_file.assert_called_once()
        folder = self.ticket.get_folder()
        self.ticket.delete()
        mocked_dir.assert_any_call(folder)


class Test_Forms(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def _dependence_form(self, code, user, **kwargs):
        return TicketDependenceForm(
            data={"ticket": code, "note": "n"},
            user=user,
            structure=self.structure,
            ticket_code=kwargs.get("ticket_code", "current"),
            ticket_dependences=kwargs.get("ticket_dependences", []),
        )

    def test_ticket_dependence_form(self):
        code = str(self.ticket.code)
        form = self._dependence_form(code, self.manager, ticket_code=code)
        self.assertFalse(form.is_valid())

        form = self._dependence_form(code, self.manager, ticket_dependences=[code])
        self.assertFalse(form.is_valid())

        form = self._dependence_form("not-existent", self.manager)
        self.assertFalse(form.is_valid())

        form = self._dependence_form(code, self.manager)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["ticket"], self.ticket)

    def test_ticket_dependence_form_operator(self):
        code = str(self.ticket.code)
        # ticket not yet taken
        form = self._dependence_form(code, self.operator)
        self.assertFalse(form.is_valid())

        self.assignment.taken_date = timezone.localtime()
        self.assignment.taken_by = self.operator
        self.assignment.save()
        form = self._dependence_form(code, self.operator)
        self.assertTrue(form.is_valid())

    def test_assign_ticket_to_operator_form(self):
        form = AssignTicketToOperatorForm(
            structure=self.structure, office=self.office, current_user=self.manager
        )
        self.assertEqual(list(form.fields["assign_to"].queryset), [self.operator])


class Test_DynamicForm(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_conditions_and_captcha(self):
        TicketCategoryCondition.objects.create(
            category=self.category, title="cond", text="text"
        )
        form = self.module.get_form(show_conditions=True, current_user=AnonymousUser())
        names = list(form.fields.keys())
        self.assertTrue(any("condizioni" in n or "conditions" in n for n in names) or
                        len(names) > 2)
        # captcha fields are added for anonymous users
        self.assertTrue(any("captcha" in n for n in names))

    def test_serialize_form(self):
        class SampleForm(forms.Form):
            date = forms.DateField(widget=forms.DateInput)
            date_time = forms.DateTimeField(widget=forms.DateTimeInput)
            simple = forms.ChoiceField(choices=[("a", "A"), ("c", "C")])
            multiple = forms.MultipleChoiceField(choices=[("x", "X")])
            category = forms.ModelChoiceField(queryset=TicketCategory.objects.all())
            text = forms.CharField(widget=forms.Textarea, required=False)

        fields = {f["id"]: f for f in serialize_form(SampleForm())}
        self.assertEqual(fields["date"]["type"], "date")
        self.assertEqual(fields["date_time"]["type"], "datetime")
        self.assertEqual(fields["simple"]["type"], "select")
        self.assertEqual(
            [o["value"] for o in fields["simple"]["options"]], ["a", "c"]
        )
        self.assertEqual(fields["multiple"]["multiple"], 1)
        self.assertEqual(
            fields["category"]["options"],
            [{"text": str(self.category), "value": self.category.pk}],
        )
        self.assertEqual(fields["text"]["type"], "textarea")
        self.assertFalse(fields["text"]["required"])

    def test_get_choices_grouped(self):
        from uni_ticket.dynamic_form import _get_choices
        choices = [("Group", (("a", "A"), ("b", "B"))), ("c", "C")]
        self.assertEqual(
            [o["value"] for o in _get_choices(choices)], ["a", "b", "c"]
        )
        # Django >= 5 normalizes grouped choices as lists
        normalized = [("Group", [("a", "A"), ("b", "B")]), ("c", "C")]
        self.assertEqual(
            _get_choices(normalized),
            [{"text": "A", "value": "a"},
             {"text": "B", "value": "b"},
             {"text": "C", "value": "c"}],
        )

    def test_serialize_form_grouped_choices(self):
        class GroupedForm(forms.Form):
            grouped = forms.ChoiceField(
                choices=[("Group", (("a", "A"), ("b", "B"))), ("c", "C")]
            )

        field = serialize_form(GroupedForm())[0]
        self.assertEqual(field["type"], "select")
        self.assertEqual([o["value"] for o in field["options"]], ["a", "b", "c"])


class Test_Statistics(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_stats(self):
        now = timezone.now()
        # notification ticket
        self.make_ticket("Notification", self.module, self.user, is_notification=True)
        # ticket closed by the user himself
        self.make_ticket(
            "Self closed", self.module, self.user,
            is_closed=True, closed_date=now,
        )
        # closed by operator
        self.make_ticket(
            "Op closed", self.module, self.user,
            is_closed=True, closed_date=now, closed_by=self.operator,
            assigned_date=now,
        )
        # reopened ticket
        self.ticket.closed_date = now - timezone.timedelta(hours=1)
        self.ticket.save()
        Log.objects.log_action(
            user_id=self.operator.pk,
            content_type_id=__import__(
                "django.contrib.contenttypes.models", fromlist=["ContentType"]
            ).ContentType.objects.get_for_model(Ticket).pk,
            object_id=self.ticket.pk,
            object_repr=str(self.ticket),
            action_flag=2,
            change_message="reopen",
        )
        TicketReply.objects.create(
            ticket=self.ticket, owner=self.operator, subject="s", text="t"
        )

        stats = uniTicketStats(
            structure_slug=self.structure.slug,
            office_slug=[self.office.slug],
            category_slug=[self.category.slug],
            date_end=now + timezone.timedelta(hours=1),
        )
        stats.load()
        self.assertEqual(stats.notifications, 1)
        # tickets with a closed_date in range (the reopened one too)
        self.assertEqual(stats.closed, 3)
        self.assertEqual(stats.closed_by_users, 2)
        self.assertEqual(stats.closed_by_ops, {str(self.operator): 1})
        self.assertEqual(stats.reopened, 1)
        self.assertEqual(stats.open, 4)
        self.assertIn(self.operator.pk, list(stats.get_operators_pks()))


class Test_Admin(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_task_admin(self):
        model_admin = TaskAdmin(Task, django_admin.site)
        self.assertFalse(model_admin.has_add_permission(RequestFactory().get("/")))

    def test_download_report_csv(self):
        queryset = TicketCategory.objects.filter(pk=self.category.pk)
        response = admin_actions.download_report_csv(None, None, queryset)
        self.assertIn(self.category.name, response["Content-Disposition"])

        self.make_category("Category B", self.structure, self.office)
        self.make_category("Category C", self.structure, self.office)
        queryset = TicketCategory.objects.all()
        with mock.patch(
            "uni_ticket.admin_actions.export_category_zip",
            side_effect=[HttpResponse(b"zip"), Exception("err"), HttpResponse(b"zip")],
        ):
            response = admin_actions.download_report_csv(None, None, queryset)
        self.assertIn("uniticket_", response["Content-Disposition"])
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        # the failing category is skipped
        self.assertEqual(len(archive.namelist()), 2)


class Test_ProjectUrls(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_test500(self):
        from uni_ticket_project.urls import test500
        self.client.force_login(self.user)
        with self.assertRaises(Exception):
            self.client.get(reverse("test500"))
        request = mock.Mock(spec=["user"])
        request.user = self.user
        self.assertEqual(test500(request).status_code, 500)

    def _reload_urls(self):
        import uni_ticket.urls
        import uni_ticket_project.urls
        importlib.reload(uni_ticket.urls)
        importlib.reload(uni_ticket_project.urls)
        clear_url_caches()
        return uni_ticket_project.urls

    def _fake_package(self, name, urls_app_name=None):
        pkg = types.ModuleType(name)
        pkg.__path__ = []
        urls = types.ModuleType("{}.urls".format(name))
        urls.urlpatterns = []
        if urls_app_name:
            urls.app_name = urls_app_name
        pkg.urls = urls
        return {name: pkg, "{}.urls".format(name): urls}

    def _route_names(self, urls_module):
        names = []
        for p in urls_module.urlpatterns:
            names.append(getattr(p, "name", None))
        return names

    def test_optional_apps_urls(self):
        apps = list(settings.INSTALLED_APPS) + ["saml2_sp", "djangosaml2", "chat"]
        fake_modules = {}
        fake_modules.update(self._fake_package("saml2_sp", "saml2_sp"))
        fake_modules.update(self._fake_package("chat", "chat"))
        try:
            with mock.patch.dict(sys.modules, fake_modules), \
                    mock.patch.object(settings, "INSTALLED_APPS", apps), \
                    override_settings(DEBUG=True, SAML2_URL_PREFIX="saml2"):
                urls_module = self._reload_urls()
                names = self._route_names(urls_module)
                import uni_ticket.urls
                ut_names = self._route_names(uni_ticket.urls)
            self.assertIn("saml2_acs", names)
            self.assertIn("saml2_metadata", names)
            self.assertIn("new_chat_preload", ut_names)
        finally:
            self._reload_urls()

    def test_spid_oidc_rp_urls(self):
        apps = list(settings.INSTALLED_APPS) + ["spid_oidc_rp"]
        try:
            with mock.patch.dict(sys.modules, self._fake_package("spid_oidc_rp")), \
                    mock.patch.object(settings, "INSTALLED_APPS", apps):
                urls_module = self._reload_urls()
                names = self._route_names(urls_module)
            self.assertIn("login", names)
            self.assertIn("logout", names)
        finally:
            self._reload_urls()

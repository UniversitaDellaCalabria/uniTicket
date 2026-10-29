import csv
import io
import json
import os
import shutil
import tempfile
import zipfile

from unittest import mock

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, QueryDict
from django.test import RequestFactory, TestCase, override_settings

from organizational_area.models import OrganizationalStructureOfficeEmployee
from uni_ticket import utils
from uni_ticket.models import TicketAssignment, TicketCategoryInputList

from .test_16_models import ORMFixtureMixin


class Test_RolesUtils(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()
        cls.superuser = cls.make_user("Super", is_superuser=True)

    def test_user_manage_something(self):
        self.assertFalse(utils.user_manage_something(None))
        self.assertFalse(utils.user_manage_something(self.user))
        self.assertEqual(utils.user_manage_something(self.operator), [self.structure])
        self.assertEqual(
            utils.user_manage_something(self.superuser),
            [self.structure, self.structure_b],
        )

    def test_user_is_manager(self):
        self.assertFalse(utils.user_is_manager(None, self.structure))
        self.assertFalse(utils.user_is_manager(self.manager, None))
        self.assertTrue(utils.user_is_manager(self.superuser, self.structure))
        self.assertTrue(utils.user_is_manager(self.manager, self.structure))
        self.assertFalse(utils.user_is_manager(self.operator, self.structure))

    def test_user_is_in_default_office(self):
        self.assertFalse(utils.user_is_in_default_office(None, self.structure))
        self.assertTrue(utils.user_is_in_default_office(self.superuser, self.structure))
        self.assertFalse(utils.user_is_in_default_office(self.operator, self.structure))

    def test_user_is_operator(self):
        self.assertFalse(utils.user_is_operator(None, self.structure))
        self.assertTrue(utils.user_is_operator(self.operator, self.structure))
        self.assertIsNone(utils.user_is_operator(self.user, self.structure))

    def test_user_manage_office(self):
        self.assertFalse(utils.user_manage_office(None, self.office))
        self.assertFalse(utils.user_manage_office(self.operator, None))
        inactive = self.make_office("Inactive", self.structure, is_active=False)
        self.assertFalse(utils.user_manage_office(self.operator, inactive))
        self.assertTrue(utils.user_manage_office(self.manager, self.office))
        self.assertFalse(
            utils.user_manage_office(self.manager, self.office, strictly_assigned=True)
        )
        self.assertTrue(utils.user_manage_office(self.operator, self.office))

    def test_get_user_type(self):
        self.assertEqual(utils.get_user_type(self.manager), "user")
        self.assertEqual(utils.get_user_type(self.manager, self.structure), "manager")
        self.assertEqual(utils.get_user_type(self.operator, self.structure), "operator")
        self.assertEqual(utils.get_user_type(self.user, self.structure), "user")

    def test_user_is_employee(self):
        self.assertFalse(utils.user_is_employee(None))
        self.assertFalse(utils.user_is_employee(self.user))
        self.user.identificativo_dipendente = "EMP"
        self.assertEqual(utils.user_is_employee(self.user), "EMP")
        fake_user = mock.Mock(**{settings.EMPLOYEE_ATTRIBUTE_NAME: lambda: True})
        self.assertTrue(utils.user_is_employee(fake_user))

    def test_user_is_in_organization(self):
        self.assertFalse(utils.user_is_in_organization(None))
        self.assertFalse(utils.user_is_in_organization(self.user))
        self.user.identificativo_utente = "USR"
        self.assertEqual(utils.user_is_in_organization(self.user), "USR")
        fake_user = mock.Mock(**{settings.USER_ATTRIBUTE_NAME: lambda: True})
        self.assertTrue(utils.user_is_in_organization(fake_user))

    def test_visible_tickets_to_user(self):
        office_employee = OrganizationalStructureOfficeEmployee.objects.filter(
            employee=self.operator
        )
        tickets = utils.visible_tickets_to_user(
            self.operator, self.structure, office_employee
        )
        self.assertEqual(list(tickets), [self.ticket.pk])
        tickets = utils.visible_tickets_to_user(self.manager, self.structure, [])
        self.assertEqual(list(tickets), [self.ticket.pk])

    def test_office_can_be_deleted(self):
        self.assertFalse(utils.office_can_be_deleted(None))
        self.assertFalse(utils.office_can_be_deleted(self.default_office))
        self.assertFalse(utils.office_can_be_deleted(self.office))
        empty_office = self.make_office("Empty", self.structure)
        self.assertTrue(utils.office_can_be_deleted(empty_office))

    def test_user_offices_list(self):
        self.assertEqual(utils.user_offices_list([]), [])
        office_employee = OrganizationalStructureOfficeEmployee.objects.filter(
            employee=self.operator
        )
        self.assertEqual(utils.user_offices_list(office_employee), [self.office])

    def test_ticket_user_summary_dict_operator(self):
        TicketAssignment.objects.create(
            ticket=self.ticket, office=self.default_office
        )
        # operators only see their own offices (not the default one,
        # even if it has open tickets)
        summary = utils.ticket_user_summary_dict(self.operator)
        self.assertEqual(list(summary.keys()), [self.structure])
        self.assertEqual(list(summary[self.structure].keys()), [self.office])
        self.assertEqual(summary[self.structure][self.office],
                         [{'subject': self.ticket.subject,
                           'code': str(self.ticket.code),
                           'url': self.ticket.get_url(structure=self.structure)}])
        # managers see all the structure offices
        summary = utils.ticket_user_summary_dict(self.manager)
        self.assertEqual(
            set(summary[self.structure].keys()), {self.office, self.default_office}
        )


class Test_MailUtils(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_send_custom_mail(self):
        self.assertFalse(utils.send_custom_mail("s", [], "body"))
        self.user.email_notify = False
        self.other_user.email = None
        # no valid recipients
        self.assertIsNone(
            utils.send_custom_mail("s", [self.user, self.other_user], "body")
        )
        with mock.patch("uni_ticket.utils.send_mail", return_value=1) as m:
            result = utils.send_custom_mail(
                "s", [self.user], "body {hostname}",
                params={"hostname": "host"}, force=True
            )
        self.assertEqual(result, 1)
        self.assertEqual(m.call_args.kwargs["recipient_list"], [self.user.email])
        self.assertIn("body host", m.call_args.kwargs["message"])

    def test_send_summary_email(self):
        self.user.email = None
        # same ticket in two offices is counted once
        TicketAssignment.objects.create(ticket=self.ticket, office=self.default_office)
        with mock.patch("uni_ticket.utils.send_custom_mail", return_value=1) as m:
            result = utils.send_summary_email([self.user, self.manager])
        self.assertEqual(result, {"success": [self.manager], "failed": [self.user]})
        params = m.call_args.kwargs["params"]
        self.assertEqual(params["opened_ticket_number"], 1)
        self.assertIn(self.ticket.subject, params["tickets_per_office"])

        with mock.patch("uni_ticket.utils.send_custom_mail", return_value=0):
            result = utils.send_summary_email([self.manager])
        self.assertEqual(result, {"success": [], "failed": [self.manager]})

    def test_send_ticket_mail_to_operators(self):
        params = {"hostname": "h", "user": "", "ticket": self.ticket}
        with mock.patch("uni_ticket.utils.send_mail", return_value=1) as m:
            # category office operators
            utils.send_ticket_mail_to_operators(
                None, self.ticket, self.category, "{user}", dict(params)
            )
            self.assertEqual(
                m.call_args.kwargs["recipient_list"], [self.operator.email]
            )
            m.reset_mock()
            # empty office: fallback on default office
            empty_office = self.make_office("Empty", self.structure)
            utils.send_ticket_mail_to_operators(
                None, self.ticket, self.category, "{user}", dict(params),
                office=empty_office
            )
            self.assertEqual(
                m.call_args.kwargs["recipient_list"], [self.manager.email]
            )
            m.reset_mock()
            # empty office without fallback: nothing sent
            utils.send_ticket_mail_to_operators(
                None, self.ticket, self.category, "{user}", dict(params),
                office=empty_office, send_to_default_office=False
            )
            m.assert_not_called()


class Test_FileUtils(TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_download_delete_file(self):
        f = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        path = os.path.join(self.tmp, "sub")
        utils.save_file(f, path, "test.txt")
        self.assertTrue(os.path.exists(os.path.join(path, "test.txt")))

        response = utils.download_file(path, "test.txt")
        self.assertEqual(response.content, b"content")
        self.assertIn("test.txt", response["Content-Disposition"])

        self.assertEqual(utils.delete_file("test.txt", path=path), path)
        self.assertFalse(utils.delete_file("test.txt", path=path))

    def test_download_missing_file(self):
        with self.assertRaises(Http404):
            utils.download_file(self.tmp, "missing.txt")

    def test_delete_directory(self):
        with override_settings(MEDIA_ROOT=self.tmp):
            os.makedirs(os.path.join(self.tmp, "folder"))
            self.assertTrue(utils.delete_directory("folder"))
            self.assertFalse(utils.delete_directory("folder"))

    def test_get_path(self):
        self.assertEqual(utils.get_path("x"), "{}/x".format(settings.MEDIA_ROOT))


class Test_GenericUtils(TestCase):

    def test_compress_decompress(self):
        self.assertEqual(
            utils.decompress_text(utils.compress_text_to_b64("text")), b"text"
        )
        self.assertEqual(
            utils.decompress_text(utils.compress_text_to_b64(b"text").decode()),
            b"text",
        )

    def test_format_slugged_name(self):
        self.assertEqual(utils.format_slugged_name("my_field"), "My field")
        self.assertEqual(
            utils.format_slugged_name("my_field", capitalize=False), "my field"
        )

    def test_uuid_code(self):
        self.assertEqual(len(utils.uuid_code()), 32)

    def test_get_text_with_hrefs(self):
        text = "see https://example.org/a?b=1 and http://test.it"
        result = utils.get_text_with_hrefs(text)
        self.assertIn('href="https://example.org/a?b=1"', result)
        self.assertIn('href="http://test.it"', result)
        self.assertEqual(utils.get_text_with_hrefs("no links"), "no links")

    def test_get_datetime_delta(self):
        delta = utils.get_datetime_delta(1)
        self.assertEqual((delta.hour, delta.minute, delta.second), (0, 0, 0))

    def test_disable_expired_items(self):
        item = mock.Mock()
        utils.disable_expired_items([item])
        item.disable_if_expired.assert_called_once()

    def test_redirect_after_login(self):
        response = utils.redirect_after_login("/path/")
        self.assertEqual(
            response.url,
            "{}?{}=/path/".format(settings.LOGIN_URL, REDIRECT_FIELD_NAME),
        )
        with override_settings(LOGIN_URL="/login/?a=1"):
            response = utils.redirect_after_login("/path/")
        self.assertEqual(
            response.url, "/login/?a=1&{}=/path/".format(REDIRECT_FIELD_NAME)
        )

    def test_querydict_to_dict(self):
        d = {"a": 1}
        self.assertIs(utils.querydict_to_dict(d), d)
        qd = QueryDict("a=1&b=2&b=3")
        self.assertEqual(utils.querydict_to_dict(qd), {"a": "1", "b": ["2", "3"]})

    def test_custom_message(self):
        request = RequestFactory().get("/")
        request.user = mock.Mock(is_authenticated=False)
        response = utils.custom_message(request, "hello", status=403)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"hello", response.content)


class Test_ExportUtils(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()
        TicketCategoryInputList.objects.create(
            category_module=cls.module, name="text field",
            field_type="CustomCharField", ordinamento=1,
        )
        TicketCategoryInputList.objects.create(
            category_module=cls.module, name="period",
            field_type="DateStartEndComplexField", ordinamento=2,
        )
        TicketCategoryInputList.objects.create(
            category_module=cls.module, name="table",
            field_type="CustomComplexTableField", ordinamento=3,
            valore="col1#col2",
        )
        content = {
            "text_field": "hello",
            "period_data_inizio_dyn": "2024-01-01",
            "table-0-col1": "a",
            "table-0-col2": "b",
            "table-1-col1": "c",
        }
        cls.ticket.modulo_compilato = json.dumps(content)
        cls.ticket.save()
        cls.closed_ticket = cls.make_ticket(
            "Closed", cls.module, None, content={"text_field": "x"},
            is_closed=True, closing_reason="done",
        )

    def _rows(self, response):
        return list(csv.reader(io.StringIO(response.content.decode())))

    def test_export_input_module_csv(self):
        response = utils.export_input_module_csv(self.module)
        rows = self._rows(response)
        head = rows[0]
        self.assertIn("text field", head)
        self.assertIn("period_data_inizio_dyn", head)
        self.assertIn("table", head)
        self.assertEqual(len(rows), 3)

        ticket_row = [r for r in rows if r[0] == str(self.ticket.code)][0]
        self.assertIn("hello", ticket_row)
        self.assertIn("2024-01-01", ticket_row)
        self.assertIn("col1: a\ncol2: b\n\ncol1: c", ticket_row)

        closed_row = [r for r in rows if r[0] == str(self.closed_ticket.code)][0]
        self.assertIn("done", closed_row)
        self.assertIn("Utente anonimo", closed_row)

    def test_export_input_module_csv_filtered(self):
        response = utils.export_input_module_csv(
            self.module, ticket_codes_list=[self.ticket.code]
        )
        self.assertEqual(len(self._rows(response)), 2)
        self.assertFalse(
            utils.export_input_module_csv(self.module, ticket_codes_list=["nope"])
        )

    def test_export_category_zip(self):
        response = utils.export_category_zip(self.category)
        self.assertEqual(response["Content-Type"], "application/zip")
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(len(archive.namelist()), 1)
        self.assertTrue(archive.namelist()[0].startswith(self.category.name))

    def test_export_category_zip_error(self):
        with mock.patch(
            "uni_ticket.utils.export_input_module_csv", side_effect=Exception("err")
        ):
            response = utils.export_category_zip(self.category)
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(archive.namelist(), [])

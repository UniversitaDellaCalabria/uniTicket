import json

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.text import slugify

from organizational_area.models import (
    OrganizationalStructure,
    OrganizationalStructureOffice,
    OrganizationalStructureOfficeEmployee,
    UserManageOrganizationalStructure,
)
from uni_ticket.models import (
    CompiledTicket,
    Log,
    OrganizationalStructureAllowedUsersList,
    OrganizationalStructureWSProtocollo,
    Task,
    Ticket,
    Ticket2Ticket,
    TicketAssignment,
    TicketCategory,
    TicketCategoryCondition,
    TicketCategoryDefaultReply,
    TicketCategoryInputList,
    TicketCategoryModule,
    TicketCategoryTask,
    TicketCategoryWSProtocollo,
    TicketReply,
)
from uni_ticket.utils import compress_text_to_b64


class ORMFixtureMixin:
    """
    Lightweight fixture built directly with the ORM
    (much faster than the HTTP based environments in base_*.py)
    """

    @classmethod
    def make_user(cls, name, **kwargs):
        return get_user_model().objects.create_user(
            username=slugify(name),
            password="passw",
            first_name=name,
            last_name="Lastname",
            email="{}@test.it".format(slugify(name)),
            **kwargs
        )

    @classmethod
    def make_structure(cls, name):
        return OrganizationalStructure.objects.create(
            name=name, slug=slugify(name), unique_code=slugify(name)
        )

    @classmethod
    def make_office(cls, name, structure, is_active=True):
        return OrganizationalStructureOffice.objects.create(
            name=name,
            slug=slugify(name),
            organizational_structure=structure,
            is_active=is_active,
        )

    @classmethod
    def make_category(cls, name, structure, office, **kwargs):
        return TicketCategory.objects.create(
            name=name,
            slug=slugify(name),
            organizational_structure=structure,
            organizational_office=office,
            **kwargs
        )

    @classmethod
    def make_ticket(cls, subject, module, user, content=None, **kwargs):
        return Ticket.objects.create(
            subject=subject,
            description=subject,
            input_module=module,
            created_by=user,
            modulo_compilato=json.dumps(content or {}),
            **kwargs
        )

    @classmethod
    def build_fixture(cls):
        cls.structure = cls.make_structure("Structure A")
        cls.structure_b = cls.make_structure("Structure B")
        cls.default_office = cls.structure.get_default_office()
        cls.office = cls.make_office("Office A", cls.structure)

        cls.manager = cls.make_user("Manager A")
        cls.operator = cls.make_user("Operator A")
        cls.user = cls.make_user("Simple User")
        cls.other_user = cls.make_user("Other User")

        OrganizationalStructureOfficeEmployee.objects.create(
            employee=cls.manager, office=cls.default_office
        )
        UserManageOrganizationalStructure.objects.create(
            user=cls.manager, organizational_structure=cls.structure
        )
        OrganizationalStructureOfficeEmployee.objects.create(
            employee=cls.operator, office=cls.office
        )

        cls.category = cls.make_category(
            "Category A", cls.structure, cls.office, is_active=True
        )
        cls.module = TicketCategoryModule.objects.create(
            name="module", ticket_category=cls.category, is_active=True
        )
        cls.ticket = cls.make_ticket("Ticket A", cls.module, cls.user)
        cls.assignment = TicketAssignment.objects.create(
            ticket=cls.ticket, office=cls.office, assigned_by=cls.user
        )


class Test_ExpirableModel(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_expiration(self):
        now = timezone.localtime()
        cat = self.category
        self.assertFalse(cat.is_expired())
        self.assertTrue(cat.is_started())
        self.assertTrue(cat.is_published())

        cat.date_start = now + timezone.timedelta(days=1)
        self.assertFalse(cat.is_started())
        self.assertFalse(cat.is_in_progress())

        cat.date_start = now - timezone.timedelta(days=2)
        cat.date_end = now - timezone.timedelta(days=1)
        self.assertTrue(cat.is_started())
        self.assertTrue(cat.is_expired())
        self.assertFalse(cat.is_published())

    def test_disable_if_expired(self):
        cat = self.category
        cat.date_end = timezone.localtime() - timezone.timedelta(days=1)
        cat.save()
        cat.disable_if_expired()
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)


class Test_TicketCategory(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_allowed_users_list_str(self):
        allowed_list = OrganizationalStructureAllowedUsersList.objects.create(
            organizational_structure=self.structure, name="List"
        )
        self.assertEqual(str(allowed_list), "List - {}".format(self.structure))

    def test_can_be_deleted(self):
        self.assertFalse(self.category.can_be_deleted())
        empty_cat = self.make_category("Empty", self.structure, self.office)
        TicketCategoryModule.objects.create(name="m", ticket_category=empty_cat)
        self.assertTrue(empty_cat.can_be_deleted())

    def test_something_stops_activation(self):
        cat = self.make_category("No office", self.structure, None)
        self.assertIn("ufficio di competenza", str(cat.something_stops_activation()))

        inactive_office = self.make_office("Inactive", self.structure, is_active=False)
        cat.organizational_office = inactive_office
        self.assertIn("attivare l'ufficio", str(cat.something_stops_activation()))

        cat.organizational_office = self.office
        cat.save()
        self.assertIn("modulo di input", str(cat.something_stops_activation()))

        TicketCategoryModule.objects.create(
            name="m", ticket_category=cat, is_active=True
        )
        cat.date_end = timezone.localtime() - timezone.timedelta(days=1)
        self.assertIn("data di scadenza", str(cat.something_stops_activation()))

        cat.date_end = None
        self.assertFalse(cat.something_stops_activation())

    def test_get_conditions_and_tasks(self):
        TicketCategoryCondition.objects.create(
            category=self.category, title="c1", text="t", is_printable=True
        )
        TicketCategoryCondition.objects.create(
            category=self.category, title="c2", text="t", is_printable=False
        )
        self.assertEqual(self.category.get_conditions().count(), 2)
        self.assertEqual(self.category.get_conditions(is_printable=True).count(), 1)

        TicketCategoryTask.objects.create(
            category=self.category, subject="t1", code="cat-task-1",
            description="d", is_active=True
        )
        TicketCategoryTask.objects.create(
            category=self.category, subject="t2", code="cat-task-2",
            description="d", is_active=False
        )
        self.assertEqual(self.category.get_tasks().count(), 1)
        self.assertEqual(self.category.get_tasks(is_active=False).count(), 2)

    def test_allowed_to_user(self):
        cat = self.category
        self.assertEqual(cat.allowed_to_user(None), (False,))

        cat.allow_anonymous = True
        self.assertEqual(cat.allowed_to_user(self.user), (True,))
        cat.allow_anonymous = False

        cat.allow_spid_cie = True
        self.assertFalse(cat.allowed_to_user(self.user)[0])
        self.user.last_login_context = "https://www.spid.gov.it/SpidL2"
        self.assertTrue(cat.allowed_to_user(self.user)[0])
        cat.allow_spid_cie = False

        # guest allowed
        self.assertEqual(cat.allowed_to_user(self.user), (True,))

        cat.allow_guest = False
        # neither employee nor internal user
        self.assertFalse(cat.allowed_to_user(self.user)[0])

        self.user.identificativo_dipendente = "123"
        self.assertEqual(cat.allowed_to_user(self.user), (True,))

        self.user.identificativo_dipendente = None
        self.user.identificativo_utente = "ABC"
        self.assertEqual(cat.allowed_to_user(self.user), (True,))

    def test_get_active_protocol_configuration(self):
        # no structure configuration
        self.assertFalse(self.category.get_active_protocol_configuration())

        OrganizationalStructureWSProtocollo.objects.create(
            organizational_structure=self.structure,
            name="conf", is_active=True,
            protocollo_username="u", protocollo_password="p",
            protocollo_aoo="aoo",
        )
        # structure configuration but no category configuration
        self.assertFalse(self.category.get_active_protocol_configuration())

        conf = TicketCategoryWSProtocollo.objects.create(
            ticket_category=self.category, name="cat conf", is_active=True,
            protocollo_uo="uo", protocollo_cod_titolario="tit",
        )
        self.assertEqual(self.category.get_active_protocol_configuration(), conf)

    def test_user_can_open_tickets(self):
        self.assertTrue(self.category.user_can_open_tickets(self.user))
        self.category.allowed_users.add(self.other_user)
        self.assertFalse(self.category.user_can_open_tickets(self.user))
        self.assertTrue(self.category.user_can_open_tickets(self.other_user))

        allowed_list = OrganizationalStructureAllowedUsersList.objects.create(
            organizational_structure=self.structure, name="List"
        )
        allowed_list.allowed_users.add(self.user)
        self.category.allowed_users_lists.add(allowed_list)
        self.assertTrue(self.category.user_can_open_tickets(self.user))


class Test_TicketCategoryModule(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_can_be_deleted(self):
        self.assertFalse(self.module.can_be_deleted())
        other = TicketCategoryModule.objects.create(
            name="other", ticket_category=self.category
        )
        self.assertTrue(other.can_be_deleted())
        self.assertEqual(str(other), "other")

    def test_disable_other_modules(self):
        other = TicketCategoryModule.objects.create(
            name="other", ticket_category=self.category, is_active=True
        )
        other.disable_other_modules()
        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)
        other.refresh_from_db()
        self.assertTrue(other.is_active)

    def test_input_list_field_exist(self):
        TicketCategoryInputList.objects.create(
            category_module=self.module, name="Field", field_type="CustomCharField"
        )
        self.assertEqual(
            TicketCategoryInputList.field_exist(self.module, "field"), "field"
        )
        self.assertFalse(TicketCategoryInputList.field_exist(self.module, "nope"))


class Test_Ticket(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_serialize_and_str(self):
        data = self.ticket.serialize()
        self.assertEqual(data["code"], self.ticket.code)
        self.assertEqual(data["category"], self.category.name)
        self.assertEqual(data["assigned_office"], [{"name": self.office.name}])
        self.assertEqual(
            str(self.ticket), "{} ({})".format(self.ticket.subject, self.ticket.code)
        )

    def test_compress_modulo_compilato(self):
        content = {"field": "x" * 200}
        self.ticket.modulo_compilato = json.dumps(content)
        # short text is not compressed
        self.ticket.compress_modulo_compilato(check_length=False)
        self.assertEqual(self.ticket.get_modulo_compilato(), content)
        self.assertNotEqual(self.ticket.modulo_compilato, json.dumps(content))

        short = Ticket(modulo_compilato="{}")
        short.compress_modulo_compilato()
        self.assertEqual(short.modulo_compilato, "{}")

    def test_number_limit_reached_by_user(self):
        with override_settings(MAX_DAILY_TICKET_PER_USER=0):
            self.assertFalse(Ticket.number_limit_reached_by_user(self.user))
        with override_settings(MAX_DAILY_TICKET_PER_USER=100):
            self.assertFalse(Ticket.number_limit_reached_by_user(self.user))
        with override_settings(MAX_DAILY_TICKET_PER_USER=1):
            self.assertTrue(Ticket.number_limit_reached_by_user(self.user))

    def test_existent_open_ticket(self):
        self.assertTrue(Ticket.existent_open_ticket(self.user, self.category))
        self.assertFalse(Ticket.existent_open_ticket(self.other_user, self.category))

    def test_is_open(self):
        self.assertFalse(self.ticket.is_open())
        self.assignment.taken_date = timezone.localtime()
        self.assignment.taken_by = self.operator
        self.assignment.save()
        self.assertTrue(self.ticket.is_open())
        self.ticket.is_closed = True
        self.assertFalse(self.ticket.is_open())

    def test_owners(self):
        self.assertFalse(self.ticket.check_if_owner(None))
        self.assertTrue(self.ticket.check_if_owner(self.user))
        self.assertFalse(self.ticket.check_if_owner(self.other_user))
        self.assertEqual(self.ticket.get_owners_html(), self.user)
        self.assertEqual(self.ticket.get_owners(), [self.user])

        self.ticket.compiled_by = self.other_user
        self.assertTrue(self.ticket.check_if_owner(self.other_user))
        self.assertIn(str(self.other_user), self.ticket.get_owners_html())
        self.assertEqual(self.ticket.get_owners(), [self.user, self.other_user])

        self.ticket.created_by = None
        self.assertEqual(self.ticket.get_owners(), [])

    def test_get_allegati_dict(self):
        self.assertEqual(self.ticket.get_allegati_dict(), {})
        self.assertEqual(
            self.ticket.get_allegati_dict(ticket_dict={"allegati": {"a": "b"}}),
            {"a": "b"},
        )

    def test_compiled_form_without_module(self):
        with mock.patch.object(Ticket, "get_form_module", return_value=None):
            self.assertIsNone(self.ticket.compiled_form())

    def _status_variants(self, method):
        t = self.ticket
        t.draft = True
        self.assertIn("Bozza", str(method()))
        t.is_closed = True
        self.assertIn("Chiusa", str(method()))
        t.draft = False

        # notification or closed by user himself
        t.is_notification = True
        self.assertIn("Chiusa", str(method()))
        t.is_notification = False
        t.closed_by = self.operator
        results = []
        for status in (-1, 0, 1, 2):
            t.closing_status = status
            results.append(method())
            self.assertIn(str(self.operator), results[-1])
        self.assertEqual(len(set(results)), 4)

        t.is_closed = False
        self.assertIn("Aperta", str(method()))
        self.assignment.taken_by = self.operator
        self.assignment.taken_date = timezone.localtime()
        self.assignment.save()
        self.assertIn("Assegnata", str(method()))

    def test_get_status(self):
        self._status_variants(self.ticket.get_status)

    def test_get_status_table(self):
        self._status_variants(self.ticket.get_status_table)

    def test_update_log(self):
        self.assertFalse(self.ticket.update_log(None))
        log = self.ticket.update_log(self.operator, is_public=False, note="note")
        self.assertIsInstance(log, Log)
        self.assertFalse(log.is_public)

    def test_assigned_offices_and_structures(self):
        inactive = self.make_office("Inactive", self.structure, is_active=False)
        TicketAssignment.objects.create(
            ticket=self.ticket, office=inactive, follow=False
        )
        self.assertEqual(self.ticket.get_assigned_to_offices(), [self.office])
        self.assertEqual(
            len(self.ticket.get_assigned_to_offices(office_active=False)), 2
        )
        self.assertEqual(
            self.ticket.get_assigned_to_offices(
                office_active=False, ignore_follow=False
            ),
            [self.office],
        )
        self.assertEqual(
            self.ticket.get_assigned_to_offices(structure=self.structure_b), []
        )
        self.assertEqual(self.ticket.get_assigned_to_structures(), [self.structure])

    def test_add_competence(self):
        # already assigned
        self.assertFalse(self.ticket.add_competence(self.office, self.manager))
        # operator of destination office takes the ticket
        competence = self.ticket.add_competence(self.default_office, self.manager)
        self.assertEqual(competence.taken_by, self.manager)
        office_b = self.structure_b.get_default_office()
        competence = self.ticket.add_competence(office_b, self.manager, note="n")
        self.assertIsNone(competence.taken_by)

    def _take_all(self):
        now = timezone.localtime()
        default_assignment = TicketAssignment.objects.create(
            ticket=self.ticket, office=self.default_office,
            taken_by=self.manager, taken_date=now
        )
        self.assignment.taken_by = self.operator
        self.assignment.taken_date = now
        self.assignment.save()
        return default_assignment

    def test_block_competence_user(self):
        self.assertFalse(
            self.ticket.block_competence(self.user, self.structure)
        )

    def test_block_competence_operator(self):
        default_assignment = self._take_all()
        operator_office_b = self.make_office("Office B", self.structure)
        TicketAssignment.objects.create(ticket=self.ticket, office=operator_office_b)
        # operator can disable only his own (non default) offices
        offices = self.ticket.block_competence(self.operator, self.structure)
        self.assertEqual(offices, [self.office])
        self.assignment.refresh_from_db()
        self.assertTrue(self.assignment.readonly)
        default_assignment.refresh_from_db()
        self.assertFalse(default_assignment.readonly)

    def test_block_competence_manager(self):
        default_assignment = self._take_all()
        # untaken competence is skipped
        untaken_office = self.make_office("Untaken", self.structure)
        TicketAssignment.objects.create(ticket=self.ticket, office=untaken_office)
        offices = self.ticket.block_competence(
            self.manager, self.structure, allow_readonly=False
        )
        self.assertEqual(len(offices), 3)
        self.assignment.refresh_from_db()
        self.assertFalse(self.assignment.follow)
        default_assignment.refresh_from_db()
        self.assertFalse(default_assignment.follow)

        # already unfollowed competences are skipped
        offices = self.ticket.block_competence(self.manager, self.structure)
        self.assignment.refresh_from_db()
        self.assertFalse(self.assignment.follow)

    def test_block_competence_selected_office(self):
        self._take_all()
        offices = self.ticket.block_competence(
            self.manager, self.structure, selected_office=self.office
        )
        self.assertEqual(offices, [self.office])
        self.assignment.refresh_from_db()
        self.assertTrue(self.assignment.readonly)
        # default office is not changed
        offices = self.ticket.block_competence(
            self.manager, self.structure, selected_office=self.default_office
        )
        self.assertEqual(offices, [self.default_office])

    def test_is_closable(self):
        self.assertFalse(self.ticket.is_closable())
        self._take_all()
        self.assertTrue(self.ticket.is_closable())

        self.ticket.draft = True
        self.assertFalse(self.ticket.is_closable())
        self.ticket.draft = False
        self.ticket.is_closed = True
        self.assertFalse(self.ticket.is_closable())
        self.ticket.is_closed = False

        main = self.make_ticket("Main", self.module, self.other_user)
        Ticket2Ticket.objects.create(subordinate_ticket=self.ticket, main_ticket=main)
        self.assertFalse(self.ticket.is_closable())
        self.assertEqual(main.blocks_some_ticket(), [self.ticket])
        self.assertTrue(Ticket2Ticket.main_is_already_used(self.ticket))
        main.is_closed = True
        main.save()
        self.assertFalse(Ticket2Ticket.main_is_already_used(self.ticket))
        self.assertTrue(self.ticket.is_closable())

        task = Task.objects.create(
            ticket=self.ticket, subject="task", code="task-1", description="d"
        )
        self.assertFalse(self.ticket.is_closable())
        task.is_closed = True
        task.save()
        self.assertTrue(self.ticket.is_closable())

    def test_is_valid(self):
        self.assertTrue(self.ticket.is_valid())
        self.ticket.modulo_compilato = json.dumps({"allegati": {"file": "f.pdf"}})
        form = mock.Mock()
        form.is_valid.return_value = False
        with mock.patch.object(Ticket, "compiled_form", return_value=form):
            self.assertFalse(self.ticket.is_valid())
            form.is_valid.return_value = True
            self.assertTrue(self.ticket.is_valid())

    def test_followed(self):
        self.assertFalse(self.ticket.is_followed_in_structure(None))
        self.assertFalse(self.ticket.is_followed_by_office(None))
        self.assertFalse(self.ticket.is_followed_by_one_of_offices([]))
        self.assertEqual(
            self.ticket.is_followed_by_office(self.office),
            {"follow": True, "readonly": False},
        )
        self.assertFalse(self.ticket.is_followed_by_office(self.office, taken=True))
        self.assertFalse(
            self.ticket.is_followed_in_structure(self.structure, taken=True)
        )
        self.assignment.readonly = True
        self.assignment.save()
        self.assertEqual(
            self.ticket.is_followed_by_one_of_offices([self.office]),
            {"follow": True, "readonly": True},
        )

    def test_has_been_taken_prefetched(self):
        self._take_all()
        ticket = Ticket.objects.prefetch_related(
            "ticketassignment_set__office"
        ).get(pk=self.ticket.pk)
        self.assertTrue(ticket.has_been_taken())
        self.assertTrue(ticket.has_been_taken(exclude_readonly=True))
        self.assertTrue(ticket.has_been_taken(structure=self.structure))
        self.assertFalse(ticket.has_been_taken(structure=self.structure_b))
        self.assertTrue(ticket.has_been_taken(user=self.operator))
        self.assertFalse(ticket.has_been_taken(user=self.user))
        self.assertIn(str(self.operator), ticket.taken_by_html_list())

    def test_has_been_taken_queries(self):
        self._take_all()
        self.assertTrue(
            self.ticket.has_been_taken(exclude_readonly=True, structure=self.structure)
        )
        self.assertFalse(self.ticket.has_been_taken_by_user(None))
        self.assertTrue(self.ticket.has_been_taken_by_user(self.operator))

    def test_taken_by_html_list_untaken(self):
        self.assertIn("Da assegnare", self.ticket.taken_by_html_list())

    def test_take(self):
        self.ticket.take(self.manager, self.structure, assigned_by=self.manager)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.taken_by, self.manager)
        self.assertEqual(self.assignment.assigned_by, self.manager)

    def test_is_untaken_by_user_offices(self):
        self.assertEqual(
            self.ticket.is_untaken_by_user_offices(self.operator, self.structure),
            [self.office],
        )

    def test_close(self):
        self.ticket.close(self.operator, "done")
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)
        self.assertEqual(self.ticket.closing_reason, "done")


class Test_OtherModels(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_default_reply_str(self):
        reply = TicketCategoryDefaultReply.objects.create(
            ticket_category=self.category, text="x" * 100
        )
        self.assertEqual(str(reply), "x" * 80 + "..")

    def test_ticket_assignment_per_structure_and_offices(self):
        self.assignment.taken_by = self.operator
        self.assignment.taken_date = timezone.localtime()
        self.assignment.save()
        tickets = TicketAssignment.get_ticket_per_structure(
            self.structure, closed=False, taken=True, taken_by=self.operator,
            priority_first=False, ticket_codes=[self.ticket.code]
        )
        self.assertEqual(list(tickets), [self.ticket.pk])
        tickets = TicketAssignment.get_ticket_in_office_list(
            [self.office], closed=False, taken=True, taken_by=self.operator,
            priority_first=False, ticket_codes=[self.ticket.code]
        )
        self.assertEqual(list(tickets), [self.ticket.pk])
        self.assertEqual(
            str(self.assignment), "{} - {}".format(self.ticket, self.office)
        )

    def test_ticket_reply(self):
        reply = TicketReply.objects.create(
            ticket=self.ticket, owner=self.operator, structure=self.structure,
            subject="s", text="t"
        )
        data = reply.serialize()
        self.assertEqual(data["subject"], "s")
        self.assertTrue(
            TicketReply.get_unread_messages_count([self.ticket.pk], by_operator=True)
        )
        self.assertFalse(TicketReply.get_unread_messages_count([self.ticket.pk]))
        self.assertIn(self.ticket.get_folder(), reply.get_folder())
        self.assertEqual(str(reply), "s - {}".format(self.ticket))

    def test_ticket2ticket_str(self):
        main = self.make_ticket("Main", self.module, self.other_user)
        t2t = Ticket2Ticket.objects.create(
            subordinate_ticket=self.ticket, main_ticket=main
        )
        self.assertEqual(str(t2t), "{} - {}".format(self.ticket, main))

    def test_task(self):
        task = Task.objects.create(
            ticket=self.ticket, subject="task", code="task-x", description="d"
        )
        self.assertEqual(task.get_priority(), "Normale")
        self.assertIn("Aperta", task.get_basic_status())
        self.assertIn("Aperta", task.get_status())
        task.update_log(self.operator, is_public=False, note="n")
        self.assertTrue(
            Log.objects.filter(object_id=task.pk, is_public=False).exists()
        )
        task.is_closed = True
        task.closed_by = self.operator
        self.assertIn("Chiusa", task.get_basic_status())
        results = set()
        for status in (-1, 0, 1, 2):
            task.closing_status = status
            results.add(task.get_status())
        self.assertEqual(len(results), 4)
        self.assertIn("task-x", task.get_folder())

    def test_category_condition_and_task_str(self):
        cond = TicketCategoryCondition.objects.create(
            category=self.category, title="Cond", text="t"
        )
        self.assertEqual(str(cond), "({}) Cond".format(self.category))
        self.assertIn(self.category.get_folder(), cond.get_folder())
        task = TicketCategoryTask.objects.create(
            category=self.category, subject="T", code="ct", description="d"
        )
        self.assertEqual(str(task), "T - {}".format(self.category))
        self.assertIn("ct", task.get_folder())

    def test_protocol_configurations(self):
        conf_1 = OrganizationalStructureWSProtocollo.objects.create(
            organizational_structure=self.structure, name="c1", is_active=True,
            protocollo_username="u", protocollo_password="p", protocollo_aoo="a",
        )
        conf_2 = OrganizationalStructureWSProtocollo.objects.create(
            organizational_structure=self.structure, name="c2", is_active=True,
            protocollo_username="u", protocollo_password="p", protocollo_aoo="a",
        )
        conf_1.refresh_from_db()
        # signal disables the other configurations
        self.assertFalse(conf_1.is_active)
        self.assertEqual(str(conf_2), "c2 - {}".format(self.structure))

        cat_conf_1 = TicketCategoryWSProtocollo.objects.create(
            ticket_category=self.category, name="cc1", is_active=True,
            protocollo_uo="uo", protocollo_cod_titolario="t",
        )
        TicketCategoryWSProtocollo.objects.create(
            ticket_category=self.category, name="cc2", is_active=True,
            protocollo_uo="uo", protocollo_cod_titolario="t",
        )
        cat_conf_1.refresh_from_db()
        self.assertFalse(cat_conf_1.is_active)
        self.assertEqual(str(cat_conf_1), "cc1 - {}".format(self.category))

    def test_compiled_ticket_clear(self):
        old = CompiledTicket.objects.create(content="{}")
        CompiledTicket.objects.filter(pk=old.pk).update(
            created=timezone.now() - timezone.timedelta(days=30)
        )
        new = CompiledTicket.objects.create(content="{}")
        CompiledTicket.clear()
        self.assertFalse(CompiledTicket.objects.filter(pk=old.pk).exists())
        self.assertTrue(CompiledTicket.objects.filter(pk=new.pk).exists())

    def test_get_modulo_compilato_compressed(self):
        content = {"a": "b"}
        self.ticket.modulo_compilato = compress_text_to_b64(json.dumps(content)).decode()
        self.assertEqual(self.ticket.get_modulo_compilato(), content)


class Test_TicketMisc(ORMFixtureMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.build_fixture()

    def test_taken_date_and_priority(self):
        self.assertIsNone(self.ticket.taken_date)
        now = timezone.now()
        self.assignment.taken_date = now
        self.assignment.save()
        self.assertEqual(self.ticket.taken_date, now)
        self.assertEqual(self.ticket.get_priority(), "Normale")

    def test_get_url(self):
        code = str(self.ticket.code)
        self.assertIn(code, self.ticket.get_url())
        url = self.ticket.get_url(structure=self.structure)
        self.assertIn(self.structure.slug, url)
        self.assertIn(code, url)

    def test_form_and_save_data(self):
        TicketCategoryInputList.objects.create(
            category_module=self.module, name="Field",
            field_type="CustomCharField", is_required=False
        )
        form = self.module.get_form(current_user=self.user)
        self.assertIn("field", form.fields)

        self.ticket.save_data(
            "new subject", "new description",
            {"ticket_subject": "x", "ticket_description": "y", "field": "v"}
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, "new subject")
        self.assertEqual(self.ticket.get_modulo_compilato(), {"field": "v"})

        form = self.ticket.compiled_form()
        self.assertEqual(form.data["field"], "v")
        self.assertEqual(form.data["ticket_subject"], "new subject")

    def test_attachment_upload_path(self):
        from uni_ticket.models import _attachment_upload
        reply = TicketReply(ticket=self.ticket)
        self.assertEqual(
            _attachment_upload(reply, "f.pdf"),
            "{}/f.pdf".format(reply.get_folder()),
        )

    @mock.patch("uni_ticket.models.send_custom_mail")
    def test_update_log_sends_mail(self, mocked_mail):
        log = self.ticket.update_log(self.operator, note="public note")
        self.assertTrue(log.is_public)
        mocked_mail.assert_called_once()
        self.assertEqual(
            mocked_mail.call_args.kwargs["params"]["message"], "public note"
        )

    def test_main_is_already_used_without_relations(self):
        self.assertFalse(Ticket2Ticket.main_is_already_used(self.ticket))

    def test_other_str(self):
        from uni_ticket.models import OrganizationalStructureAlert, Task2Ticket
        task = Task.objects.create(
            ticket=self.ticket, subject="task", code="task-s", description="d"
        )
        t2t = Task2Ticket.objects.create(ticket=self.ticket, task=task)
        self.assertEqual(str(t2t), "task - {}".format(self.ticket))
        alert = OrganizationalStructureAlert.objects.create(
            organizational_structure=self.structure, name="Alert", text="t"
        )
        self.assertEqual(str(alert), "Alert - {}".format(self.structure))

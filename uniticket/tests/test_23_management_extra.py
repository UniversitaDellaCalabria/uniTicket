import logging

from django.urls import NoReverseMatch, reverse

from uni_ticket.models import (
    Task,
    TicketOperatorNote,
    TicketReply,
    Ticket2Ticket,
)

from . import test_12_management_views as t12
from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class ManagementExtraMixin:

    # reuse test_12 helpers without inheriting (and re-running) its tests
    take_ticket = t12.Test_ManagementViews.take_ticket
    create_task = t12.Test_ManagementViews.create_task
    url = t12.Test_ManagementViews.url

    def _error_messages(self, response):
        return [str(m) for m in response.context['messages']
                if m.level_tag == 'error']

    def assertRedirectsTo(self, response, url_name, **kwargs):
        self.assertRedirects(response,
                             reverse(f'uni_ticket:{url_name}', kwargs=kwargs),
                             fetch_redirect_response=False)


class Test_ManagementRoleRedirects(ManagementExtraMixin, BaseTicketEnvironment):
    """
    *_url views redirect to the manager/operator version of the page
    """

    def _structure_kwargs(self):
        return {'structure_slug': self.structure_1.slug}

    def _ticket_kwargs(self):
        return {'structure_slug': self.structure_1.slug,
                'ticket_id': self.ticket.code}

    def _check_roles(self, url_name, target, kwargs):
        url = reverse(f'uni_ticket:{url_name}', kwargs=kwargs)
        # manager
        self.structure_1_manager_login()
        self.assertRedirectsTo(self.client.get(url), f'manager_{target}', **kwargs)
        # operator
        self.structure_1_default_office_operator_login()
        self.assertRedirectsTo(self.client.get(url), f'operator_{target}', **kwargs)

    def test_redirect_structure_ticket_lists(self):
        kwargs = self._structure_kwargs()
        for url_name, target in (('manage_opened_ticket_url', 'opened_ticket'),
                                 ('manage_unassigned_ticket_url', 'unassigned_ticket'),
                                 ('manage_closed_ticket_url', 'closed_ticket')):
            self._check_roles(url_name, target, kwargs)

    def test_redirect_structure_ticket_lists_simple_user(self):
        # simple users are not expected to reach management dispatchers:
        # the "user_*_ticket" redirect has no structure_slug (NoReverseMatch)
        self.client.force_login(self.create_user(name='Simple user'))
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('uni_ticket:manage_opened_ticket_url',
                                    kwargs=self._structure_kwargs()))

    def test_redirect_manage_ticket_url(self):
        # fake URL used by datatables <href> tags: always "Permesso negato"
        self.structure_1_manager_login()
        response = self.client.get(reverse('uni_ticket:manage_ticket_url',
                                           kwargs=self._structure_kwargs()))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'custom_message.html')
        self.assertEqual(str(response.context['avviso']), 'Permesso negato')

    def test_redirect_ticket_close(self):
        self._check_roles('close_ticket', 'close_ticket', self._ticket_kwargs())

    def test_redirect_ticket_competence_add(self):
        self._check_roles('add_ticket_competence_url', 'add_ticket_competence',
                          self._ticket_kwargs())

    def test_redirect_ticket_note(self):
        note = TicketOperatorNote.objects.create(ticket=self.ticket,
                                                 structure=self.structure_1,
                                                 text='note',
                                                 owner=self.staff_1)
        kwargs = self._ticket_kwargs()
        kwargs['note_id'] = note.pk
        self._check_roles('manage_ticket_note_url', 'ticket_note', kwargs)

    def test_redirect_task_add(self):
        self._check_roles('add_ticket_task_url', 'add_ticket_task',
                          self._ticket_kwargs())

    def test_redirect_task_close(self):
        task = self.create_task(self.ticket)
        kwargs = self._ticket_kwargs()
        kwargs['task_id'] = task.code
        self._check_roles('close_task', 'close_task', kwargs)


class Test_ManagementInvalidForms(ManagementExtraMixin, BaseTicketEnvironment):
    """
    Invalid forms add error messages and don't change data
    """

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()
        self.take_ticket(self.ticket)

    def _post(self, url_name, data=None, **kwargs):
        response = self.client.post(self.url(f'uni_ticket:{url_name}', **kwargs),
                                    data or {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._error_messages(response))
        return response

    def test_invalid_ticket_detail_priority(self):
        priority = self.ticket.priority
        self._post('manager_manage_ticket', {'priorita': 'not-a-priority'})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, priority)

    def test_invalid_ticket_dependence(self):
        self._post('manager_add_ticket_dependence', {'note': 'no ticket'})
        self.assertFalse(Ticket2Ticket.objects.exists())

    def test_invalid_ticket_close(self):
        self._post('manager_close_ticket', {'note': 'no status'})
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)

    def test_invalid_ticket_competence_add_final(self):
        assignments = self.ticket.ticketassignment_set.count()
        self._post('manager_add_ticket_competence_final', {},
                   new_structure_slug=self.structure_2.slug)
        self.assertEqual(self.ticket.ticketassignment_set.count(), assignments)

    def test_invalid_ticket_message(self):
        self._post('manager_ticket_message', {'subject': 'Without text'})
        self.assertFalse(TicketReply.objects.filter(subject='Without text').exists())

    def test_invalid_ticket_note_add(self):
        self._post('manager_ticket_notes', {})
        self.assertFalse(TicketOperatorNote.objects.exists())

    def test_invalid_ticket_note_edit(self):
        note = TicketOperatorNote.objects.create(ticket=self.ticket,
                                                 structure=self.structure_1,
                                                 text='original',
                                                 owner=self.staff_1)
        self._post('manager_ticket_note', {'text': ''}, note_id=note.pk)
        note.refresh_from_db()
        self.assertEqual(note.text, 'original')

    def test_invalid_task_add(self):
        self._post('manager_add_ticket_task', {'description': 'no subject'})
        self.assertFalse(Task.objects.exists())

    def test_invalid_task_detail_priority(self):
        task = self.create_task(self.ticket, priority=0)
        self._post('manager_task_detail', {'priorita': 'not-a-priority'},
                   task_id=task.code)
        task.refresh_from_db()
        self.assertEqual(task.priority, 0)

    def test_invalid_task_edit(self):
        task = self.create_task(self.ticket)
        self._post('manager_edit_task', {'subject': ''}, task_id=task.code)
        task.refresh_from_db()
        self.assertEqual(task.subject, 'Task')

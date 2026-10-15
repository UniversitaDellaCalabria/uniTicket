import io
import logging
import os
import zipfile

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from organizational_area.models import (
    OrganizationalStructureOffice,
    OrganizationalStructureOfficeEmployee,
)
from uni_ticket.models import (
    Log,
    Task,
    Ticket,
    Ticket2Ticket,
    TicketAssignment,
    TicketOperatorNote,
    TicketReply,
)

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_ManagementViews(BaseTicketEnvironment):
    """
    Covers the management views (shared by managers and operators)
    in uni_ticket/views/management.py
    """

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    # helpers

    def _messages(self, response):
        return [str(m) for m in response.context['messages']]

    def take_ticket(self, ticket, priority=0):
        assignment = TicketAssignment.objects.filter(
            ticket=ticket,
            taken_date__isnull=True,
            office__organizational_structure=self.structure_1
        ).first()
        response = self.client.post(
            reverse('uni_ticket:manager_manage_ticket',
                    kwargs={'structure_slug': self.structure_1.slug,
                            'ticket_id': ticket.code}),
            {'priority': priority, 'office': assignment.office},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertTrue(ticket.has_been_taken())
        return response

    def close_ticket(self, ticket):
        response = self.client.post(
            reverse('uni_ticket:manager_close_ticket',
                    kwargs={'structure_slug': self.structure_1.slug,
                            'ticket_id': ticket.code}),
            {'note': 'closing notes', 'status': 1},
            follow=True
        )
        ticket.refresh_from_db()
        self.assertTrue(ticket.is_closed)
        return response

    def create_task(self, ticket, subject='Task', **kwargs):
        return Task.objects.create(ticket=ticket,
                                   subject=subject,
                                   description=subject,
                                   created_by=self.staff_1,
                                   code=subject.replace(' ', '_'),
                                   **kwargs)

    def transfer_competence_readonly(self):
        """
        Structure 1 transfers ticket competence to Structure 2
        keeping a readonly access
        """
        self.take_ticket(self.ticket)
        self.client.post(
            reverse('uni_ticket:manager_add_ticket_competence_final',
                    kwargs={'structure_slug': self.structure_1.slug,
                            'ticket_id': self.ticket.code,
                            'new_structure_slug': self.structure_2.slug}),
            {'office_slug': self.office_1_str_2.slug,
             'follow': 'on',
             'readonly': 'on'},
            follow=True
        )
        can_manage = self.ticket.is_followed_in_structure(self.structure_1)
        self.assertTrue(can_manage['readonly'])

    def url(self, name, ticket=None, **kwargs):
        kwargs['structure_slug'] = kwargs.get('structure_slug',
                                              self.structure_1.slug)
        kwargs['ticket_id'] = (ticket or self.ticket).code
        return reverse(name, kwargs=kwargs)

    # ticket detail

    def test_ticket_detail_get(self):
        response = self.client.get(self.url('uni_ticket:manager_manage_ticket'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ticket'], self.ticket)
        # untaken office forms are prepared for the manager
        self.assertIn(self.office_1_str_1, response.context['offices_forms'])

    def test_ticket_detail_assign_to_operator(self):
        OrganizationalStructureOfficeEmployee.objects.create(
            employee=self.user_1, office=self.office_1_str_1
        )
        response = self.client.post(
            self.url('uni_ticket:manager_manage_ticket'),
            {'priorita': 1, 'assign_to': self.user_1.pk},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        assignment = TicketAssignment.objects.get(ticket=self.ticket,
                                                  office=self.office_1_str_1)
        self.assertEqual(assignment.taken_by, self.user_1)
        self.assertEqual(assignment.assigned_by, self.staff_1)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, 1)

    def test_ticket_detail_post_on_closed_ticket(self):
        self.take_ticket(self.ticket)
        self.close_ticket(self.ticket)
        response = self.client.post(self.url('uni_ticket:manager_manage_ticket'),
                                    {'priorita': 2},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Impossibile modificare un ticket chiuso",
                      self._messages(response))
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.priority, 2)

    @patch('uni_ticket.views.management.SIMPLE_USER_SHOW_PRIORITY', True)
    def test_ticket_detail_priority_shown_to_user(self):
        self.take_ticket(self.ticket)
        response = self.client.post(self.url('uni_ticket:manager_manage_ticket'),
                                    {'priorita': 2},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, 2)
        self.assertTrue(Log.objects.filter(object_id=self.ticket.pk,
                                           change_message__startswith='Priorità assegnata')
                                   .exists())

    # dependences

    def test_dependence_add_url_and_form(self):
        self.take_ticket(self.ticket)
        Ticket2Ticket.objects.create(subordinate_ticket=self.ticket,
                                     main_ticket=self.ticket_2,
                                     note='dep')
        response = self.client.get(self.url('uni_ticket:add_ticket_dependence_url'),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ticket'], self.ticket)
        self.assertIn('form', response.context)

    def test_dependence_add_main_already_used(self):
        self.take_ticket(self.ticket)
        # ticket_2 depends from ticket (still open)
        Ticket2Ticket.objects.create(subordinate_ticket=self.ticket_2,
                                     main_ticket=self.ticket,
                                     note='dep')
        self.take_ticket(self.ticket_2)
        ticket_3 = self.create_ticket(subject='Ticket 3', attachment=None,
                                      structure_slug=self.structure_1.slug,
                                      category=self.category_1_str_1)
        self.take_ticket(ticket_3)

        # ticket_3 can't depend from ticket_2 (ticket_2 depends from ticket)
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_dependence', ticket=ticket_3),
            {'ticket': self.ticket_2.code, 'note': 'note'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket2Ticket.objects.filter(subordinate_ticket=ticket_3)
                                              .exists())

        # ticket can't depend from ticket_3 (ticket blocks ticket_2)
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_dependence'),
            {'ticket': ticket_3.code, 'note': 'note'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket2Ticket.objects.filter(subordinate_ticket=self.ticket)
                                              .exists())

    def test_dependence_remove_main_not_in_structure(self):
        self.take_ticket(self.ticket)
        other_ticket = self.create_ticket(subject='Ticket Structure 2',
                                          attachment=None,
                                          structure_slug=self.structure_2.slug,
                                          category=self.category_1_str_2)
        self.assertTrue(other_ticket)
        t2t = Ticket2Ticket.objects.create(subordinate_ticket=self.ticket,
                                           main_ticket=other_ticket,
                                           note='dep')
        response = self.client.get(
            self.url('uni_ticket:remove_ticket_dependence',
                     main_ticket_id=other_ticket.code),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Ticket2Ticket.objects.filter(pk=t2t.pk).exists())

    # close / reopen

    def test_close_ticket_get_and_not_closable(self):
        self.take_ticket(self.ticket)
        response = self.client.get(self.url('uni_ticket:manager_close_ticket'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        # an open task makes ticket not closable
        self.create_task(self.ticket)
        response = self.client.post(self.url('uni_ticket:manager_close_ticket'),
                                    {'note': 'notes', 'status': 1},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)

    @patch('uni_ticket.views.management.send_app_io_message')
    def test_close_reopen_with_app_io(self, mock_send):
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        self.take_ticket(self.ticket)
        mock_send.return_value = {'message_id': 'id'}

        response = self.close_ticket(self.ticket)
        self.assertIn("Messaggio App IO inviato correttamente",
                      self._messages(response))

        response = self.client.get(self.url('uni_ticket:reopen_ticket'),
                                   follow=True)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)
        self.assertIn("Messaggio App IO inviato correttamente",
                      self._messages(response))
        self.assertEqual(mock_send.call_count, 2)

    @patch('uni_ticket.views.management.send_app_io_message',
           return_value={'error': 'App IO failure'})
    def test_close_with_app_io_error(self, mock_send):
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        self.take_ticket(self.ticket)
        response = self.close_ticket(self.ticket)
        self.assertTrue(any('App IO failure' in m
                            for m in self._messages(response)))

    @patch('uni_ticket.views.management.send_app_io_message')
    def test_reopen_with_app_io_error(self, mock_send):
        self.take_ticket(self.ticket)
        self.close_ticket(self.ticket)
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        mock_send.return_value = {'error': 'App IO failure'}
        response = self.client.get(self.url('uni_ticket:reopen_ticket'),
                                   follow=True)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)
        self.assertTrue(any('App IO failure' in m
                            for m in self._messages(response)))

    def test_reopen_not_allowed(self):
        self.take_ticket(self.ticket)
        reopen_url = self.url('uni_ticket:reopen_ticket')

        # not closed
        response = self.client.get(reopen_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('non è stata chiusa', str(response.context['avviso']))

        # notification ticket
        self.close_ticket(self.ticket)
        Ticket.objects.filter(pk=self.ticket.pk).update(is_notification=True)
        response = self.client.get(reopen_url, follow=True)
        self.assertIn('non può essere riaperta', str(response.context['avviso']))
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)

        # closed by user
        Ticket.objects.filter(pk=self.ticket.pk).update(is_notification=False,
                                                        closed_by=None)
        response = self.client.get(reopen_url, follow=True)
        self.assertIn("chiusa dall'utente", str(response.context['avviso']))
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)

    # competence

    def test_competence_add_final_get(self):
        self.take_ticket(self.ticket)
        response = self.client.get(
            self.url('uni_ticket:manager_add_ticket_competence_final',
                     new_structure_slug=self.structure_2.slug)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.office_1_str_2, response.context['offices'])

    def test_competence_add_private_office(self):
        self.take_ticket(self.ticket)
        self.office_1_str_2.is_private = True
        self.office_1_str_2.save()
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_competence_final',
                     new_structure_slug=self.structure_2.slug),
            {'office_slug': self.office_1_str_2.slug, 'follow': 'on'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TicketAssignment.objects.filter(
            ticket=self.ticket, office=self.office_1_str_2).exists())

    def test_competence_add_already_assigned(self):
        self.take_ticket(self.ticket)
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_competence_final',
                     new_structure_slug=self.structure_1.slug),
            {'office_slug': self.office_1_str_1.slug, 'follow': 'on'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('già di competenza' in m
                            for m in self._messages(response)))
        self.assertEqual(TicketAssignment.objects.filter(
            ticket=self.ticket, office=self.office_1_str_1).count(), 1)

    def test_competence_add_without_follow(self):
        self.take_ticket(self.ticket)
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_competence_final',
                     new_structure_slug=self.structure_2.slug),
            {'office_slug': self.office_1_str_2.slug},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        old = TicketAssignment.objects.get(ticket=self.ticket,
                                           office=self.office_1_str_1)
        self.assertFalse(old.follow)
        self.assertTrue(TicketAssignment.objects.filter(
            ticket=self.ticket, office=self.office_1_str_2).exists())

    def test_competence_add_readonly_selected_default_office(self):
        self.take_ticket(self.ticket)
        default_office = self.structure_1.get_default_office()
        response = self.client.post(
            self.url('uni_ticket:manager_add_ticket_competence_final',
                     new_structure_slug=self.structure_2.slug),
            {'office_slug': self.office_1_str_2.slug,
             'follow': 'on',
             'readonly': 'on',
             'selected_office': default_office.slug},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('non può essere' in m and 'sola lettura' in m
                            for m in self._messages(response)))
        self.assertTrue(TicketAssignment.objects.filter(
            ticket=self.ticket, office=self.office_1_str_2).exists())

    def test_competence_leave_get_and_last_office(self):
        self.take_ticket(self.ticket)
        leave_url = self.url('uni_ticket:leave_ticket_competence')
        response = self.client.get(leave_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        # the only office that follows the ticket can't leave it
        response = self.client.post(leave_url,
                                    {'office': self.office_1_str_1.slug},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Operazione non consentita' in m
                            for m in self._messages(response)))
        assignment = TicketAssignment.objects.get(ticket=self.ticket,
                                                  office=self.office_1_str_1)
        self.assertTrue(assignment.follow)

    # readonly competence

    def test_readonly_competence_blocks_changes(self):
        task = self.create_task(self.ticket)
        self.transfer_competence_readonly()

        response = self.client.post(
            self.url('uni_ticket:manager_ticket_message'),
            {'subject': 'subject', 'text': 'text'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket).exists())

        response = self.client.post(
            self.url('uni_ticket:manager_ticket_notes'),
            {'text': 'text', 'visibility': 0},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TicketOperatorNote.objects.filter(ticket=self.ticket)
                                                   .exists())

        response = self.client.post(
            self.url('uni_ticket:manager_task_detail', task_id=task.code),
            {'priorita': 2},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertNotEqual(task.priority, 2)

    # messages

    def test_message_untaken_ticket(self):
        message_url = self.url('uni_ticket:manager_ticket_message')
        response = self.client.get(message_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("La richiesta deve essere prima presa in carico",
                      self._messages(response))

        response = self.client.post(message_url,
                                    {'subject': 'subject', 'text': 'text'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket).exists())

    def test_message_closed_ticket(self):
        self.take_ticket(self.ticket)
        Ticket.objects.filter(pk=self.ticket.pk).update(is_closed=True)
        response = self.client.post(self.url('uni_ticket:manager_ticket_message'),
                                    {'subject': 'subject', 'text': 'text'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.context['avviso']),
                         "La richiesta non è modificabile")
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket).exists())

    def test_message_read_user_replies(self):
        self.take_ticket(self.ticket)
        reply = TicketReply.objects.create(ticket=self.ticket,
                                           owner=self.ticket.created_by,
                                           subject='user message',
                                           text='text')
        response = self.client.get(self.url('uni_ticket:manager_ticket_message'))
        self.assertEqual(response.status_code, 200)
        reply.refresh_from_db()
        self.assertEqual(reply.read_by, self.staff_1)
        self.assertTrue(reply.read_date)

    # operator notes

    def test_notes(self):
        notes_url = self.url('uni_ticket:manager_ticket_notes')

        # ticket must be taken
        response = self.client.get(notes_url, follow=True)
        self.assertIn("La richiesta deve essere prima presa in carico",
                      self._messages(response))
        response = self.client.post(notes_url, {'text': 'text', 'visibility': 0},
                                    follow=True)
        self.assertIn("La richiesta deve essere prima presa in carico",
                      self._messages(response))
        self.assertFalse(TicketOperatorNote.objects.exists())

        self.take_ticket(self.ticket)
        response = self.client.get(notes_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        # create
        response = self.client.post(notes_url, {'text': 'my note', 'visibility': 0},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        note = TicketOperatorNote.objects.get(ticket=self.ticket)
        self.assertEqual(note.owner, self.staff_1)
        self.assertEqual(note.structure, self.structure_1)

        # edit
        note_url = self.url('uni_ticket:manager_ticket_note', note_id=note.pk)
        response = self.client.get(note_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, note)
        response = self.client.post(note_url,
                                    {'text': 'my note edited', 'visibility': 1},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.text, 'my note edited')
        self.assertEqual(note.visibility, 1)

        # delete
        response = self.client.get(
            self.url('uni_ticket:manage_ticket_note_delete', note_id=note.pk),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TicketOperatorNote.objects.filter(pk=note.pk).exists())

    # tasks

    def test_task_add_get_and_mail_to_offices(self):
        self.take_ticket(self.ticket)
        add_url = self.url('uni_ticket:manager_add_ticket_task')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        with patch('uni_ticket.views.management.send_ticket_mail_to_operators') as mock_mail:
            response = self.client.post(add_url,
                                        {'subject': 'New task',
                                         'description': 'description',
                                         'priority': 1,
                                         'ordering': 10,
                                         'mail_to_offices': [self.office_1_str_1.pk]},
                                        follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(ticket=self.ticket,
                                            subject='New task').exists())
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_mail.call_args.kwargs['office'], self.office_1_str_1)

    def test_task_close_with_mail_and_reopen_with_attachment(self):
        self.take_ticket(self.ticket)
        task = self.create_task(self.ticket)
        with patch('uni_ticket.views.management.send_ticket_mail_to_operators') as mock_mail:
            response = self.client.post(
                self.url('uni_ticket:manager_close_task', task_id=task.code),
                {'closing_reason': 'done',
                 'closing_status': 1,
                 'closing_attachment': self.create_fake_file(name='closing'),
                 'mail_to_offices': [self.office_1_str_1.pk]},
                follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_mail.call_count, 1)
        task.refresh_from_db()
        self.assertTrue(task.is_closed)
        self.assertTrue(task.closing_attachment)
        path = task.closing_attachment.path
        self.assertTrue(os.path.exists(path))

        # already closed
        response = self.client.get(
            self.url('uni_ticket:manager_close_task', task_id=task.code)
        )
        self.assertEqual(str(response.context['avviso']), "Attività già chiusa!")

        # edit of a closed task is forbidden
        response = self.client.post(
            self.url('uni_ticket:manager_edit_task', task_id=task.code),
            {'subject': 'edited', 'description': 'd', 'priority': 0,
             'ordering': 10},
            follow=True
        )
        self.assertIn("Impossibile modificare un'attività chiusa",
                      self._messages(response))
        # priority change of a closed task is forbidden
        response = self.client.post(
            self.url('uni_ticket:manager_task_detail', task_id=task.code),
            {'priorita': 2},
            follow=True
        )
        self.assertIn("Impossibile modificare un'attività chiusa",
                      self._messages(response))
        task.refresh_from_db()
        self.assertNotEqual(task.subject, 'edited')
        self.assertNotEqual(task.priority, 2)

        # reopen removes closing attachment
        response = self.client.get(
            self.url('uni_ticket:reopen_task', task_id=task.code),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.is_closed)
        self.assertFalse(os.path.exists(path))

        # reopen a not closed task
        response = self.client.get(
            self.url('uni_ticket:reopen_task', task_id=task.code)
        )
        self.assertEqual(str(response.context['avviso']),
                         "L'attività non è stata chiusa")

    def test_task_reopen_attachment_remove_error(self):
        self.take_ticket(self.ticket)
        task = self.create_task(
            self.ticket, is_closed=True,
            closing_attachment=SimpleUploadedFile('c.pdf', b'content')
        )
        with patch('uni_ticket.views.management.os.remove',
                   side_effect=OSError('boom')):
            response = self.client.get(
                self.url('uni_ticket:reopen_task', task_id=task.code),
                follow=True
            )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.is_closed)

    def test_task_remove_with_closing_attachment(self):
        self.take_ticket(self.ticket)
        task = self.create_task(
            self.ticket, closing_attachment=SimpleUploadedFile('c.pdf', b'content')
        )
        path = task.closing_attachment.path
        self.assertTrue(os.path.exists(path))
        response = self.client.get(
            self.url('uni_ticket:task_remove', task_id=task.code),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertFalse(os.path.exists(path))

        # filesystem errors are logged, task is deleted anyway
        task = self.create_task(
            self.ticket, subject='Task 2',
            closing_attachment=SimpleUploadedFile('c.pdf', b'content')
        )
        with patch('uni_ticket.views.management.os.remove',
                   side_effect=OSError('boom')):
            self.client.get(
                self.url('uni_ticket:task_remove', task_id=task.code),
                follow=True
            )
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_task_attachment_delete_not_owner(self):
        self.take_ticket(self.ticket)
        task = self.create_task(
            self.ticket, attachment=SimpleUploadedFile('a.pdf', b'content')
        )
        # user_1 is operator of structure 1 default office
        self.structure_1_default_office_operator_login()
        response = self.client.get(
            self.url('uni_ticket:manage_elimina_allegato_task', task_id=task.code)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.context['avviso']),
                         "Permessi di modifica dell'attività mancanti")
        task.refresh_from_db()
        self.assertTrue(task.attachment)

    # export

    def test_export_detailed_report_forbidden(self):
        export_url = reverse('uni_ticket:manage_export_detailed_report',
                             kwargs={'structure_slug': self.structure_1.slug})
        # GET is not allowed
        response = self.client.get(export_url)
        self.assertEqual(str(response.context['avviso']), "Forbidden")
        self.assertEqual(response.status_code, 403)

        # simple user
        self.structure_2_default_office_operator_login()
        response = self.client.post(export_url, {'ticket_code': [self.ticket.code]})
        self.assertEqual(str(response.context['avviso']), "Forbidden")
        self.assertEqual(response.status_code, 403)

    def test_export_detailed_report_no_records(self):
        # user_1 is an operator that doesn't follow the ticket
        self.structure_1_default_office_operator_login()
        export_url = reverse('uni_ticket:manage_export_detailed_report',
                             kwargs={'structure_slug': self.structure_1.slug})
        response = self.client.post(export_url,
                                    {'ticket_code': ['not-exists', self.ticket.code]})
        self.assertEqual(str(response.context['avviso']),
                         "Nessun record da esportare")

    def test_export_detailed_report_single_category(self):
        export_url = reverse('uni_ticket:manage_export_detailed_report',
                             kwargs={'structure_slug': self.structure_1.slug})
        response = self.client.post(
            export_url, {'ticket_code': [self.ticket.code, self.ticket_2.code]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

    def test_export_detailed_report_multiple_categories(self):
        category_2 = self.add_new_category(cat_name='Category 2 Structure 1',
                                           structure_slug=self.structure_1.slug)
        self.create_input_module_in_category(name='module',
                                             structure_slug=self.structure_1.slug,
                                             category_slug=category_2.slug)
        module = category_2.ticketcategorymodule_set.first()
        self.enable_input_module(self.structure_1.slug, category_2.slug, module)
        self.assign_office_to_category(self.structure_1.slug, category_2,
                                       self.office_1_str_1.slug)
        self.enable_category(self.structure_1.slug, category_2)
        self.assertTrue(category_2.is_active)
        ticket_3 = self.create_ticket(subject='Ticket 3', attachment=None,
                                      structure_slug=self.structure_1.slug,
                                      category=category_2)
        self.assertTrue(ticket_3)

        export_url = reverse('uni_ticket:manage_export_detailed_report',
                             kwargs={'structure_slug': self.structure_1.slug})
        with patch('uni_ticket.views.management.export_category_zip',
                   side_effect=[HttpResponse(b'zip-content'),
                                Exception('broken category')]):
            response = self.client.post(
                export_url, {'ticket_code': [self.ticket.code, ticket_3.code]}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        # the broken category is skipped
        self.assertEqual(len(archive.namelist()), 1)

    # statistics

    def test_manager_statistics(self):
        stats_url = reverse('uni_ticket:manager_statistics',
                            kwargs={'structure_slug': self.structure_1.slug})
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['structure'], self.structure_1)
        self.assertIn('offices', response.context)

        today = timezone.localtime().date()
        response = self.client.post(
            stats_url,
            {'date_start': (today - timezone.timedelta(days=5)).isoformat(),
             'date_end': today.isoformat(),
             'office_slug': [self.office_1_str_1.slug],
             'category_slug': [self.category_1_str_1.slug]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['office_slugs'],
                         [self.office_1_str_1.slug])
        self.assertEqual(response.context['category_slugs'],
                         [self.category_1_str_1.slug])

    def test_manager_statistics_wrong_dates(self):
        stats_url = reverse('uni_ticket:manager_statistics',
                            kwargs={'structure_slug': self.structure_1.slug})
        today = timezone.localtime().date()
        # start > end
        response = self.client.post(
            stats_url,
            {'date_start': today.isoformat(),
             'date_end': (today - timezone.timedelta(days=5)).isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('non può essere successiva' in m
                            for m in self._messages(response)))
        # too wide time window
        response = self.client.post(
            stats_url,
            {'date_start': '2000-01-01', 'date_end': today.isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('finestra oraria massima' in m
                            for m in self._messages(response)))
        self.assertNotEqual(response.context['date_start'], '2000-01-01')

    def test_superuser_statistics(self):
        self.staff_1.is_superuser = True
        self.staff_1.save()
        response = self.client.get(reverse('uni_ticket:superuser_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'management/statistics_superuser.html')

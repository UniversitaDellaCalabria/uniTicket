import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_ManagementFunctions(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()
        # Create Office 1
        # Create a new office in Structure 1
        off_name = 'New Office'
        params = {'name': off_name,
                  'description': 'Description new office'}
        response = self.client.post(reverse('uni_ticket:manager_office_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug,}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.office_1 = OrganizationalStructureOffice.objects.get(name=off_name)

    def test_tickets(self):
        # Tickets list
        response = self.client.post(reverse('uni_ticket:manager_tickets',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    follow=True)
        assert response.status_code == 200
        assert self.ticket in response.context['ticket_non_gestiti']

    def test_take_ticket_and_test(self):
        # Take ticket
        params = {'priorita': 0}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200

        # Submit message (only if the ticket is open)
        subject = 'Ticket 1 message'
        params = {'subject': subject,
                  'text': 'Ticket message'}
        response = self.client.post(reverse('uni_ticket:ticket_message',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        message = TicketReply.objects.filter(ticket=self.ticket,
                                             owner=self.staff_1).first()
        assert message

        # Submit message (fails until ticket is not taken)
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': message.pk}),
                                   follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket,
                                                    owner=self.staff_1))

        # Delete ticket
        # Fails, ticket is taken
        response = self.client.get(reverse('uni_ticket:ticket_delete',
                                           kwargs={'ticket_id': self.ticket.code}),
                                   follow=True)
        assert response.status_code == 200
        assert self.ticket

        # Close ticket
        params = {'note': "notes"}
        response = self.client.post(reverse('uni_ticket:manager_close_ticket',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert self.ticket.is_closed

        # Reopen ticket
        response = self.client.get(reverse('uni_ticket:reopen_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                   follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)


    def test_category_field_edit(self):
        # Edit input module field
        # This fails, because a ticket exists with this input module
        field_name = 'file_field_1 edited'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_field_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'field_id': self.input_field.pk}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.input_field.refresh_from_db()
        self.assertFalse(self.input_field.name == field_name)

    def test_category_field_remove(self):
        # Remove field
        # This fails, because a ticket exists with this input module
        response = self.client.get(reverse('uni_ticket:manager_category_input_field_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'field_id': self.input_field.pk}),
                                    follow=True)
        assert response.status_code == 200
        assert TicketCategoryInputList.objects.filter(category_module=self.module_2).first()

    def test_add_field_to_input_module(self):
        # Add file field to input module
        # Fails, it has a ticket linked to
        field_name = 'file_field_2'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketCategoryInputList.objects.filter(category_module=self.module_2,
                                                                name=field_name).first())

    def test_add_ticket_competence_and_manage(self):
        # Take ticket
        params = {'priorita': 2}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert self.ticket.priority == 2
        assert self.ticket.is_taken

        # Select categories of Structure 2
        response = self.client.get(reverse('uni_ticket:manager_add_ticket_competence',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'ticket_id': self.ticket.code}),
                                   follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200

        # Assign ticket to Category_3 (Structure 2)
        # Follow and continue to manage ticket (staff_1, manager of Structure 1)
        params = {'category_slug': self.category_1_str_2.slug,
                  'follow': 'on',
                  # 'readonly': False,
        }
        response = self.client.post(reverse('uni_ticket:manager_add_ticket_competence',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'new_structure_slug': self.structure_2.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        assert self.ticket.code in TicketAssignment.get_ticket_per_structure(self.structure_1)
        assert self.ticket.code in TicketAssignment.get_ticket_per_structure(self.structure_2)

        # Change priority to ticket
        params = {'priorita': 1}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert self.ticket.priority == 1

        # Structure 2 default office operator login
        self.structure_2_default_office_operator_login()

        # Change priority to ticket (fails because User_2 hasn't privileges on Structure_1)
        params = {'priorita': -1}
        response = self.client.post(reverse('uni_ticket:operator_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert not self.ticket.priority == -1

        # Change priority to ticket (success!)
        params = {'priorita': -1}
        response = self.client.post(reverse('uni_ticket:operator_manage_ticket',
                                            kwargs={'structure_slug': self.structure_2.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert self.ticket.priority == -1

    def test_add_ticket_competence_and_readonly(self):
        # Take ticket
        params = {'priorita': 2}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket.refresh_from_db()
        assert self.ticket.priority == 2
        assert self.ticket.is_taken

        # Select categories of Structure 2
        response = self.client.get(reverse('uni_ticket:manager_add_ticket_competence',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'ticket_id': self.ticket.code}),
                                   follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200

        # Assign ticket to Category_3 (Structure 2)
        # Follow and continue to manage ticket (staff_1, manager of Structure 1)
        params = {'category_slug': self.category_1_str_2.slug,
                  'follow': 'on',
                  'readonly': True,
        }
        response = self.client.post(reverse('uni_ticket:manager_add_ticket_competence',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'new_structure_slug': self.structure_2.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        assert self.ticket.code in TicketAssignment.get_ticket_per_structure(self.structure_1)
        assert self.ticket.code in TicketAssignment.get_ticket_per_structure(self.structure_2)

        # Change priority to ticket (this fails, is readonly!)
        params = {'priorita': 1}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        self.ticket.refresh_from_db()
        assert not self.ticket.priority == 1

    def test_ticket_dependence(self):
        # Take ticket
        params = {'priorita': 0}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200

        params = {'priorita': 2}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket_2.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.ticket_2.refresh_from_db()
        assert self.ticket_2.priority == 2

        params = {'ticket': self.ticket_2.code,
                  'note': "Il ticket 1 dipende dal ticket 2"}
        response = self.client.post(reverse('uni_ticket:manager_add_ticket_dependence',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        t2t = Ticket2Ticket.objects.filter(slave_ticket=self.ticket,
                                           master_ticket=self.ticket_2).first()
        assert t2t

        response = self.client.get(reverse('uni_ticket:remove_ticket_dependence',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'master_ticket_id': self.ticket_2.code}),
                                    follow=True)
        assert response.status_code == 200
        t2t = Ticket2Ticket.objects.filter(slave_ticket=self.ticket,
                                           master_ticket=self.ticket_2)
        self.assertFalse(t2t)

    def test_ticket_message(self):
        # Take ticket
        params = {'priorita': 0}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)

        # Submit message (fails until ticket is not taken)
        subject = 'Ticket 1 message from manager'
        params = {'subject': subject,
                  'text': 'Ticket message'}
        response = self.client.post(reverse('uni_ticket:manager_ticket_message',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        assert TicketReply.objects.filter(ticket=self.ticket,
                                              owner=self.staff_1,
                                              subject=subject)

    def test_task(self):
        # Take ticket
        params = {'priorita': 0}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200

        # Create new task
        subject = 'Ticket 1 task 1'
        params = {'subject': subject,
                  'description': "Task 1 description",
                  'priority': 1}
        response = self.client.post(reverse('uni_ticket:manager_add_ticket_task',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        task = Task.objects.filter(ticket=self.ticket,
                                   subject=subject,
                                   priority=1).first()
        assert task

        # Edit task priority
        params = {'priorita': 2}
        response = self.client.post(reverse('uni_ticket:manager_task_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        assert task.priority == 2

        # Edit task
        attachment = self.create_fake_file()
        subject = "Ticket 1 task edited"
        params = {'subject': subject,
                  'description': "new descr",
                  'priority': -1,
                  'attachment': attachment}
        response = self.client.post(reverse('uni_ticket:manager_edit_task',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        assert task.priority == -1
        assert task.attachment
        assert task.subject == subject

        # Download attachment
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs={'ticket_id': self.ticket.code,
                                                   'task_id': task.code}),
                                   follow=True)
        self.assertFalse(response.status_code == 404)

        # Delete attachment
        response = self.client.get(reverse('uni_ticket:manage_elimina_allegato_task',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'ticket_id': self.ticket.code,
                                                   'task_id': task.code}),
                                   follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        self.assertFalse(task.attachment)

        # Close task without motivation (fails!)
        params = {}
        response = self.client.post(reverse('uni_ticket:manager_close_task',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        assert not task.is_closed

        # Close task with motivation
        params = {'note': "notes"}
        response = self.client.post(reverse('uni_ticket:manager_close_task',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        assert task.is_closed

        # Reopen task
        response = self.client.get(reverse('uni_ticket:reopen_task',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                   follow=True)
        assert response.status_code == 200
        task.refresh_from_db()
        assert not task.is_closed

        # Remove task
        response = self.client.get(reverse('uni_ticket:task_remove',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'task_id': task.code}),
                                   follow=True)
        assert response.status_code == 200
        self.assertFalse(Task.objects.filter(ticket=self.ticket))


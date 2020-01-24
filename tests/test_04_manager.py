import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_Manager2Functions(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        # Create Office 1
        # Create a new office in Structure 1
        off_name = 'Office 1'
        params = {'name': off_name,
                  'description': 'Description office 1'}
        response = self.client.post(reverse('uni_ticket:manager_office_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug,}),
                                    params,
                                    follow=True)
        self.office_1 = OrganizationalStructureOffice.objects.get(name=off_name)

    def test_take_ticket_and_test(self):
        # Take ticket
        params = {'priorita': 0}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)

        # Submit message (only if the ticket is open)
        subject = 'Ticket 1 message'
        params = {'subject': subject,
                  'text': 'Ticket message'}
        response = self.client.post(reverse('uni_ticket:ticket_message',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert TicketReply.objects.filter(ticket=self.ticket, owner=self.staff_1)

        # Delete ticket
        # Fails, ticket is taken
        response = self.client.get(reverse('uni_ticket:ticket_delete',
                                           kwargs={'ticket_id': self.ticket.code}),
                                   follow=True)
        assert Ticket.objects.filter(code=self.ticket.code).first()

    def test_category_field_edit(self):
        # Edit input module field
        # This fails, because a ticket exists with this input module
        field_name = 'file_field_1 edited'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_field_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk,
                                                    'field_id': self.input_field.pk}),
                                    params,
                                    follow=True)
        self.input_field.refresh_from_db()
        assert not self.input_field.name == field_name

    def test_category_field_remove(self):
        # Remove field
        # This fails, because a ticket exists with this input module
        response = self.client.get(reverse('uni_ticket:manager_category_input_field_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk,
                                                    'field_id': self.input_field.pk}),
                                    follow=True)
        assert TicketCategoryInputList.objects.filter(category_module=self.module).first()

    def test_add_field_to_input_module(self):
        # Add file field to input module
        # Fails, it has a ticket linked to
        field_name = 'file_field_2'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk}),
                                    params,
                                    follow=True)
        assert not TicketCategoryInputList.objects.filter(category_module=self.module,
                                                          name=field_name).first()

    def test_add_ticket_competence_and_manage(self):
        # Take ticket
        params = {'priorita': 2}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        self.ticket.refresh_from_db()
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
        params = {'category_slug': self.category_3.slug,
                  'follow': 'on',
                  'readonly': False,
        }
        response = self.client.post(reverse('uni_ticket:manager_add_ticket_competence',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code,
                                                    'new_structure_slug': self.structure_2.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        assert self.ticket.pk in TicketAssignment.get_ticket_per_structure(self.structure_2)
        assert self.ticket.is_taken

        # Change priority to ticket
        params = {'priorita': 1}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        self.ticket.refresh_from_db()
        assert self.ticket.priority == 1

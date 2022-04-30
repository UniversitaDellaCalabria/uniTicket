import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.settings import TICKET_CREATE_BUTTON_NAME, TICKET_GENERATE_URL_BUTTON_NAME
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_category_office_env import BaseCategoryOfficeEnvironment


logger = logging.getLogger('my_logger')


class BaseTicketEnvironment(BaseCategoryOfficeEnvironment):

    def create_fake_file(self, name="test", ext="pdf",
                         content_type="application/pdf"):
        """
        Create a fake file to simulate upload
        """
        return SimpleUploadedFile("{}.{}".format(name, ext),
                                  b"file_content",
                                  content_type=content_type)

    def create_ticket(self, subject, attachment,
                      structure_slug, category):
        """
         Create new ticket
         this may fail silently -> ticket object would be None
        """
        
        # New ticket preload (select category)
        response = self.client.get(reverse('uni_ticket:new_ticket_preload',
                                           kwargs={'structure_slug': structure_slug,}),
                                   follow=True)
        self.assertTrue(response.status_code == 200)
        self.assertTrue(category in response.context['categorie'])

        # Add ticket (base form with an attachment)
        params = {'ticket_subject': subject,
                  'ticket_description': subject,
                  TICKET_CREATE_BUTTON_NAME: 'conferma'}
        if attachment:
            params['file_field_1'] = attachment
        response = self.client.post(reverse('uni_ticket:add_new_ticket',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category.slug}),
                                    params,
                                    follow=True)
        self.assertTrue(response.status_code == 200)
        ticket = Ticket.objects.filter(subject=subject).first()
        return ticket

    def delegate_ticket(self, subject, attachment,
                        structure_slug, category):
        # Create new ticket
        # New ticket preload (select category)
        response = self.client.get(reverse('uni_ticket:new_ticket_preload',
                                           kwargs={'structure_slug': structure_slug,}),
                                   follow=True)
        assert response.status_code == 200
        assert category in response.context['categorie']

        # Add ticket (base form with an attachment)
        params = {'ticket_subject': subject,
                  'ticket_description': subject,
                  TICKET_GENERATE_URL_BUTTON_NAME: 'delega'}
        response = self.client.post(reverse('uni_ticket:add_new_ticket',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        assert response.context['url_to_import']

    def setUp(self):
        super().setUp()

        # Generate URL pre-filled ticket
        self.ticket = self.delegate_ticket(subject='Ticket 1',
                                           attachment=self.create_fake_file(),
                                           structure_slug=self.structure_1.slug,
                                           category=self.category_1_str_1)

        # Create new ticket
        self.ticket = self.create_ticket(subject='Ticket 1',
                                         attachment=self.create_fake_file(),
                                         structure_slug=self.structure_1.slug,
                                         category=self.category_1_str_1)
        assert self.ticket

        # Add ticket 2(base form)
        # Raise error because category_1_str_1 doesn't allow multiple
        # open tickets for same user
        self.category_1_str_1.user_multiple_open_tickets = False
        self.category_1_str_1.save()
        self.category_1_str_1.refresh_from_db()
        self.ticket_2 = self.create_ticket(
            subject='Ticket 2',
            attachment=None,
            structure_slug=self.structure_1.slug,
            category=self.category_1_str_1
        )
        assert not self.ticket_2

        # Add ticket 2(base form)
        # Create new ticket
        self.category_1_str_1.user_multiple_open_tickets = True
        self.category_1_str_1.save()
        self.category_1_str_1.refresh_from_db()
        self.ticket_2 = self.create_ticket(subject='Ticket 2',
                                           attachment=None,
                                           structure_slug=self.structure_1.slug,
                                           category=self.category_1_str_1)
        assert self.ticket_2

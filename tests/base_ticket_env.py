import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from uni_ticket.models import *
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
        # Create new ticket
        # New ticket preload (select category)
        response = self.client.get(reverse('uni_ticket:new_ticket_preload',
                                           kwargs={'structure_slug': structure_slug,}),
                                   follow=True)
        assert response.status_code == 200
        assert category in response.context['categorie']

        # Add ticket (base form with an attachment)
        params = {'ticket_subject': subject,
                  'ticket_description': subject}
        if attachment:
            params['file_field_1'] = attachment
        response = self.client.post(reverse('uni_ticket:add_new_ticket',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        ticket = Ticket.objects.filter(subject=subject).first()
        assert ticket
        return ticket

    def setUp(self):
        super().setUp()

        # Create new ticket
        self.ticket = self.create_ticket(subject='Ticket 1',
                                         attachment=self.create_fake_file(),
                                         structure_slug=self.structure_1.slug,
                                         category=self.category_1_str_1)

        # Add ticket 2(base form)
        # Create new ticket
        self.ticket_2 = self.create_ticket(subject='Ticket 2',
                                           attachment=None,
                                           structure_slug=self.structure_1.slug,
                                           category=self.category_1_str_1)

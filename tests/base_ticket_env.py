import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_category_env import BaseCategoryEnvironment


logger = logging.getLogger('my_logger')


class BaseTicketEnvironment(BaseCategoryEnvironment):

    def create_fake_file(self, name="test", ext="pdf",
                         content_type="application/pdf"):
        """
        Create a fake file to simulate upload
        """
        return SimpleUploadedFile("{}.{}".format(name, ext),
                                  b"file_content",
                                  content_type=content_type)

    def setUp(self):
        super().setUp()

        # Create new ticket
        # New ticket preload (select category)
        response = self.client.get(reverse('uni_ticket:new_ticket_preload',
                                           kwargs={'structure_slug': self.structure_1.slug,}),
                                   follow=True)
        assert self.category_1 in response.context['categorie']

        # Add ticket (base form with an attachment)
        attachment = self.create_fake_file()
        subject = 'Ticket 1'
        params = {'ticket_subject': subject,
                  'ticket_description': 'Description category 1',
                  'file_field_1': attachment}
        response = self.client.post(reverse('uni_ticket:add_new_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        self.ticket = Ticket.objects.first()
        assert self.ticket

import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_GenericFunctions(BaseTicketEnvironment):

    def test_opened_tickets_page(self):
        response = self.client.get(reverse('uni_ticket:manager_opened_ticket',
                                           kwargs={'structure_slug': self.structure_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        self.assertEquals(response.context['structure'], self.structure_1)

    def test_closed_tickets_page(self):
        response = self.client.get(reverse('uni_ticket:manager_closed_ticket',
                                           kwargs={'structure_slug': self.structure_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        self.assertEquals(response.context['structure'], self.structure_1)

    def test_unassigned_tickets_page(self):
        response = self.client.get(reverse('uni_ticket:manager_unassigned_ticket',
                                           kwargs={'structure_slug': self.structure_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        self.assertEquals(response.context['structure'], self.structure_1)

    def test_email_notify_change(self):
        self.structure_1_default_office_operator_login()
        email_notify = self.user_1.email_notify
        response = self.client.post(reverse('uni_ticket:email_notify_change'),
                                    {}, follow=True)
        assert response.status_code == 200
        self.user_1.refresh_from_db()
        if not self.user_1.email:
            assert response.context['data']['error']
        else:
            assert response.context['data']['email'] == self.user_1.email
            self.assertFalse(self.user_1.email_notify == email_notify)





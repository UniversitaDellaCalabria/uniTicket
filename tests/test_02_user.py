import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_UserFunctions(BaseTicketEnvironment):

    def test_user_dashboard(self):
        # Dashboard
        response = self.client.get(reverse('uni_ticket:user_dashboard'),
                                   follow=True)
        assert response.status_code == 200
        assert response.context['ticket_non_gestiti'] > 0
        # assert self.ticket in response.context['ticket_non_gestiti']

    def test_edit_ticket(self):
        # Edit ticket
        subject = 'Ticket 1 Edited'
        params = {'ticket_subject': subject,
                  'ticket_description': 'Description category 1 Edited'}
        response = self.client.post(reverse('uni_ticket:ticket_edit',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200
        self.assertEqual(self.ticket.subject, subject)

    def test_delete_attachment(self):
        # Delete attachment
        assert self.ticket.get_allegati_dict()
        response = self.client.get(reverse('uni_ticket:delete_my_attachment',
                                            kwargs={'ticket_id': self.ticket.code,
                                                    'attachment': 'file_field_1'}),
                                   follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200
        self.assertFalse(self.ticket.get_allegati_dict())

    def test_close_ticket(self):
        # Close ticket
        params = {'note': 'My notes',
                  'status': 1}
        response = self.client.post(reverse('uni_ticket:user_close_ticket',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200
        assert self.ticket.is_closed

        # Delete ticket (fails because ticket is closed!)
        response = self.client.get(reverse('uni_ticket:ticket_delete',
                                           kwargs={'ticket_id': self.ticket.code}),
                                   follow=True)
        self.ticket.refresh_from_db()
        assert response.status_code == 200
        assert self.ticket

    def test_ticket_deletion(self):
        # Delete ticket
        code = self.ticket.code
        response = self.client.get(reverse('uni_ticket:ticket_delete',
                                           kwargs={'ticket_id': code}),
                                   follow=True)
        assert response.status_code == 200
        self.assertFalse(Ticket.objects.filter(code=code))

    def test_ticket_message(self):
        # Submit message (fails until ticket is not taken)
        subject = 'Ticket 1 message'
        params = {'subject': subject,
                  'text': 'Ticket message'}
        response = self.client.post(reverse('uni_ticket:ticket_message',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket,
                                                    owner=self.staff_1))

    def test_message_untaken_ticket(self):
        # Submit message (only if the ticket is open)
        subject = 'Ticket 1 message'
        params = {'subject': subject,
                  'text': 'Ticket message'}
        response = self.client.post(reverse('uni_ticket:ticket_message',
                                            kwargs={'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket,
                                                    owner=self.staff_1))

    def test_download_attachment(self):
        response = self.client.get(reverse('uni_ticket:download_attachment',
                                            kwargs={'ticket_id': self.ticket.code,
                                                    'attachment': 'file_field_1'}),
                                   follow=True)
        assert response.status_code == 200

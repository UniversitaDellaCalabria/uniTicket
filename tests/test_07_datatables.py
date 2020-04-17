import json
import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_DatatablesFunctions(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.post_data = json.dumps({"draw":1,
                                     "order":[{"column":0,"dir":"asc"}],
                                     "start":0,
                                     "length":10,
                                     "search":{"value":"","regex":False}
                                    })

    def test_manager_unassigned_tickets_json(self):
        self.structure_1_manager_login()
        response = self.client.post(reverse('uni_ticket:manager_unassigned_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        data = response_json['data']
        assert data

    def test_manager_opened_tickets_json_fails(self):
        self.structure_1_manager_login()
        response = self.client.post(reverse('uni_ticket:manager_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        data = response_json['data']
        self.assertFalse(data)

    def test_manager_opened_tickets_json(self):
        self.structure_1_manager_login()
        # Take ticket
        assignment = TicketAssignment.objects.filter(ticket=self.ticket,
                                                     taken_date__isnull=True,
                                                     office__organizational_structure=self.structure_1).first()
        params = {'priority': 0, 'office': assignment.office}
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        response = self.client.post(reverse('uni_ticket:manager_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        data = response_json['data']
        assert data

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

    def test_user_json(self):
        self.structure_1_manager_login()

        # user_all_tickets_json
        response = self.client.post(reverse('uni_ticket:user_all_tickets_json'),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # user_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:user_opened_ticket_json'),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # user_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:user_closed_ticket_json'),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # user_unassigned_ticket_json
        response = self.client.post(reverse('uni_ticket:user_unassigned_ticket_json'),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        # data = response_json['data']
        # assert data
        assert response.status_code == 200

    def test_operator_json(self):
        self.structure_1_default_office_operator_login()

        # operator_all_tickets_json
        response = self.client.post(reverse('uni_ticket:operator_all_tickets_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # operator_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:operator_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # operator_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:operator_my_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # operator_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:operator_closed_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        assert response.status_code == 200

        # operator_unassigned_ticket_json
        response = self.client.post(reverse('uni_ticket:operator_unassigned_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        json.loads(response_string)
        # data = response_json['data']
        # assert data
        assert response.status_code == 200

    def test_manager_json(self):
        # manager_all_tickets_json
        response = self.client.post(reverse('uni_ticket:manager_all_tickets_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        assert response.status_code == 200

        # test_manager_unassigned_tickets_json
        response = self.client.post(reverse('uni_ticket:manager_unassigned_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        data = response_json['data']
        assert data

        # test_manager_opened_tickets_json_fails
        response = self.client.post(reverse('uni_ticket:manager_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        data = response_json['data']
        self.assertFalse(data)

        # test_manager_opened_tickets_json
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

        # test_manager_closed_tickets_json
        response = self.client.post(reverse('uni_ticket:manager_closed_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        # data = response_json['data']
        # assert data
        assert response.status_code == 200

        # test_manager_my_opened_ticket_json
        response = self.client.post(reverse('uni_ticket:manager_my_opened_ticket_json',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    {"args": self.post_data})
        response_string = response.content.decode("utf-8")
        response_json = json.loads(response_string)
        # data = response_json['data']
        # assert data
        assert response.status_code == 200

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from uni_ticket.models import *
from api_rest.models import AuthorizationToken

logger = logging.getLogger(__name__)


class uniTicketAPITest(TestCase):
    """
        tests
            openapi-schema
            openapi-schema-json

            api-strutture-list
            api-ticket-category-list

            api-new-ticket
            api-view-ticket
            api-ticket-user-list
            api-ticket-close

    """

    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username = "test"
        )
        self.at = AuthorizationToken.objects.create(
            name = "test AT",
            user = self.user1,
            active_until = timezone.localtime() + timezone.timedelta(hours = 1)
        )

        self.struttura = OrganizationalStructure.objects.create(
            **{
                "id": 10,
                "name": "Structure 1",
                "slug": "structure-1",
                "unique_code": "structure-1",
                "description": "",
                "banner": None,
                "url": None,
                "is_active": True,
                "structure_type": None
            }
        )

        self.category = TicketCategory.objects.create(
            **{
                "id": 3,
                "organizational_structure": self.struttura,
                # helpdesk is the default/automatic one
                # "organizational_office": "office-1",
                "date_start": None,
                "date_end": None,
                "created": "2020-05-08T09:30:02.759000+02:00",
                "modified": "2022-04-11T13:02:23.178085+02:00",
                "name": "Modello di richiesta di test",
                "slug": "modello-di-richiesta-di-test",
                "description": "Descrizione del modulo e delle sue finalità",
                "is_active": True,
                "not_available_message": None,
                "show_heading_text": True,
                "allow_anonymous": False,
                "allow_guest": True,
                "allow_user": True,
                "allow_employee": True,
                "is_notification": False,
                "footer_text": "",
                "receive_email": False,
                "protocol_required": False,
                "user_multiple_open_tickets": True
            }
        )


    def test_strutture_list(self):
        req = Client()
        url = reverse('api-strutture-list')
        
        # no auth
        res = req.get(url)
        self.assertEqual(res.status_code,  401)

        # auth
        res = req.get(url, **self.at.as_http_header)
        self.assertEqual(res.json()['count'],  1)

    def test_category_list(self):
        req = Client()
        url = reverse('api-ticket-category-list')
        
        # no auth
        res = req.get(url)
        self.assertEqual(res.status_code,  401)

        # auth
        res = req.get(url, **self.at.as_http_header)
        self.assertEqual(res.json()['count'],  1)
import logging

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from uni_ticket.models import *
from api_rest.models import AuthorizationToken

logger = logging.getLogger(__name__)


TICKET_FIELDS = [
    {'name': 'Custom field multi-choice', 'field_type': 'MultiCheckBoxField', 'valore': 'value1;value2;value3', 'is_required': True, 'aiuto': 'Help-test field', 'pre_text': '', 'ordinamento': 0},
    {'name': 'data di riferimento', 'field_type': 'BaseDateField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 10},
    {'name': 'URL', 'field_type': 'CustomURLField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 12},
    {'name': 'email', 'field_type': 'CustomEmailField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 20},
    {'name': 'data e ora con inserimento singolo', 'field_type': 'DateStartEndComplexField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 30},
    {'name': 'data e ora con campi separati', 'field_type': 'BaseDateTimeField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 40},
    {'name': 'selezione di una scelta', 'field_type': 'CheckBoxField', 'valore': 'opzione 1;opzione 2;opzione 3', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 50},
    {'name': 'numero con virgola positivo', 'field_type': 'PositiveFloatField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 70},
    {'name': 'numero intero positivo', 'field_type': 'PositiveIntegerField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 75},
    {'name': 'MAC Address', 'field_type': 'CustomMACField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 80},
    {'name': 'indirizzo ip', 'field_type': 'CustomIPField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 81},
    {'name': 'testo ad inserimento libero', 'field_type': 'CustomCharField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 85},
    {'name': 'testo lungo ad inserimento libero', 'field_type': 'TextAreaField', 'valore': '', 'is_required': True, 'aiuto': '', 'pre_text': '', 'ordinamento': 90},
    {'name': 'allegato di test', 'field_type': 'CustomFileField', 'valore': '', 'is_required': False, 'aiuto': 'un allegato di test', 'pre_text': '', 'ordinamento': 100}
]

TEST_STRUTTURA = {
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
            **TEST_STRUTTURA
        )

        office = OrganizationalStructureOffice.objects.create(
            **{
                'name': 'that office',
                'slug': 'that-office',
                'organizational_structure': self.struttura,
                'description': 'that Office',
                'is_default': True,
                'is_private': False,
                'is_active': True
            }
        )

        self.category = TicketCategory.objects.create(
            **{
                "id": 3,
                "organizational_structure": self.struttura,
                # helpdesk is the default/automatic one
                "organizational_office": office,
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
                "user_multiple_open_tickets": True,
                "max_requests_per_user": 0,
            }
        )
        self.modulo = TicketCategoryModule.objects.create(
            **{
                'name': 'Modulo esteso',
                'ticket_category': self.category,
                'is_active': True
            }
        )
        for i in TICKET_FIELDS:
            TicketCategoryInputList.objects.create(
                category_module = self.modulo, **i
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


    def test_new_ticket(self):
        req = Client()
        url = reverse(
            'api-new-ticket',
            kwargs={
                "structure_slug": "structure-1",
                "category_slug": "modello-di-richiesta-di-test"
            }
        )

        # no auth
        res = req.get(url)
        self.assertEqual(res.status_code,  401)

        # auth - GET
        res = req.get(url, **self.at.as_http_header)
        for i in ['name', 'description', 'protocol_required', 'slug', 'messages', 'conditions', 'form']:
            self.assertTrue(i in res.json().keys())

        # auth - POST
        data = {
            "ticket_subject" : "test ticket",
            "ticket_description" : "description",
            "custom_field_multi-choice" : ['value1'],
            "data_di_riferimento" : "2022-12-31",
            "url" : "https://example.it",
            "email" : "that@ema.il",
            "data_e_ora_con_inserimento_singolo_data_inizio_dyn": "2022-12-31",
            "data_e_ora_con_inserimento_singolo_data_fine_dyn": "2022-12-31",
            "data_e_ora_con_campi_separati_data_dyn": "2022-12-31",
            "data_e_ora_con_campi_separati_ore_dyn": "10",
            "data_e_ora_con_campi_separati_minuti_dyn": "10",
            "selezione_di_una_scelta": "opzione 1",
            "numero_con_virgola_positivo": 1.5,
            "numero_intero_positivo": 2,
            "mac_address": "02:42:39:a7:4f:3c",
            "indirizzo_ip": "192.168.6.7",
            "testo_ad_inserimento_libero": "lorem ipsum",
            "testo_lungo_ad_inserimento_libero": "long lorem ipsum"
        }
        res = req.post(
            url,
            data=data,
            content_type="application/json",
            **self.at.as_http_header
        )

        self.assertTrue(
            res.json()['messages'][0].get('SUCCESS', None)
        )

        # get ticket detail
        tcode = res.json()['status']['code']
        durl = reverse("api-view-ticket", kwargs={'ticket_uid': tcode})
        res = req.get(durl, **self.at.as_http_header)
        res_form = res.json()['ticket']['form']
        for i in data.keys():
            if i in ('ticket_subject', 'ticket_description'):
                continue
            self.assertIn(i, res_form)


        # get ticket list
        lurl = reverse("api-ticket-user-list")

        # create another ticket
        req.post(
            url,
            data=data,
            content_type="application/json",
            **self.at.as_http_header
        )

        res = req.get(lurl, **self.at.as_http_header)
        self.assertTrue(
            res.json()['count'] == 2
        )
        self.assertTrue(
            len(res.json()['results']) == 2
        )

        # close ticket
        curl = reverse("api-ticket-close", kwargs={'ticket_id': tcode})
        res = req.post(curl, data={'note': "have to go"}, **self.at.as_http_header)
        self.assertTrue(
            res.json()['messages'][0].get("SUCCESS", None)
        )

from unittest import mock

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from api_rest.models import AuthorizationToken
from api_rest.views import user as api_user
from api_rest.views.generic import message_level
from organizational_area.models import OrganizationalStructure, OrganizationalStructureOffice
from tests.base_ticket_env import BaseTicketEnvironment
from uni_ticket.models import (CompiledTicket,
                               Ticket,
                               TicketCategory,
                               TicketCategoryModule,
                               TicketReply)
from uni_ticket.settings import TICKET_GENERATE_URL_BUTTON_NAME
from uni_ticket.views.user import TicketAddNew, TicketDetail


def _token(user, name, hours=1):
    return AuthorizationToken.objects.create(
        name=name,
        user=user,
        active_until=timezone.localtime() + timezone.timedelta(hours=hours)
    )


class uniTicketAPIModelsTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="token-user")

    def test_token(self):
        token = _token(self.user, "token")
        self.assertEqual(str(token), f"token [{self.user}]")
        self.assertEqual(len(token.value), 128)
        self.assertTrue(token.is_active)
        self.assertEqual(token.as_http_header,
                         {"HTTP_AUTHORIZATION": f"Token {token.value}"})

    def test_expired_token(self):
        token = _token(self.user, "expired", hours=-1)
        self.assertFalse(token.is_active)
        res = Client().get(reverse('api_rest:api-strutture-list'),
                           **token.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_without_expiration(self):
        token = AuthorizationToken(name="no date", user=self.user)
        # comparison with None raises TypeError
        self.assertFalse(token.is_active)

    def test_message_level(self):
        self.assertEqual(message_level(25), 'SUCCESS')
        self.assertEqual(message_level(99), 99)


class uniTicketAPIOperatorTest(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        # user_1 is operator of structure 1 default office
        self.operator_at = _token(self.user_1, "operator AT")
        # user_2 is operator of structure 2 default office
        self.other_at = _token(self.user_2, "other AT")

    def _url(self, name):
        return reverse(f'api_rest:api-operator-tickets-{name}-count',
                       kwargs={'structure_slug': self.structure_1.slug})

    def _count(self, name, token):
        res = Client().get(self._url(name), **token.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.json()['count']

    def test_permissions(self):
        for name in ('unassigned', 'open', 'my-open', 'messages'):
            url = self._url(name)
            self.assertEqual(Client().get(url).status_code,
                             status.HTTP_401_UNAUTHORIZED)
            res = Client().get(url, **self.other_at.as_http_header)
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = Client().get(
            reverse('api_rest:api-operator-tickets-open-count',
                    kwargs={'structure_slug': 'not-existent'}),
            **self.operator_at.as_http_header
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_counters(self):
        self.assertEqual(self._count('unassigned', self.operator_at), 2)
        self.assertEqual(self._count('open', self.operator_at), 0)
        self.assertEqual(self._count('my-open', self.operator_at), 0)
        self.assertEqual(self._count('messages', self.operator_at), 0)

        # a message from ticket owner
        TicketReply.objects.create(ticket=self.ticket,
                                   subject='message',
                                   text='text',
                                   owner=self.ticket.created_by)
        self.assertEqual(self._count('messages', self.operator_at), 1)


class uniTicketAPIUserTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="api-user")
        self.at = _token(self.user, "user AT")
        self.client = Client()
        structure = OrganizationalStructure.objects.create(name="Structure",
                                                           slug="structure",
                                                           unique_code="structure",
                                                           is_active=True)
        office = OrganizationalStructureOffice.objects.create(
            name='office',
            slug='office',
            organizational_structure=structure,
            is_default=True,
            is_active=True
        )
        self.category = TicketCategory.objects.create(
            organizational_structure=structure,
            organizational_office=office,
            name="Category",
            slug="category",
            is_active=True,
            allow_guest=True,
            allow_user=True,
            allow_employee=True,
            user_multiple_open_tickets=True,
        )
        TicketCategoryModule.objects.create(name='module',
                                            ticket_category=self.category,
                                            is_active=True)
        self.url = reverse('api_rest:api-new-ticket',
                           kwargs={"structure_slug": structure.slug,
                                   "category_slug": self.category.slug})
        self.data = {"ticket_subject": "subject",
                     "ticket_description": "description"}

    def _post(self, data):
        return self.client.post(self.url,
                                data=data,
                                content_type="application/json",
                                **self.at.as_http_header)

    def _create_ticket(self):
        res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.json()['status']['code']

    def test_new_ticket_get_unpublished_category(self):
        self.category.is_active = False
        self.category.save()
        res = self.client.get(self.url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_new_ticket_user_not_allowed(self):
        self.category.allow_guest = False
        self.category.allow_user = False
        self.category.allow_employee = False
        self.category.save()
        res = self.client.get(self.url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(res.json()['detail'])
        res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(res.json()['detail'])
        self.assertFalse(Ticket.objects.exists())

    def test_new_ticket_existent_open_ticket(self):
        self._create_ticket()
        self.category.user_multiple_open_tickets = False
        self.category.save()
        res = self.client.get(self.url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('richieste aperte', res.json()['detail'])
        res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('richieste aperte', res.json()['detail'])
        self.assertEqual(Ticket.objects.count(), 1)

    def test_new_ticket_post_not_in_allowed_users(self):
        other_user = get_user_model().objects.create(username="other-user")
        self.category.allowed_users.add(other_user)
        res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(res.json()['detail'])
        self.assertFalse(Ticket.objects.exists())

    def test_new_ticket_post_daily_limit_reached(self):
        with mock.patch.object(Ticket, 'number_limit_reached_by_user',
                               return_value=True):
            res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.json()['redirect_url'], reverse('uni_ticket:user_dashboard'))
        self.assertFalse(Ticket.objects.exists())

    def test_new_ticket_import_errors(self):
        # expired compiled ticket
        res = self.client.get(f'{self.url}?import=not-existent',
                              **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('scaduto', res.json()['detail'])
        # not decryptable content
        CompiledTicket.objects.create(url_path='invalid', content='garbage')
        res = self.client.get(f'{self.url}?import=invalid',
                              **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non consistenti', res.json()['detail'])

    def test_new_ticket_get_daily_limit_reached(self):
        with mock.patch.object(Ticket, 'number_limit_reached_by_user',
                               return_value=True):
            res = self.client.get(self.url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        detail = res.json()
        self.assertEqual(detail['redirect_url'], reverse('uni_ticket:user_dashboard'))
        self.assertTrue(detail['messages'][0].get('ERROR'))

    def test_new_ticket_form_errors(self):
        res = self._post({"ticket_subject": ""})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn('status', res.json())
        self.assertFalse(Ticket.objects.exists())

    def test_new_ticket_generate_url(self):
        # a valid form that doesn't create a ticket
        data = dict(self.data, **{TICKET_GENERATE_URL_BUTTON_NAME: 1})
        res = self._post(data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Ticket.objects.exists())

    def test_new_ticket_anonymous_creator(self):
        original_post = TicketAddNew.post

        def post_without_creator(view, *args, **kwargs):
            response = original_post(view, *args, **kwargs)
            view.ticket.created_by = None
            return response

        with mock.patch.object(TicketAddNew, 'post', post_without_creator):
            res = self._post(self.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['status']['created_by'], 'Utente anonimo')

    def test_ticket_detail_not_found(self):
        url = reverse("api_rest:api-view-ticket", kwargs={'ticket_uid': 'not-existent'})
        res = self.client.get(url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_ticket_detail_legacy_responses(self):
        # NOTE: TicketDetail.get(api=True) returns a dict or raises Http404:
        # the HttpResponse branches of TicketAPIDetail are defensive code
        url = reverse("api_rest:api-view-ticket", kwargs={'ticket_uid': 'code'})
        expected = ((404, status.HTTP_404_NOT_FOUND),
                    (403, status.HTTP_403_FORBIDDEN),
                    (200, status.HTTP_400_BAD_REQUEST))
        for legacy_status, api_status in expected:
            with mock.patch.object(TicketDetail, 'get',
                                   return_value=HttpResponse(status=legacy_status)):
                res = self.client.get(url, **self.at.as_http_header)
            self.assertEqual(res.status_code, api_status)

    def test_ticket_list_without_pagination(self):
        code = self._create_ticket()
        with mock.patch.object(api_user.TicketAPIListCreated, 'pagination_class', None):
            res = self.client.get(reverse("api_rest:api-ticket-user-list"),
                                  **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([t['code'] for t in res.json()], [code])

    def test_ticket_list_anonymous(self):
        # permission classes block anonymous users before list() is called
        res = self.client.get(reverse("api_rest:api-ticket-user-list"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        # list() also checks authentication by itself
        request = APIRequestFactory().get('/')
        request.user = mock.Mock(is_authenticated=False)
        with self.assertRaises(PermissionDenied):
            api_user.TicketAPIListCreated().list(request)

    def test_close_ticket_get(self):
        code = self._create_ticket()
        url = reverse("api_rest:api-ticket-close", kwargs={'ticket_id': code})
        res = self.client.get(url, **self.at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['ticket']['code'], code)
        self.assertIn('form', res.json())
        # GET doesn't send a closing reason: ticket is still open
        self.assertFalse(Ticket.objects.get(code=code).is_closed)

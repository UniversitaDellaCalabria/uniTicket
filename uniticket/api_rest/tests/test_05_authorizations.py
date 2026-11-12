import logging

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from api_rest.authorizations import AuthorizationToken as TokenAuthentication
from api_rest.models import AuthorizationToken


logger = logging.getLogger('my_logger')


class uniTicketAPIAuthorizationTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='api-user',
                                                         password='passw',
                                                         email='api-user@test.it')
        self.token = AuthorizationToken.objects.create(
            name='auth test',
            user=self.user,
            active_until=timezone.localtime() + timezone.timedelta(hours=1)
        )
        self.url = reverse('api_rest:api-strutture-list')
        self.auth = TokenAuthentication()

    def _assert_rejected(self, header, message, client=None):
        client = client or Client()
        with self.assertLogs('api_rest.authorizations', level='WARNING') as logs:
            res = client.get(self.url, **header)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res.json()['detail'], message)
        self.assertTrue(any(message in line for line in logs.output))

    def test_valid_token(self):
        self.assertEqual(self.auth.authenticate_credentials(self.token.value),
                         (self.user, self.token))
        res = Client().get(self.url, **self.token.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_invalid_token(self):
        self._assert_rejected({'HTTP_AUTHORIZATION': 'Token not-existent'},
                              'Invalid token.')

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate_credentials(self.token.value)
        self._assert_rejected(self.token.as_http_header,
                              'User inactive or deleted.')

    def test_expired_token(self):
        self.token.active_until = timezone.localtime() - timezone.timedelta(hours=1)
        self.token.save()
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate_credentials(self.token.value)
        self._assert_rejected(self.token.as_http_header, 'Token expired.')

    def test_expired_token_with_valid_session(self):
        # an invalid token must not fall back to session authentication
        self.token.active_until = timezone.localtime() - timezone.timedelta(hours=1)
        self.token.save()
        client = Client()
        client.force_login(self.user)
        self.assertEqual(client.get(self.url).status_code, status.HTTP_200_OK)
        self._assert_rejected(self.token.as_http_header, 'Token expired.',
                              client=client)

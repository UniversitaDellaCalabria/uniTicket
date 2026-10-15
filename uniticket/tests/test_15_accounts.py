import logging

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.middlewares import AccountsChangeDataMiddleware
from organizational_area.models import get_user_model


logger = logging.getLogger('my_logger')


class Test_AccountsChangeDataMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AccountsChangeDataMiddleware(
            lambda request: HttpResponse("ok")
        )
        self.user = get_user_model().objects.create_user(
            username='user-with-email',
            password='passw',
            email='user@test.it'
        )
        self.user_no_email = get_user_model().objects.create_user(
            username='user-without-email',
            password='passw',
            email=''
        )

    def _request(self, path, user):
        request = self.factory.get(path)
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_anonymous_user_passes(self):
        request = self._request(reverse('uni_ticket:user_dashboard'),
                                AnonymousUser())
        response = self.middleware(request)
        self.assertEqual(response.content, b"ok")

    def test_complete_profile_passes(self):
        request = self._request(reverse('uni_ticket:user_dashboard'),
                                self.user)
        response = self.middleware(request)
        self.assertEqual(response.content, b"ok")

    def test_incomplete_profile_is_redirected(self):
        request = self._request(reverse('uni_ticket:user_dashboard'),
                                self.user_no_email)
        response = self.middleware(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:change_data'))
        self.assertEqual(len(list(get_messages(request))), 1)

    def test_incomplete_profile_on_safe_app_passes(self):
        # accounts app is in SAFE_URL_APPS
        request = self._request(reverse('accounts:change_data'),
                                self.user_no_email)
        response = self.middleware(request)
        self.assertEqual(response.content, b"ok")

import importlib
import logging

from unittest import mock

from django.contrib.auth.models import Group
from django.core import mail
from django.forms import modelform_factory
from django.template import Context, Template
from django.test import TestCase
from django.urls import clear_url_caches, reverse
from django.utils import timezone

from accounts import urls as accounts_urls
from accounts.forms import UserDataForm
from accounts.settings import CHANGE_EMAIL_TOKEN_LIFE
from accounts.templatetags.accounts_tags import accounts_settings_value
from accounts.templatetags.has_group import has_group
from organizational_area.models import get_user_model
from uni_ticket.jwts import encrypt_to_jwe


logger = logging.getLogger('my_logger')


class AccountsMixin:

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='account-user',
                                                         password='passw',
                                                         first_name='Name',
                                                         last_name='Surname',
                                                         email='old@test.it')
        self.client.force_login(self.user)
        self.change_url = reverse('accounts:change_data')
        self.confirm_url = reverse('accounts:confirm_email')

    def _messages(self, response):
        return [str(m) for m in response.context['messages']]

    def _token(self, user_id=None, email='new@test.it', date=None):
        date = date or timezone.now()
        return encrypt_to_jwe(f'{user_id or self.user.pk}|{email}|{date}')


class Test_AccountsChangeData(AccountsMixin, TestCase):

    def test_get_form(self):
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'change_user_data.html')
        form = response.context['form']
        self.assertEqual(form.initial['email'], 'old@test.it')
        self.assertTrue(form.fields['email'].required)

    def test_invalid_data(self):
        response = self.client.post(self.change_url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dati errati', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@test.it')

    def test_same_email(self):
        response = self.client.post(self.change_url, {'email': 'old@test.it'},
                                    follow=True)
        self.assertRedirects(response, self.change_url)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(self._messages(response))

    def test_new_email_sends_confirmation(self):
        response = self.client.post(self.change_url, {'email': 'new@test.it'},
                                    follow=True)
        self.assertRedirects(response, self.change_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['new@test.it'])
        self.assertIn(self.confirm_url + '?token=', mail.outbox[0].body)
        self.assertTrue(any('inviata un' in m for m in self._messages(response)))
        # email is changed only after confirmation
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@test.it')
        self.assertIsNone(self.user.manual_user_update)

    def test_other_editable_fields(self):
        form_class = modelform_factory(get_user_model(),
                                       form=UserDataForm,
                                       fields=['email', 'first_name', 'last_name'])
        with mock.patch('accounts.views.UserDataForm', form_class):
            response = self.client.post(self.change_url,
                                        {'email': 'old@test.it',
                                         'first_name': 'New name',
                                         'last_name': 'New surname'},
                                        follow=True)
        self.assertIn('Dati salvati con successo', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New name')
        self.assertEqual(self.user.last_name, 'New surname')
        self.assertEqual(self.user.email, 'old@test.it')
        self.assertTrue(self.user.manual_user_update)

    def test_one_other_editable_field(self):
        form_class = modelform_factory(get_user_model(),
                                       form=UserDataForm,
                                       fields=['email', 'taxpayer_id'])
        with mock.patch('accounts.views.UserDataForm', form_class):
            response = self.client.post(self.change_url,
                                        {'email': 'old@test.it',
                                         'taxpayer_id': 'TAXPAYER01'},
                                        follow=True)
        self.assertIn('Dati salvati con successo', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.taxpayer_id, 'TAXPAYER01')
        self.assertEqual(self.user.email, 'old@test.it')
        self.assertTrue(self.user.manual_user_update)

    def test_form_save_keeps_initial_email(self):
        form = UserDataForm({'email': 'new@test.it'}, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        self.assertEqual(user.email, 'old@test.it')
        user = form.save()
        user.refresh_from_db()
        self.assertEqual(user.email, 'old@test.it')


class Test_AccountsConfirmEmail(AccountsMixin, TestCase):

    def test_missing_token(self):
        response = self.client.get(self.confirm_url, follow=True)
        self.assertRedirects(response, self.change_url)
        self.assertIn('Token mancante', self._messages(response))

    def test_invalid_token(self):
        response = self.client.get(self.confirm_url, {'token': 'invalid'}, follow=True)
        self.assertRedirects(response, self.change_url)
        self.assertIn('Token non valido', self._messages(response))

    def _assert_invalid_token(self, token):
        response = self.client.get(self.confirm_url, {'token': token}, follow=True)
        self.assertRedirects(response, self.change_url)
        self.assertIn('Token non valido', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@test.it')

    def test_malformed_token_payload(self):
        # valid JWE without "|" separators
        self._assert_invalid_token(encrypt_to_jwe('malformed'))

    def test_unparsable_token_date(self):
        self._assert_invalid_token(
            encrypt_to_jwe(f'{self.user.pk}|new@test.it|not-a-date')
        )

    def test_confirm_email(self):
        response = self.client.get(self.confirm_url, {'token': self._token()})
        self.assertRedirects(response, reverse('uni_ticket:user_settings'),
                             fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@test.it')
        self.assertTrue(self.user.manual_user_update)

    def test_expired_token(self):
        date = timezone.now() - timezone.timedelta(minutes=CHANGE_EMAIL_TOKEN_LIFE + 1)
        response = self.client.get(self.confirm_url, {'token': self._token(date=date)},
                                   follow=True)
        self.assertIn('Token scaduto', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@test.it')

    def test_token_older_than_last_update(self):
        token = self._token(date=timezone.now() - timezone.timedelta(minutes=1))
        self.user.manual_user_update = timezone.now()
        self.user.save()
        response = self.client.get(self.confirm_url, {'token': token}, follow=True)
        self.assertIn('Token scaduto', self._messages(response))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@test.it')

    def test_not_existent_user(self):
        self._assert_invalid_token(self._token(user_id=999999))

    def test_token_of_another_user(self):
        other = get_user_model().objects.create_user(username='other-user',
                                                     password='passw',
                                                     email='other@test.it')
        self._assert_invalid_token(self._token(user_id=other.pk))
        other.refresh_from_db()
        self.assertEqual(other.email, 'other@test.it')

    def test_invalid_token_date(self):
        # well formatted but not existent date: parse_datetime raises ValueError
        self._assert_invalid_token(
            encrypt_to_jwe(f'{self.user.pk}|new@test.it|2026-13-45 10:00:00+00:00')
        )

    def test_token_with_extra_fields(self):
        self._assert_invalid_token(
            encrypt_to_jwe(f'{self.user.pk}|new@test.it|{timezone.now()}|extra')
        )


class Test_AccountsTemplatetags(TestCase):

    def test_accounts_settings_value(self):
        self.assertEqual(accounts_settings_value('CHANGE_EMAIL_TOKEN_LIFE'),
                         CHANGE_EMAIL_TOKEN_LIFE)
        self.assertIsNone(accounts_settings_value('NOT_EXISTENT'))
        with mock.patch('accounts.settings.SAFE_URL_PATHS', 'path/{slug}', create=True):
            self.assertEqual(accounts_settings_value('SAFE_URL_PATHS', slug='x'), 'path/x')
        rendered = Template(
            '{% load accounts_tags %}{% accounts_settings_value "CHANGE_EMAIL_TOKEN_LIFE" %}'
        ).render(Context())
        self.assertEqual(rendered, str(CHANGE_EMAIL_TOKEN_LIFE))

    def test_has_group(self):
        user = get_user_model().objects.create_user(username='group-user', password='p')
        group = Group.objects.create(name='editors')
        Group.objects.create(name='others')
        user.groups.add(group)
        self.assertTrue(has_group(user, 'editors'))
        self.assertFalse(has_group(user, 'others'))
        self.assertFalse(has_group(user, 'not-existent'))
        self.assertFalse(has_group(user, ''))
        self.assertFalse(has_group(None, 'editors'))


class Test_AccountsUrls(TestCase):

    def test_no_editable_fields(self):
        try:
            with mock.patch('accounts.settings.EDITABLE_FIELDS', []):
                importlib.reload(accounts_urls)
                self.assertEqual(accounts_urls.urlpatterns, [])
        finally:
            importlib.reload(accounts_urls)
            clear_url_caches()
        self.assertEqual([p.name for p in accounts_urls.urlpatterns],
                         ['change_data', 'confirm_email'])

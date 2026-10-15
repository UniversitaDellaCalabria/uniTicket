import logging

from unittest import mock

import requests

from django.contrib.admin.models import CHANGE
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from app_io import utils as app_io_utils
from app_io.forms import IOServiceTicketCategoryForm
from app_io.models import IOLog, IOService, IOServiceTicketCategory
from uni_ticket.models import Log, Ticket

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


def _http_response(status_code, data):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = data
    return response


class Test_AppIOUtils(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.ticket.created_by.taxpayer_id = 'RSSMRA80A01H501U'
        self.ticket.created_by.save()
        self.service = IOService.objects.create(name='Service',
                                                service_id='srv-1',
                                                api_key='key-1')
        self.io_service = IOServiceTicketCategory.objects.create(
            service=self.service,
            category=self.category_1_str_1,
            is_active=True
        )
        self.log = Log.objects.log_action(
            user_id=self.staff_1.pk,
            content_type_id=ContentType.objects.get_for_model(Ticket).pk,
            object_id=self.ticket.pk,
            object_repr=str(self.ticket),
            action_flag=CHANGE,
            change_message='closed',
        )

    def test_service_str(self):
        self.assertEqual(str(self.service), 'Service (srv-1)')

    @mock.patch('app_io.utils.requests.request')
    def test_call_io_api(self, request):
        request.return_value = _http_response(200, {'ok': True})
        result = app_io_utils._callIOApi(method='post',
                                         endpoint='profiles',
                                         key='key',
                                         data={'a': 1})
        self.assertEqual(result, {'data': {'ok': True}, 'status': 200})
        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs['url'],
                         f'{app_io_utils.APP_IO_API_BASE_URL}/profiles')
        self.assertEqual(kwargs['headers'],
                         {app_io_utils.APP_IO_API_HEADER_KEY: 'key'})
        self.assertEqual(kwargs['data'], '{"a": 1}')

    @mock.patch('app_io.utils.requests.request',
                side_effect=requests.exceptions.Timeout)
    def test_call_io_api_timeout(self, request):
        result = app_io_utils._callIOApi()
        self.assertEqual(result, {'data': {}, 'status': 503})

    @mock.patch('app_io.utils._callIOApi')
    def test_check_user_profile(self, call):
        call.return_value = {'status': 200, 'data': {'sender_allowed': True}}
        self.assertEqual(app_io_utils.check_user_profile('CF', 'srv', 'key'),
                         (True, None))

        call.return_value = {'status': 200, 'data': {'sender_allowed': False}}
        self.assertEqual(app_io_utils.check_user_profile('CF', 'srv', 'key'),
                         (False, 'Sender not allowed by user'))

        call.return_value = {'status': 404, 'data': {'detail': 'Not found'}}
        self.assertEqual(app_io_utils.check_user_profile('CF', 'srv', 'key'),
                         (False, 'Not found'))

        call.return_value = {'status': 503, 'data': {}}
        self.assertEqual(app_io_utils.check_user_profile('CF', 'srv', 'key'),
                         (False, 503))

    def test_send_message_without_service(self):
        self.io_service.is_active = False
        self.io_service.save()
        self.assertFalse(app_io_utils.send_message(self.ticket, 'subject', 'body'))

    @mock.patch('app_io.utils._callIOApi')
    def test_send_message_success(self, call):
        call.side_effect = [
            {'status': 200, 'data': {'sender_allowed': True}},
            {'status': 201, 'data': {'id': 'msg-1'}},
        ]
        result = app_io_utils.send_message(self.ticket, 'subject', 'body',
                                           log=self.log)
        self.assertEqual(result, {'message_id': 'msg-1', 'error': None})
        message_data = call.call_args.kwargs['data']
        self.assertEqual(message_data['fiscal_code'], 'RSSMRA80A01H501U')
        self.assertEqual(message_data['content'],
                         {'subject': 'subject', 'markdown': 'body'})
        self.assertEqual(IOLog.objects.get(log=self.log).response, result)

    @mock.patch('app_io.utils._callIOApi')
    def test_send_message_api_error(self, call):
        call.side_effect = [
            {'status': 200, 'data': {'sender_allowed': True}},
            {'status': 400, 'data': {'detail': 'Bad request'}},
        ]
        result = app_io_utils.send_message(self.ticket, 'subject', 'body')
        self.assertEqual(result, {'message_id': None, 'error': 'Bad request'})
        self.assertFalse(IOLog.objects.exists())

    @mock.patch('app_io.utils._callIOApi')
    def test_send_message_api_error_without_detail(self, call):
        call.side_effect = [
            {'status': 200, 'data': {'sender_allowed': True}},
            {'status': 500, 'data': {}},
        ]
        # error_detail falls back to the (int) status code
        result = app_io_utils.send_message(self.ticket, 'subject', 'body')
        self.assertEqual(result, {'message_id': None, 'error': 500})

    @mock.patch('app_io.utils._callIOApi')
    def test_send_message_profile_error(self, call):
        call.return_value = {'status': 200, 'data': {'sender_allowed': False}}
        result = app_io_utils.send_message(self.ticket, 'subject', 'body',
                                           log=self.log)
        self.assertEqual(result, {'message_id': None,
                                  'error': 'Sender not allowed by user'})
        # only profile API has been called
        call.assert_called_once()
        self.assertEqual(IOLog.objects.get(log=self.log).response, result)


class Test_AppIOViews(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        self.structure_1_manager_login()
        self.service_1 = IOService.objects.create(name='Service 1',
                                                  service_id='srv-1',
                                                  api_key='key-1')
        self.service_2 = IOService.objects.create(name='Service 2',
                                                  service_id='srv-2',
                                                  api_key='key-2')

    def _url(self, name, **kwargs):
        kwargs.update({'structure_slug': self.structure_1.slug,
                       'category_slug': self.category_1_str_1.slug})
        return reverse(f'app_io:{name}', kwargs=kwargs)

    def _service_url(self, name, service):
        return self._url(name, service_id=service.pk)

    def _add_service(self, service, is_active=False):
        return IOServiceTicketCategory.objects.create(service=service,
                                                      category=self.category_1_str_1,
                                                      is_active=is_active)

    def test_app_io_disabled(self):
        self.structure_1.app_io_enabled = False
        self.structure_1.save()
        cat_service = self._add_service(self.service_1)
        self.assertEqual(self.client.get(self._url('app_io_services_new')).status_code, 403)
        response = self.client.get(self._service_url('app_io_services_edit', cat_service))
        self.assertEqual(response.status_code, 403)
        for name in ('app_io_services_enable',
                     'app_io_services_disable',
                     'app_io_services_delete'):
            response = self.client.post(self._service_url(name, cat_service))
            self.assertEqual(response.status_code, 403)
        self.assertTrue(IOServiceTicketCategory.objects.filter(pk=cat_service.pk).exists())

    def test_not_manager(self):
        self.structure_1_default_office_operator_login()
        response = self.client.get(self._url('app_io_services_new'), follow=True)
        self.assertFalse(response.context.get('form'))

    def test_new_service(self):
        response = self.client.get(self._url('app_io_services_new'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category_1_str_1)

        response = self.client.post(self._url('app_io_services_new'),
                                    {'service': self.service_1.pk, 'note': 'note'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service = IOServiceTicketCategory.objects.get(category=self.category_1_str_1)
        self.assertEqual(cat_service.service, self.service_1)
        self.assertEqual(cat_service.note, 'note')
        self.assertFalse(cat_service.is_active)

        # an already assigned service is excluded from choices
        response = self.client.get(self._url('app_io_services_new'))
        queryset = response.context['form'].fields['service'].queryset
        self.assertNotIn(self.service_1, queryset)
        self.assertIn(self.service_2, queryset)

    def test_edit_service(self):
        cat_service = self._add_service(self.service_1)
        self._add_service(self.service_2)
        url = self._service_url('app_io_services_edit', cat_service)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        queryset = response.context['form'].fields['service'].queryset
        # current service is still selectable, other assigned ones are not
        self.assertIn(self.service_1, queryset)
        self.assertNotIn(self.service_2, queryset)

        response = self.client.post(url,
                                    {'service': self.service_1.pk, 'note': 'edited'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service.refresh_from_db()
        self.assertEqual(cat_service.note, 'edited')

    def test_enable_disable_service(self):
        cat_service_1 = self._add_service(self.service_1, is_active=True)
        cat_service_2 = self._add_service(self.service_2)

        # enable service 2: service 1 is disabled
        response = self.client.post(self._service_url('app_io_services_enable', cat_service_2),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service_1.refresh_from_db()
        cat_service_2.refresh_from_db()
        self.assertTrue(cat_service_2.is_active)
        self.assertFalse(cat_service_1.is_active)

        # enable an already active service
        response = self.client.post(self._service_url('app_io_services_enable', cat_service_2),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service_2.refresh_from_db()
        self.assertTrue(cat_service_2.is_active)

        # disable
        response = self.client.post(self._service_url('app_io_services_disable', cat_service_2),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service_2.refresh_from_db()
        self.assertFalse(cat_service_2.is_active)

        # disable an already disabled service
        response = self.client.post(self._service_url('app_io_services_disable', cat_service_2),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        cat_service_2.refresh_from_db()
        self.assertFalse(cat_service_2.is_active)

    def test_delete_service(self):
        cat_service = self._add_service(self.service_1)
        response = self.client.post(self._service_url('app_io_services_delete', cat_service),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(IOServiceTicketCategory.objects.filter(pk=cat_service.pk).exists())
        # service is not deleted
        self.assertTrue(IOService.objects.filter(pk=self.service_1.pk).exists())

    def test_category_detail_renders_post_forms(self):
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        active = self._add_service(self.service_1, is_active=True)
        inactive = self._add_service(self.service_2)
        response = self.client.get(reverse('uni_ticket:manager_category_detail',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manager/category_app_io_services.html')
        content = response.content.decode()
        for name, service in (('app_io_services_enable', inactive),
                              ('app_io_services_disable', active),
                              ('app_io_services_delete', active)):
            action = 'method="post" action="{}"'.format(self._service_url(name, service))
            self.assertIn(action, content)

    def test_state_changes_require_post(self):
        cat_service = self._add_service(self.service_1)
        for name in ('app_io_services_enable',
                     'app_io_services_disable',
                     'app_io_services_delete'):
            response = self.client.get(self._service_url(name, cat_service))
            self.assertEqual(response.status_code, 405)
        cat_service.refresh_from_db()
        self.assertFalse(cat_service.is_active)

    def test_state_changes_require_csrf_token(self):
        cat_service = self._add_service(self.service_1)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff_1)
        for name in ('app_io_services_enable', 'app_io_services_delete'):
            response = csrf_client.post(self._service_url(name, cat_service))
            self.assertEqual(response.status_code, 403)
        cat_service.refresh_from_db()
        self.assertFalse(cat_service.is_active)

    def test_service_of_other_category(self):
        other = IOServiceTicketCategory.objects.create(service=self.service_1,
                                                       category=self.category_1_str_2)
        response = self.client.get(self._service_url('app_io_services_edit', other))
        self.assertEqual(response.status_code, 404)

    def test_form_requires_category(self):
        with self.assertRaises(KeyError):
            IOServiceTicketCategoryForm()

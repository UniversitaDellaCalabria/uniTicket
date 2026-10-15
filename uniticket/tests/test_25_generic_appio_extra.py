import logging

from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from app_io.models import IOService, IOServiceTicketCategory
from uni_ticket.models import TicketReply
from uni_ticket.views.generic import user_settings

from . base_ticket_env import BaseTicketEnvironment
from . test_14_generic_decorators import TempMediaRootMixin


logger = logging.getLogger('my_logger')


class Test_GenericExtraViews(TempMediaRootMixin, BaseTicketEnvironment):

    def _reply(self, attachment=None):
        return TicketReply.objects.create(ticket=self.ticket,
                                          owner=self.user_1,
                                          structure=self.structure_1,
                                          subject='Reply',
                                          text='Reply',
                                          attachment=attachment)

    def _download_url(self, reply):
        return reverse('uni_ticket:download_message_attachment',
                       kwargs={'ticket_id': self.ticket.code,
                               'reply_id': reply.pk})

    def test_download_message_attachment(self):
        reply = self._reply(SimpleUploadedFile('reply.pdf', b'reply_file',
                                               content_type='application/pdf'))
        response = self.client.get(self._download_url(reply))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'reply_file')
        self.assertIn('reply.pdf', response['Content-Disposition'])

    def test_download_message_without_attachment(self):
        response = self.client.get(self._download_url(self._reply()))
        self.assertEqual(response.status_code, 404)

    def test_download_message_not_existent(self):
        response = self.client.get(reverse('uni_ticket:download_message_attachment',
                                           kwargs={'ticket_id': self.ticket.code,
                                                   'reply_id': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_user_settings(self):
        response = self.client.get(reverse('uni_ticket:user_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/user_settings.html')
        self.assertIsNone(response.context['structure'])

    @mock.patch('uni_ticket.views.generic.render', return_value=HttpResponse('ok'))
    def test_user_settings_template_by_user_type(self, mock_render):
        for user, expected in ((self.staff_1, 'manager'),
                               (self.user_1, 'operator'),
                               (self.user_2, 'user')):
            request = RequestFactory().get('/')
            request.user = user
            request.structure = self.structure_1
            user_settings(request)
            _, template, context = mock_render.call_args.args
            self.assertEqual(template, '{}/user_settings.html'.format(expected))
            self.assertEqual(context['structure'], self.structure_1)


class Test_AppIOViewsInvalidForms(BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1.app_io_enabled = True
        self.structure_1.save()
        self.structure_1_manager_login()
        self.service = IOService.objects.create(name='Service',
                                                service_id='srv-1',
                                                api_key='key-1')

    def _url(self, name, **kwargs):
        kwargs.update({'structure_slug': self.structure_1.slug,
                       'category_slug': self.category_1_str_1.slug})
        return reverse(f'app_io:{name}', kwargs=kwargs)

    def _error_messages(self, response):
        return [str(m) for m in response.context['messages']
                if m.level_tag == 'error']

    def test_new_service_invalid_form(self):
        response = self.client.post(self._url('app_io_services_new'),
                                    {'service': '', 'note': 'note'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertTrue(self._error_messages(response))
        self.assertFalse(IOServiceTicketCategory.objects.exists())

    def test_edit_service_invalid_form(self):
        cat_service = IOServiceTicketCategory.objects.create(service=self.service,
                                                             category=self.category_1_str_1,
                                                             note='original')
        response = self.client.post(self._url('app_io_services_edit',
                                              service_id=cat_service.pk),
                                    {'service': 999999, 'note': 'edited'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('service', response.context['form'].errors)
        self.assertTrue(self._error_messages(response))
        cat_service.refresh_from_db()
        self.assertEqual(cat_service.note, 'original')

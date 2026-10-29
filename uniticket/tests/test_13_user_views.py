import base64
import json
import logging
import os
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core import mail
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from django_form_builder.enc import encrypt
from django_form_builder.utils import set_as_dict
from uni_ticket.jwts import encrypt_to_jwe
from uni_ticket.models import (CompiledTicket,
                               Task,
                               Ticket,
                               TicketAssignment,
                               TicketCategoryCondition,
                               TicketCategoryInputList,
                               TicketCategoryTask,
                               TicketReply)
from uni_ticket.settings import (TICKET_COMPILED_BY_USER_NAME,
                                 TICKET_CONDITIONS_FIELD_ID,
                                 TICKET_CREATE_BUTTON_NAME,
                                 TICKET_DRAFT_BUTTON_NAME,
                                 TICKET_GENERATE_URL_BUTTON_NAME,
                                 TICKET_SHARE_DRAFT_BUTTON_NAME,
                                 TICKET_SUBMIT_DRAFT_BUTTON_NAME)
from uni_ticket.forms import BaseTicketCloseForm
from uni_ticket.utils import get_path
from uni_ticket.views.user import (TicketAddNew,
                                  TicketClose,
                                  TicketDetail,
                                  chat_new_preload)

from . base_ticket_env import BaseTicketEnvironment
from . test_14_generic_decorators import TempMediaRootMixin


logger = logging.getLogger('my_logger')

# protocolled tickets require a minimum subject length
PROTOCOL_SUBJECT = 'Ticket subject long enough to be protocolled'


class UserViewsMixin:

    def _new_ticket_url(self, category=None):
        category = category or self.category_1_str_1
        return reverse('uni_ticket:add_new_ticket',
                       kwargs={'structure_slug': category.organizational_structure.slug,
                               'category_slug': category.slug})

    def _post_new_ticket(self, subject='New ticket', button=TICKET_CREATE_BUTTON_NAME,
                         extra=None, category=None, url_suffix='', follow=False):
        params = {'ticket_subject': subject,
                  'ticket_description': subject,
                  button: 'ok'}
        if extra:
            params.update(extra)
        return self.client.post(self._new_ticket_url(category) + url_suffix,
                                params,
                                follow=follow)

    def _create_draft(self, subject='Draft ticket'):
        self._post_new_ticket(subject=subject, button=TICKET_DRAFT_BUTTON_NAME)
        draft = Ticket.objects.get(subject=subject)
        self.assertTrue(draft.draft)
        return draft

    def _update_category(self, **fields):
        for k, v in fields.items():
            setattr(self.category_1_str_1, k, v)
        self.category_1_str_1.save()

    def _add_second_file_field(self):
        TicketCategoryInputList.objects.create(
            category_module=self.module_2,
            name='file_field_2',
            field_type='CustomFileField',
            is_required=False,
        )

    def _attachment_exists(self, ticket, file_name):
        return os.path.exists(os.path.join(get_path(ticket.get_folder()),
                                           file_name))

    def _assert_custom_message(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertTemplateUsed(response, 'custom_message.html')


class Test_UserNewTicket(UserViewsMixin, TempMediaRootMixin, BaseTicketEnvironment):

    def test_preload_daily_limit_reached(self):
        with override_settings(MAX_DAILY_TICKET_PER_USER=2):
            response = self.client.get(reverse('uni_ticket:new_ticket_preload'))
        self.assertRedirects(response, reverse('uni_ticket:user_dashboard'))

    def test_preload_excludes_unpublished_categories(self):
        self._update_category(date_end=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse('uni_ticket:new_ticket_preload',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.category_1_str_1, response.context['categorie'])

    def test_preload_user_roles(self):
        url = reverse('uni_ticket:new_ticket_preload',
                      kwargs={'structure_slug': self.structure_1.slug})
        # employee only
        self._update_category(allow_guest=False, allow_user=False, allow_employee=True)
        self.staff_1.identificativo_dipendente = '1234'
        self.staff_1.save()
        response = self.client.get(url)
        self.assertIn(self.category_1_str_1, response.context['categorie'])
        # employee and internal user
        self.staff_1.identificativo_utente = 'abcd'
        self.staff_1.save()
        response = self.client.get(url)
        self.assertIn(self.category_1_str_1, response.context['categorie'])
        # internal user only
        self._update_category(allow_user=True, allow_employee=False)
        self.staff_1.identificativo_dipendente = None
        self.staff_1.save()
        response = self.client.get(url)
        self.assertIn(self.category_1_str_1, response.context['categorie'])
        # employee category is hidden to internal users
        self._update_category(allow_user=False, allow_employee=True)
        response = self.client.get(url)
        self.assertNotIn(self.category_1_str_1, response.context['categorie'])

    def test_unpublished_category(self):
        self._update_category(date_end=timezone.now() - timedelta(days=1))
        response = self.client.get(self._new_ticket_url())
        self._assert_custom_message(response, 404)
        response = self._post_new_ticket()
        self._assert_custom_message(response, 404)

    def test_anonymous_user_not_allowed(self):
        self.client.logout()
        response = self.client.get(self._new_ticket_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_daily_limit_reached(self):
        with override_settings(MAX_DAILY_TICKET_PER_USER=2):
            response = self.client.get(self._new_ticket_url())
        self.assertRedirects(response, reverse('uni_ticket:user_dashboard'))

    def test_user_type_not_allowed(self):
        self._update_category(allow_guest=False, allow_user=False, allow_employee=False)
        response = self.client.get(self._new_ticket_url())
        self._assert_custom_message(response, 403)
        self.assertNotIn('form', response.context)

    def test_max_requests_per_user(self):
        self._update_category(max_requests_per_user=1)
        response = self._post_new_ticket(subject='Over the limit')
        self._assert_custom_message(response, 403)
        self.assertFalse(Ticket.objects.filter(subject='Over the limit').exists())

    def test_user_not_in_allowed_users(self):
        self.category_1_str_1.allowed_users.add(self.user_2)
        response = self._post_new_ticket(subject='Not allowed')
        self._assert_custom_message(response, 403)
        self.assertFalse(Ticket.objects.filter(subject='Not allowed').exists())

    def test_import_anonymous(self):
        self._update_category(allow_anonymous=True)
        self.client.logout()
        response = self.client.get(self._new_ticket_url() + '?import=something')
        self._assert_custom_message(response, 403)

    def test_import_expired_ticket(self):
        response = self.client.get(self._new_ticket_url() + '?import=not-existent')
        self._assert_custom_message(response, 404)
        self.assertIn('scaduto', response.context['avviso'])
        response = self._post_new_ticket(subject='Imported',
                                         url_suffix='?import=not-existent')
        self._assert_custom_message(response, 404)
        self.assertFalse(Ticket.objects.filter(subject='Imported').exists())

    def test_import_invalid_content(self):
        compiled = CompiledTicket.objects.create(url_path='invalid', content='garbage')
        response = self.client.get(self._new_ticket_url() + f'?import={compiled.url_path}')
        self._assert_custom_message(response, 400)
        self.assertIn('non consistenti', response.context['avviso'])

    def test_import_without_input_module(self):
        content = encrypt_to_jwe(json.dumps({'ticket_subject': 'x'}).encode())
        compiled = CompiledTicket.objects.create(url_path='no-module', content=content)
        response = self.client.get(self._new_ticket_url() + f'?import={compiled.url_path}')
        self._assert_custom_message(response, 400)
        self.assertIn('Modulo di input mancante', response.context['avviso'])

    def test_generate_url_compiled_by_user(self):
        # generate an URL with "compiled by user" flag
        response = self._post_new_ticket(subject='Generated',
                                         button=TICKET_GENERATE_URL_BUTTON_NAME,
                                         extra={TICKET_COMPILED_BY_USER_NAME: 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['url_to_import'])
        compiled = CompiledTicket.objects.latest('created')
        # import it
        response = self.client.get(self._new_ticket_url() + f'?import={compiled.url_path}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['compiled_by'], self.staff_1)
        self.assertEqual(response.context['form'].data['ticket_subject'], 'Generated')
        # create it
        self._post_new_ticket(subject='Imported',
                              url_suffix=f'?import={compiled.url_path}')
        ticket = Ticket.objects.get(subject='Imported')
        self.assertEqual(ticket.compiled_by, self.staff_1)
        self.assertTrue(ticket.compiled)

    def test_api_get_and_post(self):
        factory = RequestFactory()
        url = self._new_ticket_url()

        request = factory.get(url)
        request.user = self.staff_1
        view = TicketAddNew()
        view.setup(request)
        data = view.get(request, self.structure_1.slug,
                        self.category_1_str_1.slug, api=True)
        self.assertEqual(data['categoria'], self.category_1_str_1)
        self.assertIn('form', data)

        # valid form but no action button: context data returned
        request = factory.post(url, {'ticket_subject': 'API',
                                     'ticket_description': 'API'})
        request.user = self.staff_1
        view = TicketAddNew()
        view.setup(request)
        data = view.post(request, self.structure_1.slug,
                         self.category_1_str_1.slug, api=True)
        self.assertEqual(data['categoria'], self.category_1_str_1)
        self.assertFalse(Ticket.objects.filter(subject='API').exists())

    def test_create_draft(self):
        draft = self._create_draft()
        self.assertFalse(TicketAssignment.objects.filter(ticket=draft).exists())

    def test_create_anonymous_ticket(self):
        self._update_category(allow_anonymous=True)
        self.client.logout()
        # valid CaPTCHA for anonymous users
        hidden = json.dumps({'created': timezone.localtime().isoformat(),
                             'text': 'ABCDE'})
        captcha = {'ticket_captcha': 'ABCDE',
                   'ticket_captcha_hidden': base64.b64encode(encrypt(hidden)).decode()}
        response = self._post_new_ticket(subject='Anonymous ticket', extra=captcha)
        self.assertRedirects(response, self._new_ticket_url())
        ticket = Ticket.objects.get(subject='Anonymous ticket')
        self.assertIsNone(ticket.created_by)

    def test_create_notification_ticket(self):
        self._update_category(is_notification=True)
        self._post_new_ticket(subject='Notification')
        ticket = Ticket.objects.get(subject='Notification')
        self.assertTrue(ticket.is_closed)
        self.assertTrue(ticket.is_notification)

    def test_create_ticket_receive_email(self):
        self._update_category(receive_email=True)
        mail.outbox = []
        self._post_new_ticket(subject='With mail')
        self.assertTrue(Ticket.objects.filter(subject='With mail').exists())
        recipients = [r for m in mail.outbox for r in m.to]
        # office operators (default office of structure 1) are notified
        self.assertIn(self.user_1.email, recipients)

    def _create_category_task(self):
        return TicketCategoryTask.objects.create(
            category=self.category_1_str_1,
            subject='Default task',
            description='Default task',
            code='default-task',
            is_active=True,
            attachment=self.create_fake_file(name='default_task'),
        )

    def test_create_ticket_with_default_tasks(self):
        self._create_category_task()
        self._post_new_ticket(subject='With tasks')
        ticket = Ticket.objects.get(subject='With tasks')
        task = Task.objects.get(ticket=ticket, subject='Default task')
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT,
                                                    task.get_folder())))
        # the attachment points to the copy in ticket task folder
        self.assertEqual(task.attachment.name,
                         '{}/default_task.pdf'.format(task.get_folder()))
        self.assertTrue(os.path.exists(task.attachment.path))

    def test_default_task_attachment_after_category_task_delete(self):
        category_task = self._create_category_task()
        self._post_new_ticket(subject='With tasks')
        ticket = Ticket.objects.get(subject='With tasks')
        task = Task.objects.get(ticket=ticket, subject='Default task')
        category_task.delete()
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs={'ticket_id': ticket.code,
                                                   'task_id': task.code}))
        self.assertEqual(response.status_code, 200)

    def test_create_ticket_with_default_tasks_copy_error(self):
        category_task = self._create_category_task()
        with patch('uni_ticket.views.user.shutil.copytree', side_effect=OSError), \
             self.assertLogs('uni_ticket.views.user', level='ERROR'):
            self._post_new_ticket(subject='With tasks error')
        ticket = Ticket.objects.get(subject='With tasks error')
        task = Task.objects.get(ticket=ticket, subject='Default task')
        # the category file reference is kept
        self.assertEqual(task.attachment.name,
                         category_task.attachment.name)

    @patch('uni_ticket.views.user.download_ticket_pdf',
           return_value=MagicMock(content=b'%PDF'))
    @patch('uni_ticket.views.user.ticket_protocol',
           return_value={'numero': '42', 'message': 'protocol message'})
    def test_create_ticket_with_protocol(self, mock_protocol, mock_pdf):
        self._update_category(protocol_required=True)
        self._post_new_ticket(subject=PROTOCOL_SUBJECT)
        ticket = Ticket.objects.get(subject=PROTOCOL_SUBJECT)
        self.assertTrue(mock_protocol.called)
        self.assertEqual(ticket.protocol_number, '42')
        self.assertTrue(ticket.protocol_date)

    @patch('uni_ticket.views.user.download_ticket_pdf',
           return_value=MagicMock(content=b'%PDF'))
    @patch('uni_ticket.views.user.ticket_protocol',
           side_effect=Exception('protocol error'))
    def test_create_ticket_with_protocol_error(self, mock_protocol, mock_pdf):
        self._update_category(protocol_required=True)
        response = self._post_new_ticket(subject=PROTOCOL_SUBJECT, follow=True)
        ticket = Ticket.objects.get(subject=PROTOCOL_SUBJECT)
        # ticket is created anyway
        self.assertFalse(ticket.protocol_number)
        msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(any('protocol error' in m for m in msgs))

    def test_create_ticket_with_formset_attachment(self):
        TicketCategoryInputList.objects.create(
            category_module=self.module_2,
            name='tabella',
            field_type='CustomComplexTableField',
            valore="documento({'type':'CustomFileField'})",
            is_required=False,
        )
        extra = {'tabella-TOTAL_FORMS': '1',
                 'tabella-INITIAL_FORMS': '0',
                 'tabella-MIN_NUM_FORMS': '0',
                 'tabella-MAX_NUM_FORMS': '1000',
                 'tabella-0-documento': self.create_fake_file(name='formset_file')}
        self._post_new_ticket(subject='Formset', extra=extra)
        ticket = Ticket.objects.get(subject='Formset')
        allegati = ticket.get_allegati_dict()
        self.assertEqual(allegati.get('tabella-0-documento'), 'formset_file.pdf')

    def test_create_ticket_attachments_with_same_name(self):
        self._add_second_file_field()
        extra = {'file_field_1': self.create_fake_file(name='same_name'),
                 'file_field_2': self.create_fake_file(name='same_name')}
        self._post_new_ticket(subject='Same name', extra=extra)
        ticket = Ticket.objects.get(subject='Same name')
        allegati = ticket.get_allegati_dict()
        self.assertEqual(len(allegati), 2)
        self.assertNotEqual(allegati['file_field_1'], allegati['file_field_2'])
        for file_name in allegati.values():
            self.assertTrue(self._attachment_exists(ticket, file_name))


class Test_UserTicketViews(UserViewsMixin, TempMediaRootMixin, BaseTicketEnvironment):

    def _ticket_url(self, name, ticket=None):
        return reverse(f'uni_ticket:{name}',
                       kwargs={'ticket_id': (ticket or self.ticket).code})

    def _share_ticket_with_user_1(self, ticket=None):
        ticket = ticket or self.ticket
        ticket.compiled_by = self.user_1
        ticket.save()

    # dashboard
    def test_dashboard_counters(self):
        self._create_draft()
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        response = self.client.get(reverse('uni_ticket:user_dashboard'))
        self.assertEqual(response.context['bozze'], 1)
        self.assertEqual(response.context['ticket_aperti'], 1)
        self.assertEqual(response.context['ticket_non_gestiti'], 1)

    def test_draft_ticket_page(self):
        response = self.client.get(reverse('uni_ticket:user_draft_ticket'))
        self.assertEqual(response.status_code, 200)

    # edit
    def test_edit_protocolled_ticket(self):
        self.ticket.protocol_number = '1'
        self.ticket.save()
        response = self.client.get(self._ticket_url('ticket_edit'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))

    def test_edit_ticket_compiled_by_other_user(self):
        self._share_ticket_with_user_1()
        self.structure_1_default_office_operator_login()
        response = self.client.get(self._ticket_url('ticket_edit'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))

    def test_edit_ticket_add_attachment(self):
        self.assertFalse(self.ticket_2.get_allegati_dict())
        params = {'ticket_subject': 'Ticket 2 edited',
                  'ticket_description': 'Ticket 2 edited',
                  TICKET_CONDITIONS_FIELD_ID: 'on',
                  'file_field_1': self.create_fake_file(name='new_file')}
        response = self.client.post(self._ticket_url('ticket_edit', self.ticket_2),
                                    params)
        self.assertRedirects(response, self._ticket_url('ticket_edit', self.ticket_2))
        self.ticket_2.refresh_from_db()
        self.assertEqual(self.ticket_2.subject, 'Ticket 2 edited')
        self.assertEqual(self.ticket_2.get_allegati_dict(),
                         {'file_field_1': 'new_file.pdf'})

    def test_edit_ticket_add_attachment_with_existing_name(self):
        self._add_second_file_field()
        self.assertEqual(self.ticket.get_allegati_dict(),
                         {'file_field_1': 'test.pdf'})
        params = {'ticket_subject': 'Ticket 1 edited',
                  'ticket_description': 'Ticket 1 edited',
                  TICKET_CONDITIONS_FIELD_ID: 'on',
                  'file_field_2': self.create_fake_file()}
        response = self.client.post(self._ticket_url('ticket_edit'), params)
        self.assertRedirects(response, self._ticket_url('ticket_edit'))
        self.ticket.refresh_from_db()
        allegati = self.ticket.get_allegati_dict()
        self.assertEqual(allegati['file_field_1'], 'test.pdf')
        self.assertNotEqual(allegati['file_field_2'], 'test.pdf')
        for file_name in allegati.values():
            self.assertTrue(self._attachment_exists(self.ticket, file_name))

    def test_delete_attachment_shared_by_another_field(self):
        # legacy tickets may have two fields pointing to the same file
        json_dict = self.ticket.get_modulo_compilato()
        json_dict[settings.ATTACHMENTS_DICT_PREFIX]['file_field_2'] = 'test.pdf'
        set_as_dict(self.ticket, json_dict)
        response = self.client.post(reverse('uni_ticket:delete_my_attachment',
                                            kwargs={'ticket_id': self.ticket.code,
                                                    'attachment': 'file_field_1'}))
        self.assertRedirects(response, self._ticket_url('ticket_edit'))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.get_allegati_dict(),
                         {'file_field_2': 'test.pdf'})
        self.assertTrue(self._attachment_exists(self.ticket, 'test.pdf'))

        # the file is removed when no other field uses it
        self.client.post(reverse('uni_ticket:delete_my_attachment',
                                 kwargs={'ticket_id': self.ticket.code,
                                         'attachment': 'file_field_2'}))
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.get_allegati_dict())
        self.assertFalse(self._attachment_exists(self.ticket, 'test.pdf'))

    # delete
    def test_delete_protocolled_ticket(self):
        self.ticket.protocol_number = '1'
        self.ticket.save()
        response = self.client.post(self._ticket_url('ticket_delete'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk).exists())

    def test_delete_ticket_by_compiler(self):
        self._share_ticket_with_user_1()
        self.structure_1_default_office_operator_login()
        response = self.client.post(self._ticket_url('ticket_delete'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk).exists())

    def test_delete_shared_ticket(self):
        self._share_ticket_with_user_1()
        response = self.client.post(self._ticket_url('ticket_delete'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk).exists())

    def test_delete_draft(self):
        draft = self._create_draft()
        response = self.client.post(self._ticket_url('ticket_delete', draft))
        self.assertRedirects(response, reverse('uni_ticket:user_unassigned_ticket'))
        self.assertFalse(Ticket.objects.filter(pk=draft.pk).exists())

    # detail
    def test_ticket_detail_print(self):
        task = Task.objects.create(ticket=self.ticket, subject='Printable',
                                   description='Printable', code='printable',
                                   is_printable=True)
        Task.objects.create(ticket=self.ticket, subject='Not printable',
                            description='Not printable', code='not-printable')
        response = self.client.get(self._ticket_url('ticket_detail_print'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['ticket_task']), [task])

    def test_ticket_detail_api(self):
        request = RequestFactory().get('/')
        request.user = self.staff_1
        data = TicketDetail().get(request, ticket_id=self.ticket.code, api=True)
        self.assertEqual(data['ticket'], self.ticket)
        self.assertEqual(data['allegati'], self.ticket.get_allegati_dict())

    def test_draft_detail(self):
        draft = self._create_draft()
        response = self.client.get(self._ticket_url('ticket_detail', draft))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category_1_str_1)
        self.assertTrue(response.context['user_can_open_tickets'])
        self.assertIn('allowed_users', response.context)

    def test_ticket_url(self):
        response = self.client.get(reverse('uni_ticket:user_ticket_url'))
        self._assert_custom_message(response)

    # messages
    def test_ticket_message_marks_operator_replies_as_read(self):
        reply = TicketReply.objects.create(ticket=self.ticket,
                                           owner=self.user_1,
                                           structure=self.structure_1,
                                           subject='Operator reply',
                                           text='Operator reply')
        response = self.client.get(self._ticket_url('ticket_message'))
        self.assertEqual(response.status_code, 200)
        reply.refresh_from_db()
        self.assertEqual(reply.read_by, self.staff_1)
        self.assertTrue(reply.read_date)

    def test_ticket_message_with_operators_email(self):
        self._update_category(receive_email=True)
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        mail.outbox = []
        response = self.client.post(self._ticket_url('ticket_message'),
                                    {'subject': 'User message',
                                     'text': 'User message'})
        self.assertRedirects(response, self._ticket_url('ticket_message'))
        self.assertTrue(TicketReply.objects.filter(ticket=self.ticket,
                                                   subject='User message').exists())
        recipients = [r for m in mail.outbox for r in m.to]
        self.assertIn(self.user_1.email, recipients)

    # close
    def test_close_already_closed_ticket(self):
        self.ticket.is_closed = True
        self.ticket.save()
        response = self.client.get(self._ticket_url('user_close_ticket'))
        self._assert_custom_message(response)

    def test_close_not_shared_draft(self):
        draft = self._create_draft()
        response = self.client.get(self._ticket_url('user_close_ticket', draft))
        self._assert_custom_message(response)

    def test_close_ticket_by_compiler(self):
        self._share_ticket_with_user_1()
        self.structure_1_default_office_operator_login()
        response = self.client.get(self._ticket_url('user_close_ticket'))
        self.assertRedirects(response, self._ticket_url('ticket_detail'))

    def test_close_ticket_form(self):
        response = self.client.get(self._ticket_url('user_close_ticket'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def _assert_close_rejected(self, params):
        response = self.client.post(self._ticket_url('user_close_ticket'), params,
                                    follow=True)
        self.assertRedirects(response, self._ticket_url('ticket_detail'))
        self.assertTrue(any(m.level_tag == 'error'
                            for m in response.context['messages']))
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_closed)

    def test_close_ticket_invalid_form(self):
        self._assert_close_rejected({'other': 'value'})

    def test_close_ticket_empty_post(self):
        self._assert_close_rejected({})

    def test_close_ticket_by_owner_does_not_set_closed_by(self):
        response = self.client.post(self._ticket_url('user_close_ticket'),
                                    {'note': 'Closed by owner'}, follow=True)
        self.assertRedirects(response, self._ticket_url('ticket_detail'))
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)
        self.assertEqual(self.ticket.closing_reason, 'Closed by owner')
        # closed_by identifies operators' closures (see ticket_reopen)
        self.assertIsNone(self.ticket.closed_by)

    def test_close_ticket_api_get(self):
        request = RequestFactory().get('/')
        request.user = self.staff_1
        view = TicketClose()
        view.context_data = {}
        context = view.get(request, api=True)
        self.assertIs(context, view.context_data)
        self.assertIsInstance(context['form'], BaseTicketCloseForm)

    # reopen
    def test_reopen_not_closed_ticket(self):
        response = self.client.post(self._ticket_url('user_reopen_ticket'))
        self._assert_custom_message(response)

    def test_reopen_ticket_closed_by_operator(self):
        self.ticket.is_closed = True
        self.ticket.closed_by = self.user_1
        self.ticket.save()
        response = self.client.post(self._ticket_url('user_reopen_ticket'))
        self._assert_custom_message(response)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)

    def test_reopen_notification_ticket(self):
        self.ticket.is_closed = True
        self.ticket.is_notification = True
        self.ticket.save()
        response = self.client.post(self._ticket_url('user_reopen_ticket'))
        self._assert_custom_message(response)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)

    def test_reopen_with_other_open_tickets(self):
        self.ticket.is_closed = True
        self.ticket.save()
        self._update_category(user_multiple_open_tickets=False)
        response = self.client.post(self._ticket_url('user_reopen_ticket'))
        self._assert_custom_message(response)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_closed)

    # clone
    def test_clone_with_inactive_module(self):
        self.module_2.is_active = False
        self.module_2.save()
        response = self.client.get(self._ticket_url('user_clone_ticket'))
        self._assert_custom_message(response)

    def test_clone_redirects_to_import(self):
        response = self.client.get(self._ticket_url('user_clone_ticket'))
        compiled = CompiledTicket.objects.latest('created')
        self.assertRedirects(response,
                             self._new_ticket_url() + f'?import={compiled.url_path}',
                             fetch_redirect_response=False)


class Test_UserSubmitDraft(UserViewsMixin, TempMediaRootMixin, BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.draft = self._create_draft()
        self.submit_url = reverse('uni_ticket:ticket_submit_draft',
                                  kwargs={'ticket_id': self.draft.code})
        self.detail_url = reverse('uni_ticket:ticket_detail',
                                  kwargs={'ticket_id': self.draft.code})

    def _submit(self, params=None):
        params = params or {TICKET_SUBMIT_DRAFT_BUTTON_NAME: 'ok'}
        return self.client.post(self.submit_url, params)

    def test_submit_invalid_draft(self):
        with patch.object(Ticket, 'is_valid', return_value=False):
            response = self._submit()
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.draft)

    def test_submit_without_accepting_conditions(self):
        TicketCategoryCondition.objects.create(category=self.category_1_str_1,
                                               title='Condition',
                                               text='Condition')
        response = self._submit()
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.draft)

    def test_submit_user_not_allowed(self):
        self.category_1_str_1.allowed_users.add(self.user_2)
        response = self._submit()
        self._assert_custom_message(response, 403)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.draft)

    def test_submit_daily_limit_reached(self):
        with patch.object(Ticket, 'number_limit_reached_by_user', return_value=True):
            response = self._submit()
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.draft)

    def test_submit_draft(self):
        TicketCategoryTask.objects.create(category=self.category_1_str_1,
                                          subject='Default task',
                                          description='Default task',
                                          code='default-task',
                                          is_active=True)
        self._update_category(receive_email=True)
        mail.outbox = []
        response = self._submit()
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertFalse(self.draft.draft)
        self.assertTrue(TicketAssignment.objects.filter(ticket=self.draft).exists())
        self.assertTrue(Task.objects.filter(ticket=self.draft,
                                            subject='Default task').exists())
        recipients = [r for m in mail.outbox for r in m.to]
        self.assertIn(self.user_1.email, recipients)
        self.assertIn(self.staff_1.email, recipients)

    @patch('uni_ticket.views.user.download_ticket_pdf',
           return_value=MagicMock(content=b'%PDF'))
    @patch('uni_ticket.views.user.ticket_protocol',
           return_value={'numero': '7'})
    def test_submit_notification_draft_with_protocol(self, mock_protocol, mock_pdf):
        self._update_category(is_notification=True, protocol_required=True)
        response = self._submit()
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertFalse(self.draft.draft)
        self.assertTrue(self.draft.is_closed)
        self.assertEqual(self.draft.protocol_number, '7')

    def test_share_already_shared_draft(self):
        self.draft.compiled_by = self.user_1
        self.draft.save()
        response = self._submit({TICKET_SHARE_DRAFT_BUTTON_NAME: 'ok',
                                 'sharing_user': self.user_2.pk})
        self._assert_custom_message(response, 403)

    def test_share_without_user(self):
        response = self._submit({TICKET_SHARE_DRAFT_BUTTON_NAME: 'ok'})
        self.assertRedirects(response, self.detail_url)
        self.draft.refresh_from_db()
        self.assertIsNone(self.draft.compiled_by)

    def test_share_with_not_allowed_user(self):
        self.category_1_str_1.allowed_users.add(self.staff_1)
        response = self._submit({TICKET_SHARE_DRAFT_BUTTON_NAME: 'ok',
                                 'sharing_user': self.user_2.pk})
        self._assert_custom_message(response, 403)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.created_by, self.staff_1)

    def test_share_draft(self):
        response = self._submit({TICKET_SHARE_DRAFT_BUTTON_NAME: 'ok',
                                 'sharing_user': self.user_1.pk})
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.created_by, self.user_1)
        self.assertEqual(self.draft.compiled_by, self.staff_1)
        self.assertTrue(self.draft.draft)

    def test_close_shared_draft_by_compiler(self):
        self.draft.compiled_by = self.staff_1
        self.draft.created_by = self.user_1
        self.draft.save()
        response = self.client.get(reverse('uni_ticket:user_close_ticket',
                                           kwargs={'ticket_id': self.draft.code}))
        self._assert_custom_message(response)

    def test_submit_without_action(self):
        # neither submit nor share button: nothing changes
        response = self._submit({'other': 'value'})
        self.assertRedirects(response,
                             reverse('uni_ticket:ticket_detail',
                                     kwargs={'ticket_id': self.draft.code}),
                             fetch_redirect_response=False)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.draft)


class Test_UserExtraViews(UserViewsMixin, TempMediaRootMixin, BaseTicketEnvironment):

    def _ticket_url(self, name, ticket=None, **kwargs):
        kwargs['ticket_id'] = (ticket or self.ticket).code
        return reverse(f'uni_ticket:{name}', kwargs=kwargs)

    def _error_messages(self, response):
        return [str(m) for m in response.context['messages']
                if m.level_tag == 'error']

    def test_edit_ticket_invalid_form(self):
        response = self.client.post(self._ticket_url('ticket_edit'),
                                    {'ticket_description': 'No subject'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._error_messages(response))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, 'Ticket 1')

    def test_ticket_message_invalid_form(self):
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        response = self.client.post(self._ticket_url('ticket_message'),
                                    {'subject': 'Without text'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._error_messages(response))
        self.assertFalse(TicketReply.objects.filter(ticket=self.ticket,
                                                    subject='Without text').exists())

    def _create_task(self, is_public=True):
        return Task.objects.create(ticket=self.ticket,
                                   subject='Task',
                                   description='Task description',
                                   code='user-task-{}'.format(int(is_public)),
                                   is_public=is_public)

    def test_task_detail(self):
        task = self._create_task()
        response = self.client.get(self._ticket_url('task_detail', task_id=task.code))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/task_detail.html')
        self.assertEqual(response.context['task'], task)
        self.assertEqual(response.context['priority'], task.get_priority())

    def test_task_detail_reserved_to_operators(self):
        task = self._create_task(is_public=False)
        response = self.client.get(self._ticket_url('task_detail', task_id=task.code))
        self._assert_custom_message(response)
        self.assertNotIn('task', response.context)

    def test_task_detail_of_another_ticket(self):
        task = self._create_task()
        response = self.client.get(self._ticket_url('task_detail',
                                                    ticket=self.ticket_2,
                                                    task_id=task.code))
        self.assertEqual(response.status_code, 404)

    def test_ticket_detail_print(self):
        response = self.client.get(self._ticket_url('ticket_detail_print'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ticket_detail_print.html')
        self.assertEqual(response.context['ticket'], self.ticket)

    @patch('uni_ticket.views.user.response_as_pdf')
    def test_download_ticket_pdf(self, mock_pdf):
        mock_pdf.return_value = HttpResponse(b'%PDF', content_type='application/pdf')
        response = self.client.get(self._ticket_url('ticket_detail_print_pdf'))
        self.assertEqual(response.content, b'%PDF')
        html_response, pdf_fname = mock_pdf.call_args.args
        self.assertEqual(pdf_fname, '{}.pdf'.format(self.ticket.code))
        self.assertIn(self.ticket.subject, html_response.content.decode())

    @patch('uni_ticket.views.user.render', return_value=HttpResponse('ok'))
    def test_chat_new_preload(self, mock_render):
        # chat app is not installed in tests: call the view directly
        request = RequestFactory().get('/')
        request.user = self.staff_1
        chat_new_preload(request)
        context = mock_render.call_args.args[2]
        self.assertIsNone(context['structure_slug'])
        self.assertEqual(set(context['strutture']),
                         {self.structure_1, self.structure_2})

        chat_new_preload(request, structure_slug=self.structure_1.slug)
        context = mock_render.call_args.args[2]
        self.assertEqual(context['sub_title'], self.structure_1)

        with self.assertRaises(Http404):
            chat_new_preload(request, structure_slug='not-existent')

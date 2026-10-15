import logging
import shutil
import tempfile

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings
from django.urls import reverse

from organizational_area.models import (OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee)
from uni_ticket.decorators import (has_access_to_ticket,
                                   has_ticket_admin_privileges,
                                   is_manager,
                                   is_operator,
                                   is_super_admin,
                                   ticket_assigned_to_structure,
                                   ticket_is_not_taken_and_not_closed,
                                   ticket_is_taken_and_not_closed,
                                   ticket_is_taken_for_employee)
from uni_ticket.models import (Task,
                               TicketCategoryCondition,
                               TicketReply)
from uni_ticket.views import generic, handlers

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


def _ok_view(request, *args, **kwargs):
    return HttpResponse("ok")


class TempMediaRootMixin:
    """
    Store uploaded files in a temporary MEDIA_ROOT, removed at the end
    """

    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp(prefix='uniticket_test_media_')
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)


class Test_Decorators(TempMediaRootMixin, BaseTicketEnvironment):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def _request(self, user, **attrs):
        request = self.factory.get('/')
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        for k, v in attrs.items():
            setattr(request, k, v)
        return request

    def test_is_super_admin(self):
        view = is_super_admin(_ok_view)
        # simple user: denied
        response = view(self._request(self.user_1))
        self.assertNotEqual(response.content, b"ok")
        # superuser: allowed
        self.user_1.is_superuser = True
        self.user_1.save()
        response = view(self._request(self.user_1))
        self.assertEqual(response.content, b"ok")

    def test_is_operator_redirects_manager(self):
        self.structure_1_manager_login()
        response = self.client.get(reverse('uni_ticket:operator_dashboard',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertRedirects(response,
                             reverse('uni_ticket:manager_dashboard',
                                     kwargs={'structure_slug': self.structure_1.slug}),
                             fetch_redirect_response=False)

    def test_is_manager(self):
        view = is_manager(_ok_view)
        response = view(self._request(self.staff_1), structure_slug=self.structure_1.slug)
        self.assertEqual(response.content, b"ok")
        response = view(self._request(self.user_1), structure_slug=self.structure_1.slug)
        self.assertNotEqual(response.content, b"ok")

    def test_is_operator(self):
        view = is_operator(_ok_view)
        request = self._request(self.user_1)
        response = view(request, structure_slug=self.structure_1.slug)
        self.assertEqual(response.content, b"ok")
        self.assertTrue(request.office_employee)
        # user_2 is not an operator of structure 1
        response = view(self._request(self.user_2), structure_slug=self.structure_1.slug)
        self.assertNotEqual(response.content, b"ok")

    def test_has_ticket_admin_privileges_default_office(self):
        view = has_ticket_admin_privileges(_ok_view)
        # structure 1 default office: allowed
        request = self._request(self.staff_1)
        response = view(request, structure_slug=self.structure_1.slug,
                        ticket_id=self.ticket.code)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(request.can_manage, {'follow': True, 'readonly': False})
        # structure 2 default office: ticket is not followed in structure 2
        response = view(self._request(self.staff_2),
                        structure_slug=self.structure_2.slug,
                        ticket_id=self.ticket.code)
        self.assertEqual(response.status_code, 302)

    def test_ticket_is_not_taken_and_not_closed(self):
        view = ticket_is_not_taken_and_not_closed(_ok_view)
        response = view(self._request(self.staff_1, ticket=self.ticket))
        self.assertEqual(response.content, b"ok")
        # closed
        self.ticket.is_closed = True
        self.ticket.save()
        response = view(self._request(self.staff_1, ticket=self.ticket))
        self.assertNotEqual(response.content, b"ok")
        # taken
        self.ticket.is_closed = False
        self.ticket.save()
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        response = view(self._request(self.staff_1, ticket=self.ticket))
        self.assertNotEqual(response.content, b"ok")

    def test_has_ticket_admin_privileges_office_operator(self):
        view = has_ticket_admin_privileges(_ok_view)
        kwargs = {'structure_slug': self.structure_1.slug,
                  'ticket_id': self.ticket.code}
        # user_2 is operator of office_1_str_1 (not default office)
        OrganizationalStructureOfficeEmployee.objects.create(employee=self.user_2,
                                                             office=self.office_1_str_1)
        request = self._request(self.user_2)
        response = view(request, **kwargs)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(request.can_manage, {'follow': True, 'readonly': False})

    def test_has_ticket_admin_privileges_office_operator_denied(self):
        view = has_ticket_admin_privileges(_ok_view)
        kwargs = {'structure_slug': self.structure_1.slug,
                  'ticket_id': self.ticket.code}
        # new office, not involved in the ticket
        office = OrganizationalStructureOffice.objects.create(
            name='Other office',
            slug='other-office',
            organizational_structure=self.structure_1,
            is_active=True
        )
        OrganizationalStructureOfficeEmployee.objects.create(employee=self.user_2,
                                                             office=office)
        response = view(self._request(self.user_2), **kwargs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         reverse('uni_ticket:manage',
                                 kwargs={'structure_slug': self.structure_1.slug}))

    def test_has_access_to_ticket(self):
        view = has_access_to_ticket(_ok_view)
        # user_1 is operator of structure 1 default office
        response = view(self._request(self.user_1), ticket_id=self.ticket.code)
        self.assertEqual(response.content, b"ok")
        # user_2 has nothing to do with the ticket
        with self.assertRaises(Http404):
            view(self._request(self.user_2), ticket_id=self.ticket.code)

    def test_ticket_is_taken_and_not_closed(self):
        view = ticket_is_taken_and_not_closed(_ok_view)
        # not taken
        response = view(self._request(self.staff_1), ticket_id=self.ticket.code)
        self.assertNotEqual(response.content, b"ok")
        # taken
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        response = view(self._request(self.staff_1), ticket_id=self.ticket.code)
        self.assertEqual(response.content, b"ok")
        # closed
        self.ticket.is_closed = True
        self.ticket.save()
        response = view(self._request(self.staff_1), ticket_id=self.ticket.code)
        self.assertNotEqual(response.content, b"ok")

    def test_ticket_assigned_to_structure(self):
        view = ticket_assigned_to_structure(_ok_view)
        response = view(self._request(self.staff_1, structure=self.structure_1),
                        structure_slug=self.structure_1.slug,
                        ticket_id=self.ticket.code)
        self.assertEqual(response.content, b"ok")
        response = view(self._request(self.staff_2, structure=self.structure_2),
                        structure_slug=self.structure_2.slug,
                        ticket_id=self.ticket.code)
        self.assertNotEqual(response.content, b"ok")

    def test_ticket_is_taken_for_employee(self):
        view = ticket_is_taken_for_employee(_ok_view)
        kwargs = {'structure_slug': self.structure_1.slug,
                  'ticket_id': self.ticket.code}
        detail_url = reverse('uni_ticket:manage_ticket_url_detail', kwargs=kwargs)

        # readonly competence
        request = self._request(self.staff_1,
                                structure=self.structure_1,
                                can_manage={'follow': True, 'readonly': True})
        response = view(request, **kwargs)
        self.assertEqual(response.url, detail_url)

        # not taken
        request = self._request(self.staff_1,
                                structure=self.structure_1,
                                can_manage={'follow': True, 'readonly': False})
        response = view(request, **kwargs)
        self.assertEqual(response.url, detail_url)

        # taken
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        request = self._request(self.staff_1,
                                structure=self.structure_1,
                                can_manage={'follow': True, 'readonly': False})
        response = view(request, **kwargs)
        self.assertEqual(response.content, b"ok")


class Test_GenericViews(TempMediaRootMixin, BaseTicketEnvironment):

    def _create_task(self, attachment=True, is_public=True):
        task = Task.objects.create(
            ticket=self.ticket,
            subject='Task',
            description='Task',
            code='task-code-{}-{}'.format(int(attachment), int(is_public)),
            is_public=is_public,
        )
        if attachment:
            task.attachment = SimpleUploadedFile('task.pdf', b'task_file',
                                                 content_type='application/pdf')
            task.closing_attachment = SimpleUploadedFile('closing.pdf', b'closing_file',
                                                         content_type='application/pdf')
            task.save()
        return task

    def test_manage_redirects(self):
        # without structure
        response = self.client.get(reverse('uni_ticket:manage'))
        self.assertRedirects(response, reverse('uni_ticket:user_dashboard'))
        # manager
        response = self.client.get(reverse('uni_ticket:manage',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertRedirects(response,
                             reverse('uni_ticket:manager_dashboard',
                                     kwargs={'structure_slug': self.structure_1.slug}),
                             fetch_redirect_response=False)
        # simple user in structure 2
        response = self.client.get(reverse('uni_ticket:manage',
                                           kwargs={'structure_slug': self.structure_2.slug}))
        self.assertRedirects(response, reverse('uni_ticket:user_dashboard'))

    def test_download_task_attachments(self):
        task = self._create_task()
        kwargs = {'ticket_id': self.ticket.code, 'task_id': task.code}
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'task_file')
        response = self.client.get(reverse('uni_ticket:download_task_closing_attachment',
                                           kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'closing_file')

    def test_download_task_attachment_without_file(self):
        task = self._create_task(attachment=False)
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs={'ticket_id': self.ticket.code,
                                                   'task_id': task.code}))
        self.assertEqual(response.status_code, 404)

    def test_download_task_attachment_denied(self):
        task = self._create_task()
        kwargs = {'ticket_id': self.ticket.code, 'task_id': task.code}
        # not owner nor operator
        self.structure_2_default_office_operator_login()
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'custom_message.html')
        self.assertNotEqual(response.content, b'task_file')

    def test_download_private_task_attachment_by_owner(self):
        task = self._create_task(is_public=False)
        # owner (not operator) of a ticket of another structure
        self.structure_2_default_office_operator_login()
        ticket = self.create_ticket(subject='Ticket user 2',
                                    attachment=None,
                                    structure_slug=self.structure_1.slug,
                                    category=self.category_1_str_1)
        task.ticket = ticket
        task.save()
        response = self.client.get(reverse('uni_ticket:download_task_attachment',
                                           kwargs={'ticket_id': ticket.code,
                                                   'task_id': task.code}))
        self.assertTemplateUsed(response, 'custom_message.html')

    def test_manager_my_opened_ticket(self):
        response = self.client.get(reverse('uni_ticket:manager_my_opened_ticket',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['structure'], self.structure_1)

    def test_email_notify_change_without_email(self):
        self.staff_1.email = ''
        self.staff_1.save()
        response = self.client.post(reverse('uni_ticket:email_notify_change'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['data']['error'])

    def test_email_notify_change_get(self):
        response = self.client.get(reverse('uni_ticket:email_notify_change'))
        self.assertEqual(response.status_code, 404)

    def _add_reply(self, owner, structure=None, read=False, ticket=None):
        reply = TicketReply.objects.create(ticket=ticket or self.ticket,
                                           owner=owner,
                                           structure=structure,
                                           subject='Reply',
                                           text='Reply text')
        if read:
            reply.read_by = owner
            reply.read_date = reply.created
            reply.save()
        return reply

    def test_ticket_messages_user(self):
        self._add_reply(owner=self.staff_1, structure=self.structure_1)
        response = self.client.get(reverse('uni_ticket:messages'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ticket_messages']), 1)
        self.assertEqual(response.context['my_assignments_list'], [])

    def test_ticket_messages_manager(self):
        self.ticket.take(user=self.staff_1, structure=self.structure_1)
        self._add_reply(owner=self.staff_1)
        response = self.client.get(reverse('uni_ticket:manager_messages',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['my_assignments_list'], [self.ticket.pk])

    def test_ticket_messages_operator(self):
        self._add_reply(owner=self.staff_1)
        self.structure_1_default_office_operator_login()
        response = self.client.get(reverse('uni_ticket:operator_messages',
                                           kwargs={'structure_slug': self.structure_1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ticket_messages']), 1)

    def test_ticket_message_delete_not_owner(self):
        reply = self._add_reply(owner=self.staff_1)
        self.structure_1_default_office_operator_login()
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': reply.pk}))
        self.assertTemplateUsed(response, 'custom_message.html')
        self.assertTrue(TicketReply.objects.filter(pk=reply.pk).exists())

    def test_ticket_message_delete_already_read(self):
        reply = self._add_reply(owner=self.staff_1, read=True)
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': reply.pk}))
        self.assertTemplateUsed(response, 'custom_message.html')
        self.assertTrue(TicketReply.objects.filter(pk=reply.pk).exists())

    def test_ticket_message_delete_by_user(self):
        reply = self._add_reply(owner=self.staff_1)
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': reply.pk}))
        self.assertRedirects(response,
                             reverse('uni_ticket:ticket_message',
                                     kwargs={'ticket_id': self.ticket.code}),
                             fetch_redirect_response=False)
        self.assertFalse(TicketReply.objects.filter(pk=reply.pk).exists())

    def test_ticket_message_delete_by_manager(self):
        reply = self._add_reply(owner=self.staff_1, structure=self.structure_1)
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': reply.pk}))
        self.assertRedirects(response,
                             reverse('uni_ticket:manage_ticket_message_url',
                                     kwargs={'structure_slug': self.structure_1.slug,
                                             'ticket_id': self.ticket.code}),
                             fetch_redirect_response=False)
        self.assertFalse(TicketReply.objects.filter(pk=reply.pk).exists())

    def test_ticket_message_delete_structure_simple_user(self):
        # staff_1 is a simple user in structure 2
        reply = self._add_reply(owner=self.staff_1, structure=self.structure_2)
        response = self.client.get(reverse('uni_ticket:message_delete',
                                           kwargs={'ticket_message_id': reply.pk}))
        self.assertTemplateUsed(response, 'custom_message.html')
        self.assertTrue(TicketReply.objects.filter(pk=reply.pk).exists())

    def _create_condition(self, attachment=True):
        condition = TicketCategoryCondition.objects.create(
            category=self.category_1_str_1,
            title='Condition',
            text='Condition text'
        )
        if attachment:
            condition.attachment = SimpleUploadedFile('condition.pdf', b'condition_file',
                                                      content_type='application/pdf')
            condition.save()
        return condition

    def _condition_url(self, condition):
        return reverse('uni_ticket:download_condition_attachment',
                       kwargs={'structure_slug': self.structure_1.slug,
                               'category_slug': self.category_1_str_1.slug,
                               'condition_id': condition.pk})

    def test_download_condition_attachment(self):
        condition = self._create_condition()
        response = self.client.get(self._condition_url(condition))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'condition_file')

    def test_download_condition_without_attachment(self):
        condition = self._create_condition(attachment=False)
        response = self.client.get(self._condition_url(condition))
        self.assertEqual(response.status_code, 404)

    def test_download_condition_attachment_anonymous(self):
        condition = self._create_condition()
        self.client.logout()
        response = self.client.get(self._condition_url(condition))
        self.assertEqual(response.status_code, 302)
        self.assertIn('next=', response.url)

    def test_custom_404(self):
        response = self.client.get('/this-url-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    def test_handlers_error_404(self):
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        response = handlers.error_404(request, Http404())
        self.assertEqual(response.status_code, 200)
        response = generic.custom_404(request, Http404())
        self.assertEqual(response.status_code, 404)

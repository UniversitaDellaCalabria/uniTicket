import logging
import shutil
import tempfile

from datetime import timedelta
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from organizational_area.models import (OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,
                                        UserManageOrganizationalStructure)
from uni_ticket.models import (OrganizationalStructureAlert,
                               OrganizationalStructureAllowedUsersList,
                               TicketCategory,
                               TicketCategoryCondition,
                               TicketCategoryDefaultReply,
                               TicketCategoryInputList,
                               TicketCategoryModule,
                               TicketCategoryTask,
                               TicketCategoryWSProtocollo)

from . base_category_office_env import BaseCategoryOfficeEnvironment
from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


def get_messages_list(response):
    """
    Returns the list of (string) messages rendered in response
    """
    if not response.context or 'messages' not in response.context:
        return []
    return [str(m) for m in response.context['messages']]


class ManagerViewsMixin:
    """
    Url helpers for structure 1 manager views
    """

    def url(self, name, **kwargs):
        kwargs.setdefault('structure_slug', self.structure_1.slug)
        return reverse('uni_ticket:{}'.format(name), kwargs=kwargs)

    def cat_url(self, name, category=None, **kwargs):
        category = category or self.category_1_str_1
        return self.url(name, category_slug=category.slug, **kwargs)

    def assertMessage(self, response, text):
        msgs = get_messages_list(response)
        self.assertTrue(any(text in m for m in msgs),
                        "'{}' not in {}".format(text, msgs))


class Test_ManagerOfficeViews(ManagerViewsMixin, BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()
        self.default_office = self.structure_1.get_default_office()

    def test_office_add_new_get(self):
        response = self.client.get(self.url('manager_office_add_new'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manager/office_add_new.html')
        self.assertEqual(response.context['structure'], self.structure_1)

    def test_office_add_new_duplicate_name(self):
        offices_count = OrganizationalStructureOffice.objects.count()
        response = self.client.post(self.url('manager_office_add_new'),
                                    {'name': self.office_1_str_1.name},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertMessage(response, 'Esiste già un ufficio')
        self.assertEqual(OrganizationalStructureOffice.objects.count(),
                         offices_count)

    def test_office_edit_get(self):
        response = self.client.get(self.url('manager_office_edit',
                                            office_slug=self.office_1_str_1.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['office'], self.office_1_str_1)

    def test_office_edit_duplicate_name(self):
        office_2 = self.create_new_office(name='Office 2',
                                          structure_slug=self.structure_1.slug)
        response = self.client.post(self.url('manager_office_edit',
                                             office_slug=office_2.slug),
                                    {'name': self.office_1_str_1.name},
                                    follow=True)
        self.assertMessage(response, 'Esiste già un ufficio con questo nome')
        office_2.refresh_from_db()
        self.assertEqual(office_2.name, 'Office 2')

    def test_office_add_category(self):
        category = self.add_new_category(cat_name='Category 2 Structure 1',
                                         structure_slug=self.structure_1.slug)
        self.assertIsNone(category.organizational_office)
        response = self.client.post(self.url('manager_add_office_category',
                                             office_slug=self.office_1_str_1.slug),
                                    {'category': category.slug},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertMessage(response, 'Competenza ufficio impostata')
        category.refresh_from_db()
        self.assertEqual(category.organizational_office, self.office_1_str_1)

    def test_office_add_category_already_assigned(self):
        # a category with an office is excluded by the form queryset
        response = self.client.post(self.url('manager_add_office_category',
                                             office_slug=self.default_office.slug),
                                    {'category': self.category_1_str_1.slug},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.category_1_str_1.refresh_from_db()
        self.assertEqual(self.category_1_str_1.organizational_office,
                         self.office_1_str_1)

    def test_office_add_category_get(self):
        response = self.client.get(self.url('manager_add_office_category',
                                            office_slug=self.office_1_str_1.slug))
        self.assertEqual(response.status_code, 200)
        self.assertIn('senza passare dal form', str(response.context['avviso']))

    def test_office_remove_category_not_competent(self):
        response = self.client.get(self.url('manager_remove_office_category',
                                            office_slug=self.default_office.slug,
                                            category_slug=self.category_1_str_1.slug),
                                   follow=True)
        self.assertMessage(response, 'non è di competenza di questo ufficio')
        self.category_1_str_1.refresh_from_db()
        self.assertEqual(self.category_1_str_1.organizational_office,
                         self.office_1_str_1)
        self.assertTrue(self.category_1_str_1.is_active)

    def test_office_add_operator_get_search(self):
        url = self.url('manager_add_office_operator',
                       office_slug=self.office_1_str_1.slug)
        response = self.client.get(url, {'search': 'User 1', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['key'], 'User 1')
        pks = [u['pk'] for u in response.context['users']]
        self.assertIn(self.user_1.pk, pks)
        self.assertNotIn(self.staff_1.pk, pks)

    def test_office_add_operator_invalid_form(self):
        response = self.client.post(self.url('manager_add_office_operator',
                                             office_slug=self.office_1_str_1.slug),
                                    {'description': 'no user'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertMessage(response, 'Scelta non valida')

    def test_office_add_operator_already_assigned(self):
        response = self.client.post(self.url('manager_add_office_operator',
                                             office_slug=self.default_office.slug),
                                    {'user': self.user_1.pk},
                                    follow=True)
        self.assertIn('Operatore già assegnato', str(response.context['avviso']))
        self.assertEqual(OrganizationalStructureOfficeEmployee.objects.filter(
            employee=self.user_1, office=self.default_office).count(), 1)

    def test_office_remove_manager_from_default_office(self):
        response = self.client.get(self.url('manager_remove_office_operator',
                                            office_slug=self.default_office.slug,
                                            employee_id=self.staff_1.pk),
                                   follow=True)
        self.assertIn('privilegi di Amministratore',
                      str(response.context['avviso']))
        self.assertTrue(OrganizationalStructureOfficeEmployee.objects.filter(
            employee=self.staff_1, office=self.default_office).exists())

    def test_office_remove_operator_not_assigned(self):
        response = self.client.get(self.url('manager_remove_office_operator',
                                            office_slug=self.office_1_str_1.slug,
                                            employee_id=self.user_2.pk),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertMessage(response, "L'operatore non è assegnato a questo ufficio")

    def test_office_disable_default(self):
        response = self.client.get(self.url('manager_disable_office',
                                            office_slug=self.default_office.slug),
                                   follow=True)
        self.assertMessage(response, 'Impossibile disattivare questo ufficio')
        self.default_office.refresh_from_db()
        self.assertTrue(self.default_office.is_active)

    def test_office_disable_already_disabled(self):
        self.disable_office(self.structure_1.slug, self.office_1_str_1)
        self.assertFalse(self.office_1_str_1.is_active)
        response = self.client.get(self.url('manager_disable_office',
                                            office_slug=self.office_1_str_1.slug),
                                   follow=True)
        self.assertMessage(response, 'già disattivato')

    def test_office_enable_already_enabled(self):
        response = self.client.get(self.url('manager_enable_office',
                                            office_slug=self.office_1_str_1.slug),
                                   follow=True)
        self.assertMessage(response, 'già attivato')

    def test_office_delete_default(self):
        response = self.client.get(self.url('manager_delete_office',
                                            office_slug=self.default_office.slug),
                                   follow=True)
        self.assertMessage(response, 'Impossibile eliminare')
        self.assertTrue(OrganizationalStructureOffice.objects.filter(
            pk=self.default_office.pk).exists())


class Test_ManagerCategoryViews(ManagerViewsMixin, BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    def test_category_detail_office_already_assigned(self):
        response = self.client.post(self.cat_url('manager_category_detail'),
                                    {'office': self.office_1_str_1.slug},
                                    follow=True)
        self.assertMessage(response, 'Competenza ufficio già presente')

    def test_category_add_ticket_user(self):
        url = self.cat_url('manager_category_add_ticket_user')

        # GET with search
        response = self.client.get(url, {'search': 'User'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['key'], 'User')
        self.assertTrue(response.context['users'])

        # add user
        response = self.client.post(url, {'user': self.user_2.pk}, follow=True)
        self.assertMessage(response, 'Utente inserito con successo')
        self.assertIn(self.user_2, self.category_1_str_1.allowed_users.all())

        # add same user again
        response = self.client.post(url, {'user': self.user_2.pk}, follow=True)
        self.assertIn('Utente già selezionato', str(response.context['avviso']))

        # remove user
        remove_url = self.cat_url('manager_category_remove_ticket_user',
                                  user_id=self.user_2.pk)
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, 'rimosso correttamente')
        self.assertNotIn(self.user_2, self.category_1_str_1.allowed_users.all())

        # remove user again
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, "non è tra quelli abilitati")

    def test_category_add_ticket_users_list(self):
        users_list = OrganizationalStructureAllowedUsersList.objects.create(
            organizational_structure=self.structure_1,
            name='List 1'
        )
        url = self.cat_url('manager_category_add_ticket_users_list')

        # GET with search
        response = self.client.get(url, {'search': 'List'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['pk'] for i in response.context['lists']],
                         [users_list.pk])

        # add list
        response = self.client.post(url, {'users_list': users_list.pk}, follow=True)
        self.assertMessage(response, 'Lista inserita con successo')
        self.assertIn(users_list, self.category_1_str_1.allowed_users_lists.all())

        # add same list again
        response = self.client.post(url, {'users_list': users_list.pk}, follow=True)
        self.assertIn('Lista già selezionata', str(response.context['avviso']))

        # remove list
        remove_url = self.cat_url('manager_category_remove_ticket_users_list',
                                  list_id=users_list.pk)
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, 'rimossa correttamente')
        self.assertNotIn(users_list,
                         self.category_1_str_1.allowed_users_lists.all())

        # remove list again
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, 'La lista non è tra quelle presenti')

    def test_category_remove_office_not_competent(self):
        default_office = self.structure_1.get_default_office()
        response = self.client.get(self.cat_url('manager_remove_category_office',
                                                office_slug=default_office.slug),
                                   follow=True)
        self.assertMessage(response, 'non è di competenza di questo ufficio')
        self.category_1_str_1.refresh_from_db()
        self.assertTrue(self.category_1_str_1.is_active)

    def test_category_add_new_get(self):
        response = self.client.get(self.url('manager_category_add_new'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manager/category_add_new.html')

    def test_category_add_new_duplicate(self):
        count = TicketCategory.objects.count()
        response = self.client.post(self.url('manager_category_add_new'),
                                    {'name': self.category_1_str_1.name,
                                     'max_requests_per_user': 0},
                                    follow=True)
        self.assertMessage(response, 'Esiste già una tipologia di richiesta')
        self.assertEqual(TicketCategory.objects.count(), count)

    def test_category_add_new_protocol_required(self):
        response = self.client.post(self.url('manager_category_add_new'),
                                    {'name': 'Protocol category',
                                     'max_requests_per_user': 0,
                                     'protocol_required': True},
                                    follow=True)
        self.assertMessage(response, 'Prima di attivare il protocollo')
        category = TicketCategory.objects.get(name='Protocol category')
        self.assertFalse(category.protocol_required)

    def test_category_edit_get(self):
        response = self.client.get(self.cat_url('manager_category_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category_1_str_1)

    def test_category_edit_protocol_with_anonymous(self):
        response = self.client.post(self.cat_url('manager_category_edit'),
                                    {'name': 'edited',
                                     'max_requests_per_user': 0,
                                     'protocol_required': True,
                                     'allow_anonymous': True},
                                    follow=True)
        self.assertMessage(response, 'utenti anonimi')
        self.category_1_str_1.refresh_from_db()
        self.assertEqual(self.category_1_str_1.name, 'Category 1 Structure 1')
        self.assertFalse(self.category_1_str_1.allow_anonymous)

    def test_category_edit_protocol_without_configuration(self):
        response = self.client.post(self.cat_url('manager_category_edit'),
                                    {'name': 'edited',
                                     'max_requests_per_user': 0,
                                     'protocol_required': True},
                                    follow=True)
        self.assertMessage(response, 'Il protocollo non può essere attivato')
        self.category_1_str_1.refresh_from_db()
        self.assertEqual(self.category_1_str_1.name, 'edited')
        self.assertFalse(self.category_1_str_1.protocol_required)

    def test_category_disable_already_disabled(self):
        self.disable_category(self.structure_1.slug, self.category_1_str_1)
        response = self.client.get(self.cat_url('manager_disable_category'),
                                   follow=True)
        self.assertMessage(response, 'già disattivato')

    def test_category_enable_already_enabled(self):
        response = self.client.get(self.cat_url('manager_enable_category'),
                                   follow=True)
        self.assertMessage(response, 'già attivato')

    def test_category_enable_not_started(self):
        self.disable_category(self.structure_1.slug, self.category_1_str_1)
        TicketCategory.objects.filter(pk=self.category_1_str_1.pk).update(
            date_start=timezone.now() + timedelta(days=10)
        )
        response = self.client.get(self.cat_url('manager_enable_category'),
                                   follow=True)
        self.assertMessage(response, 'Data di inizio')
        self.category_1_str_1.refresh_from_db()
        self.assertTrue(self.category_1_str_1.is_active)
        self.assertFalse(self.category_1_str_1.is_started())

    def test_input_module_new_get(self):
        response = self.client.get(self.cat_url('manager_category_new_input_module'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category_1_str_1)

    def test_input_module_edit_get(self):
        response = self.client.get(self.cat_url('manager_category_input_module_edit',
                                                module_id=self.module_2.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['module'], self.module_2)

    def test_input_module_enable_already_enabled(self):
        response = self.client.get(self.cat_url('manager_category_input_module_enable',
                                                module_id=self.module_2.pk),
                                   follow=True)
        self.assertMessage(response, 'già attivato')

    def test_input_module_disable_and_delete_inactive(self):
        module = self.create_input_module_in_category(
            name='module 2',
            structure_slug=self.structure_1.slug,
            category_slug=self.category_1_str_1.slug
        )
        response = self.client.get(self.cat_url('manager_category_input_module_disable',
                                                module_id=module.pk),
                                   follow=True)
        self.assertMessage(response, 'già disattivato')
        # category is still active
        self.category_1_str_1.refresh_from_db()
        self.assertTrue(self.category_1_str_1.is_active)

        response = self.client.get(self.cat_url('manager_category_input_module_delete',
                                                module_id=module.pk),
                                   follow=True)
        self.assertMessage(response, 'eliminato con successo')
        self.assertFalse(TicketCategoryModule.objects.filter(pk=module.pk).exists())
        self.category_1_str_1.refresh_from_db()
        self.assertTrue(self.category_1_str_1.is_active)

    def test_input_module_add_existing_field(self):
        fields_count = TicketCategoryInputList.objects.filter(
            category_module=self.module_2).count()
        response = self.client.post(self.cat_url('manager_category_input_module',
                                                 module_id=self.module_2.pk),
                                    {'name': 'file_field_1',
                                     'field_type': 'CustomFileField'},
                                    follow=True)
        self.assertMessage(response, 'Esiste già un campo con questo nome')
        self.assertEqual(TicketCategoryInputList.objects.filter(
            category_module=self.module_2).count(), fields_count)

    def test_input_field_edit_get(self):
        response = self.client.get(self.cat_url('manager_category_input_field_edit',
                                                module_id=self.module_2.pk,
                                                field_id=self.input_field.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['field'], self.input_field)

    def test_condition_views(self):
        response = self.client.get(self.cat_url('manager_category_condition_new'))
        self.assertEqual(response.status_code, 200)

        condition = TicketCategoryCondition.objects.create(
            category=self.category_1_str_1,
            title='Condition',
            text='text',
            is_active=True
        )
        response = self.client.get(self.cat_url('manager_category_condition_edit',
                                                condition_id=condition.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['condition'], condition)

        response = self.client.get(self.cat_url('manager_category_condition_detail',
                                                condition_id=condition.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['condition'], condition)

        # enable active condition
        response = self.client.get(self.cat_url('manager_category_condition_enable',
                                                condition_id=condition.pk),
                                   follow=True)
        self.assertMessage(response, 'già attivata')

        # disable active condition
        response = self.client.get(self.cat_url('manager_category_condition_disable',
                                                condition_id=condition.pk),
                                   follow=True)
        self.assertMessage(response, 'disattivata con successo')
        condition.refresh_from_db()
        self.assertFalse(condition.is_active)

    def test_clone_preload_not_manager_of_selected_structure(self):
        response = self.client.get(
            self.cat_url('manager_category_input_module_clone_preload',
                         module_id=self.module_2.pk,
                         selected_structure_slug=self.structure_2.slug)
        )
        self.assertIn('Non sei un manager', str(response.context['avviso']))

    def test_clone_preload_select_structure(self):
        response = self.client.get(
            self.cat_url('manager_category_input_module_clone_preload',
                         module_id=self.module_2.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['my_structures'], [self.structure_1])
        self.assertEqual(response.context['categories'], [])

    def test_clone_not_manager_of_selected_structure(self):
        modules_count = TicketCategoryModule.objects.count()
        response = self.client.get(
            self.cat_url('manager_category_input_module_clone',
                         module_id=self.module_2.pk,
                         selected_structure_slug=self.structure_2.slug,
                         selected_category_slug=self.category_1_str_2.slug)
        )
        self.assertIn('Non sei un manager', str(response.context['avviso']))
        self.assertEqual(TicketCategoryModule.objects.count(), modules_count)

    def test_clone_module_with_fields(self):
        response = self.client.get(
            self.cat_url('manager_category_input_module_clone',
                         module_id=self.module_2.pk,
                         selected_structure_slug=self.structure_1.slug,
                         selected_category_slug=self.category_1_str_1.slug),
            follow=True
        )
        self.assertMessage(response, 'clonato con successo')
        new_module = TicketCategoryModule.objects.filter(
            ticket_category=self.category_1_str_1
        ).exclude(pk=self.module_2.pk).get()
        self.assertTrue(TicketCategoryInputList.objects.filter(
            category_module=new_module, name='file_field_1').exists())

    def test_default_reply_views(self):
        response = self.client.get(self.cat_url('manager_category_default_reply_new'))
        self.assertEqual(response.status_code, 200)

        reply = TicketCategoryDefaultReply.objects.create(
            ticket_category=self.category_1_str_1,
            text='reply',
            is_active=True
        )
        response = self.client.get(self.cat_url('manager_category_default_reply_enable',
                                                default_reply_id=reply.pk),
                                   follow=True)
        self.assertMessage(response, 'già attivata')

        response = self.client.get(self.cat_url('manager_category_default_reply_disable',
                                                default_reply_id=reply.pk),
                                   follow=True)
        self.assertMessage(response, 'disattivata con successo')
        response = self.client.get(self.cat_url('manager_category_default_reply_disable',
                                                default_reply_id=reply.pk),
                                   follow=True)
        self.assertMessage(response, 'già disattivata')
        reply.refresh_from_db()
        self.assertFalse(reply.is_active)

        response = self.client.get(self.cat_url('manager_category_default_reply_detail',
                                                default_reply_id=reply.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['default_reply'], reply)

    def test_protocol_configuration_views(self):
        response = self.client.get(
            self.cat_url('manager_category_protocol_configuration_new')
        )
        self.assertEqual(response.status_code, 200)

        configuration = TicketCategoryWSProtocollo.objects.create(
            ticket_category=self.category_1_str_1,
            name='Conf',
            protocollo_cod_titolario='1/1',
            protocollo_fascicolo_numero='1',
        )
        self.assertFalse(configuration.is_active)

        disable_url = self.cat_url('manager_category_protocol_configuration_disable',
                                   configuration_id=configuration.pk)
        enable_url = self.cat_url('manager_category_protocol_configuration_enable',
                                  configuration_id=configuration.pk)

        response = self.client.get(disable_url, follow=True)
        self.assertMessage(response, 'già disattivata')

        response = self.client.get(enable_url, follow=True)
        self.assertMessage(response, 'attivata con successo')
        configuration.refresh_from_db()
        self.assertTrue(configuration.is_active)

        response = self.client.get(enable_url, follow=True)
        self.assertMessage(response, 'già attivata')

        response = self.client.get(
            self.cat_url('manager_category_protocol_configuration_detail',
                         configuration_id=configuration.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['configuration'], configuration)

    def test_check_protocol_success(self):
        with mock.patch('uni_ticket.views.manager.ticket_protocol') as protocol:
            response = self.client.get(self.url('manager_user_settings_check_protocol'),
                                       follow=True)
        protocol.assert_called_once()
        self.assertTrue(protocol.call_args.kwargs['test'])
        self.assertMessage(response, 'ha risposto correttamente')

    def test_check_protocol_error(self):
        with mock.patch('uni_ticket.views.manager.ticket_protocol',
                        side_effect=Exception('protocol down')):
            response = self.client.get(self.url('manager_user_settings_check_protocol'),
                                       follow=True)
        self.assertMessage(response, 'protocol down')


class Test_ManagerTaskViews(ManagerViewsMixin, BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.structure_1_manager_login()

    def test_task_new_get(self):
        response = self.client.get(self.cat_url('manager_category_task_new'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category_1_str_1)

    def test_task_with_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        attachment = SimpleUploadedFile('task.pdf', b'%PDF-1.4 content',
                                        content_type='application/pdf')
        response = self.client.post(self.cat_url('manager_category_task_new'),
                                    {'subject': 'Task',
                                     'description': 'Task description',
                                     'priority': 0,
                                     'ordering': 10,
                                     'attachment': attachment},
                                    follow=True)
        self.assertMessage(response, 'Attività creata con successo')
        task = TicketCategoryTask.objects.get(category=self.category_1_str_1,
                                              subject='Task')
        self.assertTrue(task.attachment)

        # detail
        response = self.client.get(self.cat_url('manager_category_task_detail',
                                                task_id=task.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['task'], task)

        # download attachment
        response = self.client.get(self.cat_url('category_task_download_attachment',
                                                task_id=task.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'%PDF-1.4 content')

        # edit form hides attachment field
        response = self.client.get(self.cat_url('manager_category_task_edit',
                                                task_id=task.code))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('attachment', response.context['form'].fields)
        self.assertEqual(list(response.context['allegati'].values()), ['task.pdf'])

        # delete attachment
        response = self.client.get(self.cat_url('category_task_attachment_delete',
                                                task_id=task.code),
                                   follow=True)
        self.assertMessage(response, 'eliminato')
        task.refresh_from_db()
        self.assertFalse(task.attachment)

        # download without attachment
        response = self.client.get(self.cat_url('category_task_download_attachment',
                                                task_id=task.code))
        self.assertEqual(response.status_code, 404)

    def test_task_enable_disable_twice(self):
        task = TicketCategoryTask.objects.create(category=self.category_1_str_1,
                                                 subject='Task',
                                                 description='descr',
                                                 code='task-code',
                                                 created_by=self.staff_1,
                                                 is_active=False)
        response = self.client.get(self.cat_url('manager_category_task_disable',
                                                task_id=task.code),
                                   follow=True)
        self.assertMessage(response, 'già disattivata')

        task.is_active = True
        task.save()
        response = self.client.get(self.cat_url('manager_category_task_enable',
                                                task_id=task.code),
                                   follow=True)
        self.assertMessage(response, 'già attivata')


class Test_ManagerSettingsViews(ManagerViewsMixin, BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    def test_add_manager(self):
        url = self.url('manager_user_settings_add_manager')

        response = self.client.get(url, {'search': 'User 1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['key'], 'User 1')

        # user_1 is already an operator of the default office
        response = self.client.post(url, {'user': self.user_1.pk}, follow=True)
        self.assertMessage(response, 'Manager creato con successo')
        self.assertTrue(UserManageOrganizationalStructure.objects.filter(
            user=self.user_1, organizational_structure=self.structure_1).exists())

        # again
        response = self.client.post(url, {'user': self.user_1.pk}, follow=True)
        self.assertIn('Manager già assegnato', str(response.context['avviso']))

    def test_add_manager_not_in_default_office(self):
        user = self.create_user(name='User 3')
        response = self.client.post(self.url('manager_user_settings_add_manager'),
                                    {'user': user.pk}, follow=True)
        self.assertMessage(response, 'Manager creato con successo')
        default_office = self.structure_1.get_default_office()
        self.assertTrue(OrganizationalStructureOfficeEmployee.objects.filter(
            employee=user, office=default_office).exists())
        self.assertIn(user.pk,
                      self.structure_1.get_structure_managers().values_list('user', flat=True))

    def test_alerts(self):
        response = self.client.get(self.url('manager_structure_alert_new'))
        self.assertEqual(response.status_code, 200)

        # create
        response = self.client.post(self.url('manager_structure_alert_new'),
                                    {'name': 'Alert',
                                     'text': 'Alert text',
                                     'ordinamento': 0,
                                     'is_active': True},
                                    follow=True)
        self.assertMessage(response, 'Alert creato con successo')
        alert = OrganizationalStructureAlert.objects.get(
            organizational_structure=self.structure_1, name='Alert')
        self.assertTrue(alert.is_active)

        # edit
        edit_url = self.url('manager_structure_alert_edit', alert_id=alert.pk)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(edit_url,
                                    {'name': 'Alert',
                                     'text': '<b>New text</b>',
                                     'ordinamento': 1},
                                    follow=True)
        self.assertMessage(response, 'Alert modificato con successo')
        alert.refresh_from_db()
        self.assertEqual(alert.text, 'New text')
        self.assertFalse(alert.is_active)

        # delete
        response = self.client.get(self.url('manager_structure_alert_delete',
                                            alert_id=alert.pk),
                                   follow=True)
        self.assertMessage(response, 'eliminato correttamente')
        self.assertFalse(OrganizationalStructureAlert.objects.filter(
            pk=alert.pk).exists())

    def test_users_lists(self):
        response = self.client.get(self.url('manager_structure_users_list_new'))
        self.assertEqual(response.status_code, 200)

        # create
        response = self.client.post(self.url('manager_structure_users_list_new'),
                                    {'name': 'List', 'description': 'descr'},
                                    follow=True)
        self.assertMessage(response, 'Lista creata con successo')
        users_list = OrganizationalStructureAllowedUsersList.objects.get(
            organizational_structure=self.structure_1, name='List')

        # edit
        edit_url = self.url('manager_structure_users_list_edit',
                            list_id=users_list.pk)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(edit_url,
                                    {'name': 'List edited', 'description': ''},
                                    follow=True)
        self.assertMessage(response, 'Lista modificata con successo')
        users_list.refresh_from_db()
        self.assertEqual(users_list.name, 'List edited')

        # add user
        add_url = self.url('manager_structure_users_list_add_user',
                           list_id=users_list.pk)
        response = self.client.get(add_url, {'search': 'User 2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([u['pk'] for u in response.context['users']],
                         [self.user_2.pk])
        response = self.client.post(add_url, {'user': self.user_2.pk}, follow=True)
        self.assertMessage(response, 'Utente inserito con successo')
        self.assertIn(self.user_2, users_list.allowed_users.all())

        # add user again
        response = self.client.post(add_url, {'user': self.user_2.pk}, follow=True)
        self.assertIn('Utente già selezionato', str(response.context['avviso']))

        # remove user
        remove_url = self.url('manager_structure_users_list_remove',
                              list_id=users_list.pk,
                              user_id=self.user_2.pk)
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, 'rimosso correttamente')
        self.assertNotIn(self.user_2, users_list.allowed_users.all())

        # remove user again
        response = self.client.get(remove_url, follow=True)
        self.assertMessage(response, 'non è tra quelli abilitati')

        # delete
        response = self.client.get(self.url('manager_structure_users_list_delete',
                                            list_id=users_list.pk),
                                   follow=True)
        self.assertMessage(response, 'eliminata correttamente')
        self.assertFalse(OrganizationalStructureAllowedUsersList.objects.filter(
            pk=users_list.pk).exists())


class Test_ManagerViewsWithTickets(ManagerViewsMixin, BaseTicketEnvironment):
    """
    Operations denied because of existing tickets
    """

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    def test_office_disable_with_tickets(self):
        response = self.client.get(self.url('manager_disable_office',
                                            office_slug=self.office_1_str_1.slug),
                                   follow=True)
        self.assertMessage(response, 'Alcuni ticket potrebbero rimanere privi')
        self.office_1_str_1.refresh_from_db()
        self.assertTrue(self.office_1_str_1.is_active)

    def test_office_delete_with_tickets(self):
        response = self.client.get(self.url('manager_delete_office',
                                            office_slug=self.office_1_str_1.slug),
                                   follow=True)
        self.assertMessage(response, 'Ci sono ticket assegnati')
        self.assertTrue(OrganizationalStructureOffice.objects.filter(
            pk=self.office_1_str_1.pk).exists())

    def test_category_delete_with_tickets(self):
        response = self.client.get(self.cat_url('manager_delete_category'),
                                   follow=True)
        self.assertMessage(response, 'Ci sono ticket assegnati')
        self.assertTrue(TicketCategory.objects.filter(
            pk=self.category_1_str_1.pk).exists())

    def test_input_module_delete_with_tickets(self):
        response = self.client.get(self.cat_url('manager_category_input_module_delete',
                                                module_id=self.module_2.pk),
                                   follow=True)
        self.assertMessage(response, 'Ci sono delle richieste collegate')
        self.assertTrue(TicketCategoryModule.objects.filter(
            pk=self.module_2.pk).exists())

    def test_input_module_add_field_with_tickets(self):
        response = self.client.post(self.cat_url('manager_category_input_module',
                                                 module_id=self.module_2.pk),
                                    {'name': 'new field',
                                     'field_type': 'CustomCharField'},
                                    follow=True)
        self.assertMessage(response, 'Impossibile modificare il modulo')
        self.assertFalse(TicketCategoryInputList.objects.filter(
            category_module=self.module_2, name='new field').exists())

    def test_input_field_delete_with_tickets(self):
        response = self.client.get(self.cat_url('manager_category_input_field_delete',
                                                module_id=self.module_2.pk,
                                                field_id=self.input_field.pk),
                                   follow=True)
        self.assertMessage(response, 'Ci sono delle richieste collegate')
        self.assertTrue(TicketCategoryInputList.objects.filter(
            pk=self.input_field.pk).exists())

    def test_input_field_edit_with_tickets(self):
        response = self.client.post(self.cat_url('manager_category_input_field_edit',
                                                 module_id=self.module_2.pk,
                                                 field_id=self.input_field.pk),
                                    {'name': 'edited',
                                     'field_type': 'CustomFileField'},
                                    follow=True)
        self.assertMessage(response, 'Impossibile modificare il campo')
        self.input_field.refresh_from_db()
        self.assertEqual(self.input_field.name, 'file_field_1')

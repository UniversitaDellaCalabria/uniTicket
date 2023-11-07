import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_category_office_env import BaseCategoryOfficeEnvironment


logger = logging.getLogger('my_logger')


class Test_ManagerFunctions(BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    def test_user_ismanager(self):
        # self.staff1 is a staff user
        assert user_is_manager(self.staff_1, self.structure_1)

    def test_user_is_not_manager(self):
        # self.user1 is not a staff user
        self.assertFalse(user_is_manager(self.user_1, self.structure_1))

    def test_edit_category(self):
        # Edit
        name = 'new name'
        params =  {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.category_1_str_1.refresh_from_db()
        assert self.category_1_str_1.name == name

    def test_same_name_other(self):
        # Edit with same name (fails!)
        new_cat = self.add_new_category(cat_name='Category 2 Structure 1',
                                        structure_slug=self.structure_1.slug)
        name = 'Category 1 Structure 1'
        params =  {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': new_cat.slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        new_cat.refresh_from_db()
        self.assertFalse(new_cat.name == name)

    def test_delete_category(self):
        # Delete (no ticket linked, success!)
        response = self.client.get(reverse('uni_ticket:manager_delete_category',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketCategory.objects.filter(organizational_structure__slug=self.structure_1.slug))

    def test_category_field_edit(self):
        # Edit input module field
        field_name = 'file_field_1 edited'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': True}
        response = self.client.post(reverse('uni_ticket:manager_category_input_field_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'field_id': self.input_field.pk}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        self.input_field.refresh_from_db()
        assert self.input_field.name == field_name

    def test_category_field_remove(self):
        # Remove field
        response = self.client.get(reverse('uni_ticket:manager_category_input_field_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'field_id': self.input_field.pk}),
                                    follow=True)
        assert response.status_code == 200
        assert not TicketCategoryInputList.objects.filter(category_module=self.module_2).first()

    def test_remove_category_from_office_competences(self):
        # Remove category from office competences
        response = self.client.get(reverse('uni_ticket:manager_remove_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1_str_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    follow=True)
        assert response.status_code == 200
        self.category_1_str_1.refresh_from_db()
        self.assertFalse(self.category_1_str_1.is_active)
        self.assertFalse(self.category_1_str_1.organizational_office == self.office_1_str_1)

    def test_remove_office_from_category(self):
        # Remove category from office competences
        response = self.client.get(reverse('uni_ticket:manager_remove_category_office',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'office_slug': self.office_1_str_1.slug}),
                                    follow=True)
        assert response.status_code == 200
        self.category_1_str_1.refresh_from_db()
        self.assertFalse(self.category_1_str_1.is_active)
        self.assertFalse(self.category_1_str_1.organizational_office == self.office_1_str_1)

    def test_disable_input_module(self):
        # Disable input module and category
        response = self.client.get(reverse('uni_ticket:manager_category_input_module_disable',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug,
                                                   'module_id': self.module_2.pk}),
                                   follow=True)
        assert response.status_code == 200
        self.module_2.refresh_from_db()
        self.assertFalse(self.module_2.is_active)
        self.category_1_str_1.refresh_from_db()
        self.assertFalse(self.category_1_str_1.is_active)

    def test_edit_input_module(self):
        # Edit
        new_name = 'edited input module'
        new_params = {'name': new_name,}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk}),
                                    new_params,
                                    follow=True)
        assert response.status_code == 200
        self.module_2.refresh_from_db()
        assert self.module_2.name == new_name

    def test_clone_input_module_preload(self):
        # Edit
        response = self.client.get(reverse('uni_ticket:manager_category_input_module_clone_preload',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'selected_structure_slug': self.structure_1.slug,
                                                    'selected_category_slug': self.category_1_str_1.slug}),
                                    follow=True)
        assert response.status_code == 200

    def test_clone_input_module(self):
        # Edit
        response = self.client.get(reverse('uni_ticket:manager_category_input_module_clone',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,
                                                    'selected_structure_slug': self.structure_1.slug,
                                                    'selected_category_slug': self.category_1_str_1.slug}),
                                    follow=True)
        assert response.status_code == 200

    def test_delete_input_module(self):
        # Delete
        pk = self.module_2.pk
        response = self.client.get(reverse('uni_ticket:manager_category_input_module_delete',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug,
                                                   'module_id': self.module_2.pk}),
                                   follow=True)
        assert response.status_code == 200
        self.assertFalse(TicketCategoryModule.objects.filter(pk=pk))
        self.category_1_str_1.refresh_from_db()
        self.assertFalse(self.category_1_str_1.is_active)

    def test_offices(self):
        response = self.client.get(reverse('uni_ticket:manager_offices',
                                           kwargs={'structure_slug': self.structure_1.slug,}),
                                   follow=False)
        assert response.status_code == 200
        assert response.context['offices']

    def test_categories(self):
        response = self.client.get(reverse('uni_ticket:manager_categories',
                                           kwargs={'structure_slug': self.structure_1.slug,}),
                                   follow=False)
        assert response.status_code == 200
        assert response.context['categories']

    def test_category_condition(self):
        # Create
        title = 'Condition 1'
        text = 'Example text'
        params = {'title': title,
                  'text': text,
                  'is_active': True}
        response = self.client.post(reverse('uni_ticket:manager_category_condition_new',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    params,
                                    follow=True)
        condition = TicketCategoryCondition.objects.get(category=self.category_1_str_1,
                                                        title=title)
        assert response.status_code == 200
        assert condition
        assert condition.is_active

        # Edit
        new_title = 'Condition 3'
        new_text = 'Example text 3'
        new_params = {'title': new_title,
                      'text': new_text}
        response = self.client.post(reverse('uni_ticket:manager_category_condition_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'condition_id': condition.pk}),
                                    new_params,
                                    follow=True)
        assert response.status_code == 200
        condition.refresh_from_db()
        assert condition.title=='Condition 3'
        assert condition.text=='Example text 3'

        # Disable
        response = self.client.get(reverse('uni_ticket:manager_category_condition_disable',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug,
                                                   'condition_id': condition.pk}),
                                   follow=True)
        assert response.status_code == 200
        condition.refresh_from_db()
        assert not condition.is_active

        # Enable
        response = self.client.get(reverse('uni_ticket:manager_category_condition_enable',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug,
                                                   'condition_id': condition.pk}),
                                   follow=True)
        assert response.status_code == 200
        condition.refresh_from_db()
        assert condition.is_active

        # Delete
        response = self.client.get(reverse('uni_ticket:manager_category_condition_delete',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1_str_1.slug,
                                                   'condition_id': condition.pk}),
                                   follow=True)
        assert response.status_code == 200
        condition = TicketCategoryCondition.objects.filter(category=self.category_1_str_1,
                                                           title=title)
        assert not condition

    def test_edit_office(self):
        # Edit office
        new_name = 'Office 1 Edited'
        new_descr = 'Description office 1 edited'
        new_params = {'name': new_name,
                      'description': new_descr}
        response = self.client.post(reverse('uni_ticket:manager_office_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1_str_1.slug}),
                                    new_params,
                                    follow=True)
        assert response.status_code == 200
        self.office_1_str_1.refresh_from_db()
        assert self.office_1_str_1.name == new_name
        assert self.office_1_str_1.description == new_descr

    def test_add_office_operator(self):
        # Enable office
        response = self.client.get(reverse('uni_ticket:manager_enable_office',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'office_slug': self.office_1_str_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        self.office_1_str_1.refresh_from_db()

        # Add office operator
        new_params = {'user': self.user_1.pk,
                      'description': 'operatore'}
        response = self.client.post(reverse('uni_ticket:manager_add_office_operator',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1_str_1.slug}),
                                    new_params,
                                    follow=True)
        assert response.status_code == 200
        assert user_is_operator(self.user_1, self.structure_1)
        assert user_manage_office(self.user_1, self.office_1_str_1)

        # Remove office operator
        response = self.client.get(reverse('uni_ticket:manager_remove_office_operator',
                                   kwargs={'structure_slug': self.structure_1.slug,
                                           'office_slug': self.office_1_str_1.slug,
                                           'employee_id': self.user_1.pk}),
                         follow=True)
        assert response.status_code == 200
        osoe = OrganizationalStructureOfficeEmployee.objects.filter(office=self.office_1_str_1,
                                                                    employee=self.user_1).first()
        assert not osoe
        # User1 is an employee of generic "help desk" office
        # he can view all tickets
        assert user_is_operator(self.user_1, self.structure_1)
        assert user_manage_office(self.user_1, self.office_1_str_1)

    def test_delete_office(self):
        # Delete office
        response = self.client.get(reverse('uni_ticket:manager_delete_office',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'office_slug': self.office_1_str_1.slug}),
                                   follow=True)
        office_deleted = OrganizationalStructureOffice.objects.filter(name='Office 1',
                                                                      organizational_structure=self.structure_1)
        assert response.status_code == 200
        assert not office_deleted

    def test_category_protocol_configuration(self):
        # Create
        name = 'Conf test 1'
        protocollo_uo_rpa = 'test uo rpa'
        protocollo_uo_rpa_username = '111'
        protocollo_fascicolo_numero = 1
        protocollo_fascicolo_anno = 2020

        if settings.PROTOCOL_PACKAGE == 'titulus_ws':
            params = {'name': name,
                      'protocollo_uo': '0',
                      'protocollo_uo_rpa': protocollo_uo_rpa,
                      'protocollo_uo_rpa_username': protocollo_uo_rpa_username,
                      'protocollo_cod_titolario': '1/1',
                      'protocollo_fascicolo_numero': protocollo_fascicolo_numero}
        elif settings.PROTOCOL_PACKAGE == 'archi_pro':
            params = {'name': name,
                      'protocollo_uo': '0',
                      'protocollo_cod_titolario': '1/1',
                      'protocollo_fascicolo_numero': protocollo_fascicolo_numero,
                      'protocollo_fascicolo_anno': protocollo_fascicolo_anno}

        response = self.client.post(reverse('uni_ticket:manager_category_protocol_configuration_new',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    params,
                                    follow=True)

        configuration = TicketCategoryWSProtocollo.objects.get(ticket_category=self.category_1_str_1, name=name)
        assert response.status_code == 200
        assert configuration
        assert not configuration.is_active

        # Edit
        new_name = 'Conf test 1 - edited'

        params['name'] = new_name

        response = self.client.post(reverse('uni_ticket:manager_category_protocol_configuration_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'configuration_id': configuration.pk}),
                                    params,
                                    follow=True)

        assert response.status_code == 200

        configuration.refresh_from_db()
        assert configuration.name == new_name
        # assert condition.is_active

        #Enable
        response = self.client.get(reverse('uni_ticket:manager_category_protocol_configuration_enable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'configuration_id': configuration.pk}),
                                    follow=True)

        assert response.status_code == 200

        configuration.refresh_from_db()
        assert configuration.is_active

        #Disable
        response = self.client.get(reverse('uni_ticket:manager_category_protocol_configuration_disable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'configuration_id': configuration.pk}),
                                    follow=True)

        assert response.status_code == 200

        configuration.refresh_from_db()
        assert not configuration.is_active

        #Delete
        response = self.client.get(reverse('uni_ticket:manager_category_protocol_configuration_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'configuration_id': configuration.pk}),
                                    follow=True)

        assert response.status_code == 200
        assert not TicketCategoryWSProtocollo.objects.filter(ticket_category=self.category_1_str_1,
                                                           name=new_name)

    def test_category_default_reply(self):
        # Create
        text = 'Default reply'

        params = {'text': text}

        response = self.client.post(reverse('uni_ticket:manager_category_default_reply_new',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    params,
                                    follow=True)
        reply = TicketCategoryDefaultReply.objects.get(ticket_category=self.category_1_str_1,
                                                       text=text)
        assert response.status_code == 200
        assert reply
        assert reply.is_active

        # Edit
        new_text = 'Default reply - edited'

        params = {'text': new_text}

        response = self.client.post(reverse('uni_ticket:manager_category_default_reply_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'default_reply_id': reply.pk}),
                                    params,
                                    follow=True)

        assert response.status_code == 200

        reply.refresh_from_db()
        assert reply.text == new_text
        # assert condition.is_active

        #Disable
        response = self.client.get(reverse('uni_ticket:manager_category_default_reply_disable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'default_reply_id': reply.pk}),
                                    follow=True)

        assert response.status_code == 200

        reply.refresh_from_db()
        assert not reply.is_active

        #Enable
        response = self.client.get(reverse('uni_ticket:manager_category_default_reply_enable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'default_reply_id': reply.pk}),
                                    follow=True)

        assert response.status_code == 200

        reply.refresh_from_db()
        assert reply.is_active

        #Delete
        response = self.client.get(reverse('uni_ticket:manager_category_default_reply_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'default_reply_id': reply.pk}),
                                    follow=True)

        assert response.status_code == 200
        assert not TicketCategoryDefaultReply.objects.filter(ticket_category=self.category_1_str_1,
                                                           text=new_text)

    def test_category_task(self):
        # Create
        subject = 'Category task'
        description = 'Task description'

        params = {'subject': subject,
                  'description': description,
                  'priority': 0}

        response = self.client.post(reverse('uni_ticket:manager_category_task_new',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug}),
                                    params,
                                    follow=True)
        task = TicketCategoryTask.objects.get(category=self.category_1_str_1,
                                              subject=subject)
        assert response.status_code == 200
        assert task
        assert not task.is_active

        # Edit
        new_priority = 2

        params = {'subject': subject,
                  'description': description,
                  'priority': new_priority}

        response = self.client.post(reverse('uni_ticket:manager_category_task_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'task_id': task.code}),
                                    params,
                                    follow=True)

        assert response.status_code == 200

        task.refresh_from_db()
        assert task.priority == new_priority
        # assert condition.is_active

        #Enable
        response = self.client.get(reverse('uni_ticket:manager_category_task_enable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'task_id': task.code}),
                                    follow=True)

        assert response.status_code == 200

        task.refresh_from_db()
        assert task.is_active

        #Disable
        response = self.client.get(reverse('uni_ticket:manager_category_task_disable',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'task_id': task.code}),
                                    follow=True)

        assert response.status_code == 200

        task.refresh_from_db()
        assert not task.is_active

        #Delete
        response = self.client.get(reverse('uni_ticket:manager_category_task_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'task_id': task.code}),
                                    follow=True)

        assert response.status_code == 200
        assert not TicketCategoryTask.objects.filter(category=self.category_1_str_1,
                                                     subject=subject)

    def test_structure_protocol_configuration_detail(self):
        response = self.client.get(reverse('uni_ticket:manager_structure_protocol_configuration_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'configuration_id': self.structure_1_protocol_conf.pk}),
                                   follow=True)
        assert response.status_code == 200

    def test_category_module_preview(self):
        params = {'ticket_subject': "subject",
                  'ticket_description': "description"}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module_preview',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1_str_1.slug,
                                                    'module_id': self.module_2.pk,}),
                                    params,
                                   follow=True)
        assert response.status_code == 200

    def test_manager_settings(self):
        response = self.client.get(reverse('uni_ticket:manager_user_settings',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                   follow=True)
        assert response.status_code == 200

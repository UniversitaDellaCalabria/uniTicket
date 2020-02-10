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
        new_name = 'new module name'
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
        new_params = {'operatore': self.user_1.pk,
                      'description': 'operatore'}
        response = self.client.post(reverse('uni_ticket:manager_office_detail',
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


import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_category_env import BaseCategoryEnvironment


logger = logging.getLogger('my_logger')


class Test_ManagerFunctions(BaseCategoryEnvironment):

    def setUp(self):
        super().setUp()

        # Create category 2
        cat_name = 'Category 2'
        params = {'name': cat_name,
                  'description': 'Description category 2',
                  'allow_employee': True,
                  'allow_user': True,
                  'allow_guest': True}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    params,
                                    follow=True)
        self.category_2 = TicketCategory.objects.get(name=cat_name)

        # Create Office 1
        # Create a new office in Structure 1
        off_name = 'Office 1'
        params = {'name': off_name,
                  'description': 'Description office 1'}
        response = self.client.post(reverse('uni_ticket:manager_office_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug,}),
                                    params,
                                    follow=True)
        self.office_1 = OrganizationalStructureOffice.objects.get(name=off_name)
        assert response.status_code == 200

    def test_user_ismanager(self):
        # self.staff1 is a staff user
        assert user_is_manager(self.staff_1, self.structure_1)

    def test_user_is_not_manager(self):
        # self.user1 is not a staff user
        check_manager = user_is_manager(self.user_1, self.structure_1)
        assert not check_manager

    def test_enable_empty_category(self):
        # Enable category without input modules (fails!)
        self.client.get(reverse('uni_ticket:manager_enable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_2.slug}),
                         follow=True)
        self.category_2.refresh_from_db()
        assert not self.category_2.is_active

    def test_disable_category(self):
        # Disable category
        self.client.get(reverse('uni_ticket:manager_disable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug}),
                        follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.is_active

    def test_edit_category(self):
        # Edit
        name = 'new name'
        params =  {'name': name,}
        self.client.post(reverse('uni_ticket:manager_category_edit',
                                 kwargs={'structure_slug': self.structure_1.slug,
                                         'category_slug': self.category_1.slug}),
                         params,
                         follow=True)
        self.category_1.refresh_from_db()
        assert self.category_1.name == name

    def test_edit_category_same_name_other(self):
        # Edit with same name (fails!)
        name = 'Category 2'
        params =  {'name': name,}
        self.client.post(reverse('uni_ticket:manager_category_edit',
                                 kwargs={'structure_slug': self.structure_1.slug,
                                         'category_slug': self.category_1.slug}),
                         params,
                         follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.name == name

    def test_delete_category(self):
        # Delete (no ticket linked, success!)
        name = 'Category 2'
        self.client.get(reverse('uni_ticket:manager_delete_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_2.slug}),
                         follow=True)
        assert not TicketCategory.objects.filter(name=name)

    def test_category_field_edit(self):
        # Edit input module field
        field_name = 'file_field_1 edited'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': True}
        response = self.client.post(reverse('uni_ticket:manager_category_input_field_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk,
                                                    'field_id': self.input_field.pk}),
                                    params,
                                    follow=True)
        self.input_field.refresh_from_db()
        assert self.input_field.name == field_name

    def test_category_field_remove(self):
        # Remove field
        response = self.client.get(reverse('uni_ticket:manager_category_input_field_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk,
                                                    'field_id': self.input_field.pk}),
                                    follow=True)
        assert not TicketCategoryInputList.objects.filter(category_module=self.module).first()

    def test_add_inactive_category_in_office_competences(self):
        # Add category in office competences
        # Category must be enabled (fails!)
        params = {'category': self.category_2.pk,}
        response = self.client.post(reverse('uni_ticket:manager_add_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug}),
                                    params,
                                    follow=True)
        self.category_2.refresh_from_db()
        assert not self.category_1.organizational_office == self.office_1

    def test_add_active_category_in_office_competences(self):
        # Add category in office competences
        # Category must be enabled (now is ok!)
        params = {'category': self.category_1.pk,}
        response = self.client.post(reverse('uni_ticket:manager_add_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug}),
                                    params,
                                    follow=True)
        self.category_1.refresh_from_db()
        assert self.category_1.organizational_office == self.office_1

    def test_remove_category_from_office_competences(self):
        # Remove category from office competences
        # Category must be enabled (now is ok!)
        response = self.client.get(reverse('uni_ticket:manager_remove_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.organizational_office == self.office_1

    def test_disable_input_module(self):
        # Disable input module and category
        self.client.get(reverse('uni_ticket:manager_category_input_module_disable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': self.module.pk}),
                        follow=True)
        self.module.refresh_from_db()
        assert not self.module.is_active
        assert not self.category_1.is_active

    def test_edit_input_module(self):
        # Edit
        new_name = 'new module name'
        new_params = {'name': new_name,}
        self.client.post(reverse('uni_ticket:manager_category_input_module_edit',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': self.module.pk}),
                        new_params,
                        follow=True)
        self.module.refresh_from_db()
        assert self.module.name == new_name

    def test_delete_input_module(self):
        # Delete
        pk = self.module.pk
        self.client.get(reverse('uni_ticket:manager_category_input_module_delete',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': self.module.pk}),
                        follow=True)
        assert not TicketCategoryModule.objects.filter(pk=pk)
        assert not self.category_1.is_active

    def test_offices(self):
        response = self.client.get(reverse('uni_ticket:manager_offices',
                                           kwargs={'structure_slug': self.structure_1.slug,}),
                                   follow=False)
        assert response.context['offices']

    def test_categories(self):
        response = self.client.get(reverse('uni_ticket:manager_categories',
                                           kwargs={'structure_slug': self.structure_1.slug,}),
                                   follow=False)
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
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        condition = TicketCategoryCondition.objects.get(category=self.category_1,
                                                        title=title)
        assert response.status_code == 200
        assert condition
        assert condition.is_active

        # Edit
        new_title = 'Condition 3'
        new_text = 'Example text 3'
        new_params = {'title': new_title,
                      'text': new_text}
        self.client.post(reverse('uni_ticket:manager_category_condition_edit',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'condition_id': condition.pk}),
                        new_params,
                        follow=True)
        condition.refresh_from_db()
        assert condition.title=='Condition 3'
        assert condition.text=='Example text 3'

        # Disable
        self.client.get(reverse('uni_ticket:manager_category_condition_disable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'condition_id': condition.pk}),
                        follow=True)
        condition.refresh_from_db()
        assert not condition.is_active

        # Enable
        self.client.get(reverse('uni_ticket:manager_category_condition_enable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'condition_id': condition.pk}),
                        follow=True)
        condition.refresh_from_db()
        assert condition.is_active

        # Delete
        self.client.get(reverse('uni_ticket:manager_category_condition_delete',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'condition_id': condition.pk}),
                        follow=True)
        condition = TicketCategoryCondition.objects.filter(category=self.category_1,
                                                           title=title)
        assert not condition

    def test_add_inactive_office_in_category_competences(self):
        # Add office in category competences
        # Category must be enabled (now is ok!)
        params = {'office': self.office_1.pk,}
        response = self.client.post(reverse('uni_ticket:manager_category_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.organizational_office == self.office_1

    def test_enable_office_and_assignment(self):
        # Enable office
        self.client.get(reverse('uni_ticket:manager_enable_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        self.office_1.refresh_from_db()
        assert self.office_1.is_active

        # Add office in category competences
        # Category must be enabled (now is ok!)
        params = {'office': self.office_1.pk,}
        response = self.client.post(reverse('uni_ticket:manager_category_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        self.category_1.refresh_from_db()
        assert self.category_1.organizational_office == self.office_1

        # Remove office from category competences
        # Category must be enabled (now is ok!)
        response = self.client.get(reverse('uni_ticket:manager_remove_category_office',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1.slug,
                                                   'office_slug': self.office_1.slug}),
                                   follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.organizational_office == self.office_1

        # Disable office
        self.client.get(reverse('uni_ticket:manager_disable_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        self.office_1.refresh_from_db()
        assert not self.office_1.is_active

    def test_edit_office(self):
        # Edit office
        new_name = 'Office 1 Edited'
        new_descr = 'Description office 1 edited'
        new_params = {'name': new_name,
                      'description': new_descr}
        self.client.post(reverse('uni_ticket:manager_office_edit',
                                 kwargs={'structure_slug': self.structure_1.slug,
                                         'office_slug': self.office_1.slug}),
                         new_params,
                         follow=True)
        self.office_1.refresh_from_db()
        assert self.office_1.name == new_name
        assert self.office_1.description == new_descr

    def test_add_office_operator(self):
        # Enable office
        self.client.get(reverse('uni_ticket:manager_enable_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        self.office_1.refresh_from_db()

        # Add office operator
        new_params = {'operatore': self.user_1.pk,
                      'description': 'operatore'}
        response = self.client.post(reverse('uni_ticket:manager_office_detail',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug}),
                                    new_params,
                                    follow=True)
        assert user_is_operator(self.user_1, self.structure_1)
        assert user_is_office_operator(self.user_1, self.office_1)

        # Remove office operator
        response = self.client.get(reverse('uni_ticket:manager_remove_office_operator',
                                   kwargs={'structure_slug': self.structure_1.slug,
                                           'office_slug': self.office_1.slug,
                                           'employee_id': self.user_1.pk}),
                         follow=True)
        osoe = OrganizationalStructureOfficeEmployee.objects.filter(office=self.office_1,
                                                                    employee=self.user_1).first()
        assert not osoe
        # User1 is an employee of generic "help desk" office
        # he can view all tickets
        assert user_is_operator(self.user_1, self.structure_1)
        assert user_is_office_operator(self.user_1, self.office_1)

    def test_delete_office(self):
        # Delete office
        self.client.get(reverse('uni_ticket:manager_delete_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        office_deleted = OrganizationalStructureOffice.objects.filter(name='Office 1',
                                                                      organizational_structure=self.structure_1)
        assert not office_deleted

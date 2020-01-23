import logging

from django.test import RequestFactory
from django.urls import reverse

from organizational_area.models import OrganizationalStructureOffice
from uni_ticket.models import *
from uni_ticket.views import manager
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base import BaseTest


logger = logging.getLogger('my_logger')

class Test_ManagerFunctions(BaseTest):

    def setUp(self):
        super().setUp()
        # Staff_1 User login (manager of Structure 1)
        self.client.force_login(self.staff_1)

        # Create category 1
        cat_name = 'Category 1'
        params = {'name': cat_name,
                  'description': 'Description category 1'}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    params,
                                    follow=True)
        self.category_1 = TicketCategory.objects.get(name=cat_name)

        # Create category 2
        cat_name2 = 'Category 2'
        params = {'name': cat_name2,
                  'description': 'Description category 2'}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    params,
                                    follow=True)
        self.category_2 = TicketCategory.objects.get(name=cat_name2)

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
        self.assertFalse(check_manager)

    def test_category(self):
        # Enable category without input modules (fails!)
        self.client.get(reverse('uni_ticket:manager_enable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug}),
                         follow=True)
        self.category_1.refresh_from_db()
        self.assertFalse(self.category_1.is_active)

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

        # Edit with same name (fails!)
        name = 'Category 2'
        params =  {'name': name,}
        self.client.post(reverse('uni_ticket:manager_category_edit',
                                 kwargs={'structure_slug': self.structure_1.slug,
                                         'category_slug': self.category_1.slug}),
                         params,
                         follow=True)
        self.category_1.refresh_from_db()
        self.assertFalse(self.category_1.name == name)

        # Delete
        self.client.get(reverse('uni_ticket:manager_delete_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_2.slug}),
                         follow=True)
        self.assertFalse(TicketCategory.objects.filter(name=name))

    def test_category_input_module(self):
        # Create
        name = 'module name'
        params = {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_new_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        module = TicketCategoryModule.objects.get(name=name,
                                                  ticket_category=self.category_1)
        assert module
        self.assertFalse(module.is_active)

        # Add field
        field_name = 'date_field'
        params = {'name': field_name,
                  'field_type': 'BaseDateField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': module.pk}),
                                    params,
                                    follow=True)
        input_field = TicketCategoryInputList.objects.filter(category_module=module,
                                                            name=field_name).first()
        assert input_field

        # Edit field
        field_name = 'date_field edited'
        params = {'name': field_name,
                  'field_type': 'BaseDateField',
                  'is_required': True}
        response = self.client.post(reverse('uni_ticket:manager_category_input_field_edit',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': module.pk,
                                                    'field_id': input_field.pk}),
                                    params,
                                    follow=True)
        input_field.refresh_from_db()
        assert input_field.name == field_name

        # Remove field
        field_name = 'date_field'
        response = self.client.get(reverse('uni_ticket:manager_category_input_field_delete',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': module.pk,
                                                    'field_id': input_field.pk}),
                                    follow=True)
        input_field = TicketCategoryInputList.objects.filter(category_module=module,
                                                            name=field_name).first()
        assert not input_field

        # Enable
        self.client.get(reverse('uni_ticket:manager_category_input_module_enable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': module.pk}),
                        follow=True)
        module.refresh_from_db()
        assert module.is_active

        # Add category in office competences
        # Category must be enabled (fails!)
        params = {'category': self.category_1.pk,}
        response = self.client.post(reverse('uni_ticket:manager_add_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug}),
                                    params,
                                    follow=True)
        self.category_1.refresh_from_db()
        self.assertFalse(self.category_1.organizational_office == self.office_1)

        # Enable category after enable input module
        self.client.get(reverse('uni_ticket:manager_enable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug}),
                        follow=True)
        self.category_1.refresh_from_db()
        assert self.category_1.is_active

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

        # Remove category from office competences
        # Category must be enabled (now is ok!)
        response = self.client.get(reverse('uni_ticket:manager_remove_office_category',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'office_slug': self.office_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    follow=True)
        self.category_1.refresh_from_db()
        self.assertFalse(self.category_1.organizational_office == self.office_1)

        # Disable category
        self.client.get(reverse('uni_ticket:manager_disable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug}),
                        follow=True)
        self.category_1.refresh_from_db()
        assert not self.category_1.is_active

        # Disable
        self.client.get(reverse('uni_ticket:manager_category_input_module_disable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': module.pk}),
                        follow=True)
        module.refresh_from_db()
        self.assertFalse(module.is_active)

        # Edit
        new_name = 'new module name'
        new_params = {'name': new_name,}
        self.client.post(reverse('uni_ticket:manager_category_input_module_edit',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': module.pk}),
                        new_params,
                        follow=True)
        module.refresh_from_db()
        assert module.name == new_name

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
        self.assertFalse(condition.is_active)

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
        self.assertFalse(condition)

    def test_office_and_operator(self):
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
        response = self.client.get(reverse('uni_ticket:manager_remove_office_category',
                                           kwargs={'structure_slug': self.structure_1.slug,
                                                   'category_slug': self.category_1.slug,
                                                   'office_slug': self.office_1.slug}),
                                   follow=True)
        self.category_1.refresh_from_db()
        self.assertFalse(self.category_1.organizational_office == self.office_1)

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
        self.assertFalse(osoe)
        # User1 is an employee of generic "help desk" office
        # he can view all tickets
        assert user_is_operator(self.user_1, self.structure_1)
        assert user_is_office_operator(self.user_1, self.office_1)

        # Disable office
        self.client.get(reverse('uni_ticket:manager_disable_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        self.office_1.refresh_from_db()
        self.assertFalse(self.office_1.is_active)

        # Delete office
        self.client.get(reverse('uni_ticket:manager_delete_office',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'office_slug': self.office_1.slug}),
                        follow=True)
        office_deleted = OrganizationalStructureOffice.objects.filter(name='Office 1',
                                                                      organizational_structure=self.structure_1)
        self.assertFalse(office_deleted)

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

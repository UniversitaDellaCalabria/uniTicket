import logging

from django.urls import reverse

from organizational_area.models import OrganizationalStructureOffice
from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base import BaseTest


logger = logging.getLogger('my_logger')


class BaseCategoryOfficeEnvironment(BaseTest):

    def add_new_category(self, cat_name, structure_slug,
                         allow_employee=True,
                         allow_user=True,
                         allow_guest=True):
        params = {'name': cat_name,
                  'description': cat_name,
                  'allow_employee': allow_employee,
                  'allow_user': allow_user,
                  'allow_guest': allow_guest,
                  'user_multiple_open_tickets': True}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': structure_slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        cat = TicketCategory.objects.filter(name=cat_name,
                                            organizational_structure__slug=structure_slug).first()
        return cat

    def create_input_module_in_category(self, name,
                                        structure_slug,
                                        category_slug):
        params = {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_new_input_module',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category_slug}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        module = TicketCategoryModule.objects.filter(name=name,
                                                     ticket_category__slug=category_slug).first()
        assert module
        self.assertFalse(module.is_active)
        return module

    def enable_category(self, structure_slug, category):
        response = self.client.get(reverse('uni_ticket:manager_enable_category',
                                           kwargs={'structure_slug': structure_slug,
                                                   'category_slug': category.slug}),
                                   follow=True)
        assert response.status_code == 200
        category.refresh_from_db()

    def disable_category(self, structure_slug, category):
        response = self.client.get(reverse('uni_ticket:manager_disable_category',
                                   kwargs={'structure_slug': structure_slug,
                                           'category_slug':category.slug}),
                                   follow=True)
        assert response.status_code == 200
        category.refresh_from_db()
        self.assertFalse(category.is_active)

    def enable_input_module(self, structure_slug, category_slug, module):
        response = self.client.get(reverse('uni_ticket:manager_category_input_module_enable',
                                           kwargs={'structure_slug': structure_slug,
                                                   'category_slug': category_slug,
                                                   'module_id': module.pk}),
                                   follow=True)
        assert response.status_code == 200
        module.refresh_from_db()

    def create_new_office(self, name, structure_slug):
        params = {'name': name,
                  'description': name}
        response = self.client.post(reverse('uni_ticket:manager_office_add_new',
                                            kwargs={'structure_slug': structure_slug,}),
                                    params,
                                    follow=True)
        off = OrganizationalStructureOffice.objects.filter(name=name).first()
        assert response.status_code == 200
        assert off
        self.assertFalse(off.is_active)
        return off

    def enable_office(self, structure_slug, office):
        self.client.get(reverse('uni_ticket:manager_enable_office',
                                kwargs={'structure_slug': structure_slug,
                                        'office_slug': office.slug}),
                        follow=True)
        office.refresh_from_db()

    def disable_office(self, structure_slug, office):
        self.client.get(reverse('uni_ticket:manager_disable_office',
                                kwargs={'structure_slug': structure_slug,
                                        'office_slug': office.slug}),
                        follow=True)
        office.refresh_from_db()

    def assign_office_to_category(self, structure_slug,
                                  category,
                                  office_slug):
        params = {'office': office_slug,}
        response = self.client.post(reverse('uni_ticket:manager_category_detail',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category.slug}),
                                    params,
                                    follow=True)
        category.refresh_from_db()

    def add_field_to_input_module(self, name, field_type, is_required,
                                  structure_slug, category_slug, module):
        params = {'name': name,
                  'field_type': field_type,
                  'is_required': is_required}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module',
                                            kwargs={'structure_slug': structure_slug,
                                                    'category_slug': category_slug,
                                                    'module_id': module.pk}),
                                    params,
                                    follow=True)
        assert response.status_code == 200
        module.refresh_from_db()
        self.input_field = TicketCategoryInputList.objects.filter(category_module=module,
                                                                  name=name).first()
        assert self.input_field

    def setUp(self):
        super().setUp()

        # Structure 2 Manager login
        self.structure_2_manager_login()
        self.category_1_str_2 = self.add_new_category(cat_name='Category 1 Structure 2',
                                                      structure_slug=self.structure_2.slug)
        assert self.category_1_str_2
        self.assertFalse(self.category_1_str_2.is_active)

        # Create a simple input module for Category 1 in Structure 2 (success!)
        self.module_1 = self.create_input_module_in_category(name='module',
                                                             structure_slug=self.structure_2.slug,
                                                             category_slug=self.category_1_str_2.slug)

        # Try to enable category without an enabled input module (fails!)
        self.enable_category(structure_slug=self.structure_2.slug,
                             category=self.category_1_str_2)
        self.assertFalse(self.category_1_str_2.is_active)

        # Enable input module (success!)
        self.enable_input_module(structure_slug=self.structure_2.slug,
                                 category_slug=self.category_1_str_2.slug,
                                 module=self.module_1)
        assert self.module_1.is_active

        # Enable category (fails! category needs an Office)
        self.enable_category(structure_slug=self.structure_2.slug,
                             category=self.category_1_str_2)
        self.assertFalse(self.category_1_str_2.is_active)

        # Create a new office in Structure 2
        self.office_1_str_2 = self.create_new_office(name='Office 1 Stucture 2',
                                                     structure_slug=self.structure_2.slug)

        # Add office in category competences (fails! office must be enabled)
        self.assign_office_to_category(self.structure_2.slug,
                                       self.category_1_str_2,
                                       self.office_1_str_2.slug)
        self.assertFalse(self.category_1_str_2.organizational_office == self.office_1_str_2)

        # Enable office
        self.enable_office(self.structure_2.slug, self.office_1_str_2)
        assert self.office_1_str_2.is_active

        # Add office in category competences
        self.assign_office_to_category(self.structure_2.slug,
                                       self.category_1_str_2,
                                       self.office_1_str_2.slug)
        assert self.category_1_str_2.organizational_office == self.office_1_str_2

        # Enable category (success!)
        self.enable_category(structure_slug=self.structure_2.slug,
                             category=self.category_1_str_2)
        assert self.category_1_str_2.is_active

        # Disable category (success!)
        self.disable_category(structure_slug=self.structure_2.slug,
                              category=self.category_1_str_2)

        # Enable category (success!)
        self.enable_category(structure_slug=self.structure_2.slug,
                             category=self.category_1_str_2)
        assert self.category_1_str_2.is_active

        # Disable office
        self.disable_office(self.structure_2.slug, self.office_1_str_2)
        self.office_1_str_2.refresh_from_db()
        self.assertFalse(self.office_1_str_2.is_active)
        self.category_1_str_2.refresh_from_db()
        self.assertFalse(self.category_1_str_2.is_active)

        # Enable office
        self.enable_office(self.structure_2.slug, self.office_1_str_2)
        assert self.office_1_str_2.is_active

        # Enable category (success!)
        self.enable_category(structure_slug=self.structure_2.slug,
                             category=self.category_1_str_2)
        assert self.category_1_str_2.is_active

        # Category in Structure 1
        # Staff_1 User login (manager of Structure 1)
        self.structure_1_manager_login()

        # Create category 1
        self.category_1_str_1 = self.add_new_category(cat_name='Category 1 Structure 1',
                                                      structure_slug=self.structure_1.slug)
        assert self.category_1_str_1
        self.assertFalse(self.category_1_str_1.is_active)

        # Create an input module for category 1
        # Create a simple input module for Category 1 in Structure 2 (success!)
        self.module_2 = self.create_input_module_in_category(name='module',
                                                             structure_slug=self.structure_1.slug,
                                                             category_slug=self.category_1_str_1.slug)


        # Add file field to input module
        # in order to simulate ticket attachment
        self.add_field_to_input_module(name='file_field_1',
                                       field_type='CustomFileField',
                                       is_required=False,
                                       structure_slug=self.structure_1.slug,
                                       category_slug=self.category_1_str_1.slug,
                                       module=self.module_2)

        # Enable input module (success!)
        self.enable_input_module(structure_slug=self.structure_1.slug,
                                 category_slug=self.category_1_str_1.slug,
                                 module=self.module_2)

        # Create a new office in Structure 1
        self.office_1_str_1 = self.create_new_office(name='Office 1 Stucture 1',
                                                     structure_slug=self.structure_1.slug)

        # Enable office
        self.enable_office(self.structure_1.slug, self.office_1_str_1)
        assert self.office_1_str_1.is_active

        # Add office in category competences
        self.assign_office_to_category(self.structure_1.slug,
                                       self.category_1_str_1,
                                       self.office_1_str_1.slug)
        assert self.category_1_str_1.organizational_office == self.office_1_str_1

        # Enable category
        self.enable_category(structure_slug=self.structure_1.slug,
                             category=self.category_1_str_1)
        assert self.category_1_str_1.is_active

        # Now we have 2 active categories (category_1_str_1 and category_1_str_2)
        # with their own active offices (office_1_str_1 and office_1_str_2)

    def test_create_category_without_permissions(self):
        # Structure 2 Manager login
        self.structure_2_manager_login()

        # Create in Structure 1
        cat = self.add_new_category(cat_name='Cat',
                                    structure_slug=self.structure_1.slug)
        self.assertFalse(cat)

    def test_create_category_by_operator(self):
        # Structure 1 Operator login
        self.structure_1_default_office_operator_login()

        # Create in Structure 1
        cat = self.add_new_category(cat_name='Cat',
                                    structure_slug=self.structure_1.slug)
        self.assertFalse(cat)

import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base import BaseTest


logger = logging.getLogger('my_logger')


class BaseCategoryEnvironment(BaseTest):

    def setUp(self):
        super().setUp()

        # Staff_2 User login (manager of Structure 2)
        self.client.force_login(self.staff_2)
        # Create category 3
        cat_name = 'Category 3'
        params = {'name': cat_name,
                  'description': 'Description category 3',
                  'allow_employee': True,
                  'allow_user': True,
                  'allow_guest': True}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': self.structure_2.slug}),
                                    params,
                                    follow=True)
        self.category_3 = TicketCategory.objects.get(name=cat_name)

        # Create an input module for category 3
        name = 'module name'
        params = {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_new_input_module',
                                            kwargs={'structure_slug': self.structure_2.slug,
                                                    'category_slug': self.category_3.slug}),
                                    params,
                                    follow=True)
        self.module_3 = TicketCategoryModule.objects.get(name=name,
                                                       ticket_category=self.category_3)

        # Enable module
        self.client.get(reverse('uni_ticket:manager_category_input_module_enable',
                                kwargs={'structure_slug': self.structure_2.slug,
                                        'category_slug': self.category_3.slug,
                                        'module_id': self.module_3.pk}),
                        follow=True)

        # Enable category
        self.client.get(reverse('uni_ticket:manager_enable_category',
                                kwargs={'structure_slug': self.structure_2.slug,
                                        'category_slug': self.category_3.slug}),
                        follow=True)

        # Staff_1 User login (manager of Structure 1)
        self.client.force_login(self.staff_1)

        # Create category 1
        cat_name = 'Category 1'
        params = {'name': cat_name,
                  'description': 'Description category 1',
                  'allow_employee': True,
                  'allow_user': True,
                  'allow_guest': True}
        response = self.client.post(reverse('uni_ticket:manager_category_add_new',
                                            kwargs={'structure_slug': self.structure_1.slug}),
                                    params,
                                    follow=True)
        self.category_1 = TicketCategory.objects.get(name=cat_name)

        # Create an input module for category 1
        name = 'module name'
        params = {'name': name,}
        response = self.client.post(reverse('uni_ticket:manager_category_new_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug}),
                                    params,
                                    follow=True)
        self.module = TicketCategoryModule.objects.get(name=name,
                                                       ticket_category=self.category_1)

        # Add file field to input module
        # in order to simulate ticket attachment
        field_name = 'file_field_1'
        params = {'name': field_name,
                  'field_type': 'CustomFileField',
                  'is_required': False}
        response = self.client.post(reverse('uni_ticket:manager_category_input_module',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'category_slug': self.category_1.slug,
                                                    'module_id': self.module.pk}),
                                    params,
                                    follow=True)
        self.input_field = TicketCategoryInputList.objects.filter(category_module=self.module,
                                                                  name=field_name).first()
        # Enable module
        self.client.get(reverse('uni_ticket:manager_category_input_module_enable',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug,
                                        'module_id': self.module.pk}),
                        follow=True)

        # Enable category
        self.client.get(reverse('uni_ticket:manager_enable_category',
                                kwargs={'structure_slug': self.structure_1.slug,
                                        'category_slug': self.category_1.slug}),
                        follow=True)



from django.apps import apps
from django.conf import settings
from django.test import Client, TestCase
from django.utils.text import slugify

from organizational_area.models import *


class BaseTest(TestCase):

    def create_structure(self, name, slug, unique_code, structure_type):
        return OrganizationalStructure.objects.create(name=name,
                                                      slug=slugify(name),
                                                      unique_code=unique_code,
                                                      structure_type=structure_type)

    def setUp(self):

        self.client = Client()

        struc_type = OrganizationalStructureType.objects.create(name="Macro Area")

        # Create structures
        self.structure_1 = self.create_structure(name="Structure 1",
                                                 slug="structure-1",
                                                 unique_code="code_structure_1",
                                                 structure_type=struc_type)
        self.structure_2 = self.create_structure(name="Structure 2",
                                                 slug="structure-2",
                                                 unique_code="code_structure_2",
                                                 structure_type=struc_type)

        # Create users
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        self.staff_1 = user_model.objects.create_user(username='staff1', password='passw',
                                                     first_name="Staff 1",
                                                     last_name="Lastname Staff 1",
                                                     email="staff1@test.it",
                                                     is_staff=True)
        self.staff_2 = user_model.objects.create_user(username='staff2', password='passw',
                                                     first_name="Staff 2",
                                                     last_name="Lastname Staff 2",
                                                     email="staff2@test.it",
                                                     is_staff=True)
        self.user_1 = user_model.objects.create_user(username='user1', password='passw',
                                                     first_name="User 1",
                                                     last_name="Lastname User 1",
                                                     email="user1@test.it")
        self.user_2 = user_model.objects.create_user(username='user2', password='passw',
                                                     first_name="User 2",
                                                     last_name="Lastname User 2",
                                                     email="user2@test.it")

        # Assign self.staff_1 to structure1
        # He is a staff user and for this reason he will be a structure manager
        default_office_s1 = self.structure_1.get_default_office()
        employee_manager_1 = OrganizationalStructureOfficeEmployee.objects.create(employee=self.staff_1,
                                                                                  office=default_office_s1)

        default_office_s2 = self.structure_2.get_default_office()
        employee_manager_2 = OrganizationalStructureOfficeEmployee.objects.create(employee=self.staff_2,
                                                                                  office=default_office_s2)
        # Create a standard operator in default office
        # Manager can move it
        employee_standard_1 = OrganizationalStructureOfficeEmployee.objects.create(employee=self.user_1,
                                                                                   office=default_office_s1)

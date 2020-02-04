from django.apps import apps
from django.conf import settings
from django.test import Client, TestCase
from django.utils.text import slugify

from organizational_area.models import *


class BaseTest(TestCase):

    def create_structure(self, name, slug, unique_code, structure_type_name=''):
        if not structure_type_name:
            structure_type_name = "Macro Area"
        structure_type = OrganizationalStructureType.objects.get_or_create(name=structure_type_name)[0]
        return OrganizationalStructure.objects.create(name=name,
                                                      slug=slugify(name),
                                                      unique_code=unique_code,
                                                      structure_type=structure_type)

    def assign_user_to_structure(self, user, structure):
        if not user: return False
        if not structure: return False
        default_office = structure.get_default_office()
        osoe = OrganizationalStructureOfficeEmployee.objects.create(employee=user,
                                                                    office=default_office)

    def setUp(self):
        self.client = Client()

        # Create structures
        self.structure_1 = self.create_structure(name="Structure 1",
                                                 slug="structure-1",
                                                 unique_code="code_structure_1")
        self.structure_2 = self.create_structure(name="Structure 2",
                                                 slug="structure-2",
                                                 unique_code="code_structure_2")

        # Create users
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        # Staff 1
        self.staff_1 = user_model.objects.create_user(username='staff1', password='passw',
                                                     first_name="Staff 1",
                                                     last_name="Lastname Staff 1",
                                                     email="staff1@test.it",
                                                     is_staff=True)
        # Staff 2
        self.staff_2 = user_model.objects.create_user(username='staff2', password='passw',
                                                     first_name="Staff 2",
                                                     last_name="Lastname Staff 2",
                                                     email="staff2@test.it",
                                                     is_staff=True)
        # User 1
        self.user_1 = user_model.objects.create_user(username='user1', password='passw',
                                                     first_name="User 1",
                                                     last_name="Lastname User 1",
                                                     email="user1@test.it")
        # User 2
        self.user_2 = user_model.objects.create_user(username='user2', password='passw',
                                                     first_name="User 2",
                                                     last_name="Lastname User 2",
                                                     email="user2@test.it")

        # Assign users to structures
        # These are staff users and for this reason they will be structure managers
        self.assign_user_to_structure(self.staff_1, self.structure_1)
        self.assign_user_to_structure(self.staff_2, self.structure_2)
        # These are simple users and for this reason they will be default office operators
        self.assign_user_to_structure(self.user_1, self.structure_1)
        self.assign_user_to_structure(self.user_2, self.structure_2)

    def structure_1_manager_login(self):
        # Staff_1 User login (manager of Structure 1)
        self.client.force_login(self.staff_1)

    def structure_2_manager_login(self):
        # Staff_2 User login (manager of Structure 2)
        self.client.force_login(self.staff_2)

    def structure_1_default_office_operator_login(self):
        # User_1 User login (operator of Structure 1 default office)
        self.client.force_login(self.user_1)

    def structure_2_default_office_operator_login(self):
        # User_2 User login (operator of Structure 2 default office)
        self.client.force_login(self.user_2)

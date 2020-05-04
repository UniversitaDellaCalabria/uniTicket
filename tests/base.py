from django.apps import apps
from django.conf import settings
from django.test import Client, TestCase
from django.utils.text import slugify

from organizational_area.models import *


class BaseTest(TestCase):

    def create_structure(self, name):
        structure_type = OrganizationalStructureType.objects.get_or_create(name="Macro Area")[0]
        return OrganizationalStructure.objects.create(name=name,
                                                      slug=slugify(name),
                                                      unique_code=slugify(name),
                                                      structure_type=structure_type)

    def create_user(self, name):
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        return user_model.objects.create_user(username=slugify(name),
                                              password='passw',
                                              first_name=name,
                                              last_name="Lastname {}".format(name),
                                              email="{}@test.it".format(slugify(name)))

    def assign_user_to_structure(self, user, structure, manage=False):
        # Assign users to structure default office
        # Staff users become manager
        default_office = structure.get_default_office()
        osoe_model = OrganizationalStructureOfficeEmployee
        osoe = osoe_model.objects.create(employee=user,
                                         office=default_office)
        if manage:
            umos_model = UserManageOrganizationalStructure
            umos = umos_model.objects.create(user=user,
                                             organizational_structure=structure)

    def setUp(self):
        self.client = Client()

        # Create structures
        self.structure_1 = self.create_structure(name="Structure 1")
        self.structure_2 = self.create_structure(name="Structure 2")

        # Create users
        # Staff users
        self.staff_1 = self.create_user(name="Staff 1")
        self.staff_2 = self.create_user(name="Staff 2")
        # Simple users
        self.user_1 = self.create_user(name="User 1")
        self.user_2 = self.create_user(name="User 2")

        # Assign users to structures
        # These are staff users and for this reason they will be structure managers
        self.assign_user_to_structure(self.staff_1, self.structure_1, manage=True)
        self.assign_user_to_structure(self.staff_2, self.structure_2, manage=True)
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

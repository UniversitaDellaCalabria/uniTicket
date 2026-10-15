import logging

from unittest import mock

from organizational_area.decorators import disable_for_loaddata
from organizational_area.models import (EquipmentType,
                                        OrganizationalStructureFunction,
                                        OrganizationalStructureLocation,
                                        OrganizationalStructureOfficeEmployee,
                                        OrganizationalStructureOfficeLocation,
                                        _logo_upload)
from organizational_area.settings import (DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                                          LOGOS_FOLDER,
                                          STRUCTURES_FOLDER)
from organizational_area.templatetags.organizational_area_tags import (
    employee_offices,
    organizational_area_settings_value
)

from . base import BaseTest


logger = logging.getLogger('my_logger')


class Test_OrganizationalAreaModels(BaseTest):

    def test_folders(self):
        slug = self.structure_1.slug
        self.assertEqual(self.structure_1.get_folder(),
                         '{}/{}'.format(STRUCTURES_FOLDER, slug))
        self.assertEqual(self.structure_1.get_logo_folder(),
                         '{}/{}'.format(LOGOS_FOLDER, slug))
        self.assertEqual(_logo_upload(self.structure_1, 'logo.png'),
                         '{}/{}/logo.png'.format(LOGOS_FOLDER, slug))

    def test_get_offices_and_employees(self):
        default_office = self.structure_1.get_default_office()
        self.assertEqual(list(self.structure_1.get_offices()), [default_office])
        self.assertFalse(self.structure_1.get_offices(is_default=False).exists())

        employees = self.structure_1.get_employees()
        self.assertEqual({e.employee for e in employees},
                         {self.staff_1, self.user_1})
        self.assertEqual([e.employee for e in
                          self.structure_1.get_employees(employee=self.user_1)],
                         [self.user_1])

    def test_get_structure_managers(self):
        managers = self.structure_1.get_structure_managers()
        self.assertEqual([m.user for m in managers], [self.staff_1])

    def test_str(self):
        self.assertEqual(str(self.structure_1),
                         'Structure 1, Macro Area')
        self.structure_1.structure_type = None
        self.assertEqual(str(self.structure_1), 'Structure 1')

        function = OrganizationalStructureFunction(name='Function')
        self.assertEqual(str(function), 'Function')

        equipment = EquipmentType(name='Equipment')
        self.assertEqual(str(equipment), 'Equipment')

        default_office = self.structure_1.get_default_office()
        self.assertEqual(default_office.name,
                         DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE)
        office_location = OrganizationalStructureOfficeLocation(
            office=default_office,
            address='Via Roma'
        )
        self.assertEqual(str(office_location),
                         '{} - Via Roma'.format(default_office))

        employee = OrganizationalStructureOfficeEmployee.objects.get(
            employee=self.user_1, office=default_office
        )
        self.assertEqual(str(employee),
                         '{} - {}'.format(self.user_1, default_office))

    def test_structure_location_str(self):
        # no custom __str__: falls back to the default Model representation
        location = OrganizationalStructureLocation.objects.create(
            organizational_structure=self.structure_1
        )
        self.assertEqual(str(location),
                         'OrganizationalStructureLocation object ({})'.format(location.pk))


class Test_OrganizationalAreaDecorators(BaseTest):

    def test_disable_for_loaddata(self):
        handler = mock.Mock()
        wrapped = disable_for_loaddata(handler)

        self.assertIsNone(wrapped(sender=None, raw=True))
        handler.assert_not_called()

        wrapped(sender=None, raw=False)
        handler.assert_called_once_with(sender=None, raw=False)


class Test_OrganizationalAreaTags(BaseTest):

    def test_employee_offices(self):
        self.assertIsNone(employee_offices(None))

        offices = employee_offices(self.user_1)
        self.assertEqual([o.office for o in offices],
                         [self.structure_1.get_default_office()])

        self.assertTrue(employee_offices(self.user_1, self.structure_1).exists())
        self.assertFalse(employee_offices(self.user_1, self.structure_2).exists())

    def test_organizational_area_settings_value(self):
        self.assertEqual(
            organizational_area_settings_value('DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE'),
            DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE
        )
        with mock.patch('organizational_area.settings.LOGOS_FOLDER',
                        'logos/{slug}', create=True):
            self.assertEqual(
                organizational_area_settings_value('LOGOS_FOLDER', slug='s1'),
                'logos/s1'
            )
        self.assertIsNone(organizational_area_settings_value('NOT_EXISTENT'))

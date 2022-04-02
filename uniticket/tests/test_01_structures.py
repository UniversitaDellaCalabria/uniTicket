import logging


from . base import BaseTest


logger = logging.getLogger('my_logger')

class Test_Structure(BaseTest):

    def test_structure_has_default_office(self):
        """
        """
        default_office = self.structure_1.get_default_office()
        assert default_office
        assert default_office.is_active
        assert default_office.is_default

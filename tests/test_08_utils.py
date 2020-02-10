import json
import logging

from django.urls import reverse

from uni_ticket.models import *
from uni_ticket.urls import *
from uni_ticket.utils import *

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_UtilsFunctions(BaseTicketEnvironment):

    def test_ticket_user_summary_dict(self):
        self.structure_1_manager_login()
        response = ticket_user_summary_dict(self.staff_1)
        summary_ticket = {'subject': self.ticket.subject,
                          'url': self.ticket.get_url(structure=self.structure_1)}
        assert summary_ticket in response[self.structure_1][self.office_1_str_1]

import logging

from django.urls import reverse


from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


class Test_OperatorFunctions(BaseTicketEnvironment):

    def test_operator_dashboard(self):
        # Dashboard
        self.structure_1_default_office_operator_login()
        response = self.client.get(reverse('uni_ticket:operator_dashboard',
                                           kwargs={'structure_slug': self.structure_1.slug}),
                                   follow=True)
        assert response.status_code == 200
        # assert response.context['ticket_non_gestiti'] > 0
        # assert self.ticket in response.context['ticket_non_gestiti']

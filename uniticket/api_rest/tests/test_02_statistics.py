import calendar
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from organizational_area.models import OrganizationalStructure, OrganizationalStructureOffice, OrganizationalStructureOfficeEmployee
from uni_ticket.models import Ticket, TicketCategory, TicketCategoryInputList, TicketCategoryModule, TicketReply
from tests.base_ticket_env import BaseTicketEnvironment
from uni_ticket.statistics import uniTicketStats


N_TICKET = 33


class uniTicketAPIStatsTest(BaseTicketEnvironment):

    @override_settings(MAX_DAILY_TICKET_PER_USER = 100)
    def setUp(self):
        self.op1 = get_user_model().objects.create(
            username = "operator"
        )

        # huge workaround to fit in the francescos tests
        self.staff_2 = self.op1

        self.user_1 = get_user_model().objects.create(
            username = "test"
        )
        self.structure_1 = OrganizationalStructure.objects.create(
            **{
                "id": 10,
                "name": "Structure 1",
                "slug": "structure-stats",
                "unique_code": "structure-stats",
                "description": "",
                "banner": None,
                "url": None,
                "is_active": True,
                "structure_type": None
            }
        )

        self.office = OrganizationalStructureOffice.objects.create(
            **{
                'name': 'that office',
                'slug': 'that-office',
                'organizational_structure': self.structure_1,
                'description': 'that Office',
                'is_default': True,
                'is_private': False,
                'is_active': True
            }
        )
        self.office_operator = OrganizationalStructureOfficeEmployee.objects.create(
            employee=self.op1, office=self.office
        )
        self.category = TicketCategory.objects.create(
            **{
                "id": 3,
                "organizational_structure": self.structure_1,
                # helpdesk is the default/automatic one
                "organizational_office": self.office,
                "date_start": None,
                "date_end": None,
                "created": "2020-05-08T09:30:02.759000+00:00",
                "modified": "2022-04-11T13:02:23.178085+00:00",
                "name": "Modello di richiesta di test",
                "slug": "modello-di-richiesta-di-test",
                "description": "Descrizione del modulo e delle sue finalità",
                "is_active": True,
                "not_available_message": None,
                "show_heading_text": True,
                "allow_anonymous": False,
                "allow_guest": True,
                "allow_user": True,
                "allow_employee": True,
                "is_notification": False,
                "footer_text": "",
                "receive_email": False,
                "protocol_required": False,
                "user_multiple_open_tickets": True,

            }
        )
        self.modulo = TicketCategoryModule.objects.create(
            **{
                'name': 'Modulo esteso',
                'ticket_category': self.category,
                'is_active': True
            }
        )
        TicketCategoryInputList.objects.create(
            category_module = self.modulo
        )

        for i in range(N_TICKET):
            ticket = Ticket.objects.create(
                subject = f'Ticket {i}',
                input_module = self.modulo,
            )
            if i in range(10):
                # I close the first 10
                ticket.created = timezone.localtime() - timezone.timedelta(hours=i*10)
                ticket.add_competence(office=self.office, user=self.staff_2)

                ticket.close(user=self.op1, motivazione = f"motivazione {i}")
                ticket.closed_by = self.op1
                ticket.closed_date = timezone.localtime() + timezone.timedelta(hours=1)
                ticket.save()

                # add some random message
                TicketReply.objects.create(
                    ticket = ticket,
                    owner = self.op1,
                    structure = self.structure_1,
                    subject = "test", text="that text"
                )
                TicketReply.objects.create(
                    ticket = ticket,
                    owner = self.user_1,
                    structure = self.structure_1,
                    subject = "test", text="that text"
                )

            elif i in range(10,15):
                # then assign the following 5
                ticket.created = timezone.localtime() - timezone.timedelta(hours=i*10)
                ticket.add_competence(office=self.office, user=self.staff_2)
                ticket.save()

    def test_stats_result(self):
        stats = uniTicketStats(date_end = timezone.localtime() + timezone.timedelta(hours=2))
        stats.load()
        self.assertTrue(stats.open == N_TICKET)
        self.assertTrue(tuple(stats.open_by_user.values())[0] == N_TICKET)

        self.assertTrue(stats.closed == 10)
        self.assertTrue(tuple(stats.closed_by_ops.values())[0] == 10)

        self.assertTrue(stats.avg_msg_to_close < 1.82 and stats.avg_msg_to_close > 1.81)
        self.assertTrue(stats.avg_pre_processing == 607)
        self.assertTrue(stats.avg_full_processing == 676)

        first_day = list(stats.ticket_per_day_hour.keys())[0]
        self.assertTrue(len(stats.ticket_per_day_hour[first_day].keys()) == 2)

        self.assertTrue(stats.avg_first_time_op_answer == 621)

        for i in range(0,7):
            self.assertTrue(stats.ticket_per_weekday[calendar.day_name[i]])

        self.assertTrue(len(stats.ticket_per_weekday) == 7)

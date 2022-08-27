import calendar
import statistics

from pydantic import BaseModel

from django.db.models import Q
from django.utils import timezone
from uni_ticket.models import Ticket, TicketReply

from typing import Union
from organizational_area.models import OrganizationalStructureOfficeEmployee
from uni_ticket.settings import STATS_TIME_SLOTS, STATS_DEFAULT_DATE_START_DELTA_DAYS


class StatsArgsModel(BaseModel):
    date_start : Union[timezone.datetime, None]
    date_end : Union[timezone.datetime, None]
    structure_slug : Union[str, None]
    office_slug : Union[str, None]
    category_slug : Union[str, None]


class uniTicketStats:

    def __init__(
        self,
        date_start:Union[timezone.datetime, None] = None,
        date_end:Union[timezone.datetime, None] = None,
        structure_slug:Union[str, None] = None,
        office_slug : Union[str, None] = None,
        category_slug:Union[str, None] = None
    ):
        # args validation
        StatsArgsModel(
            **dict(
                date_start = date_start,
                date_end = date_end,
                structure_slug = structure_slug,
                office_slug = office_slug,
                category_slug = category_slug
            )
        )

        self.date_end = date_end or timezone.localtime() # + timezone.timedelta(hours = 1)
        # if not date_start it will go back for 15 days by default
        self.date_start = date_start or self.date_end - timezone.timedelta(days = STATS_DEFAULT_DATE_START_DELTA_DAYS)

        self.structure_slug = structure_slug
        self.office_slug = office_slug
        self.category_slug = category_slug

        self.open: int = 0 # means not taken by any operator
        self.closed: int = 0
        self.reopened: int = 0
        self.notifications: int = 0
        self.assigned: int = 0

        self.open_day_serie: dict = {}
        self.closed_day_serie: dict = {}
        self.reopened_day_serie: dict = {}
        self.notifications_day_serie: dict = {}
        self.assigned_day_serie: dict = {}

        # in minutes (time between open and assignment)
        self.avg_pre_processing: int = 0

        # how many messages before closing the tickets
        self.avg_msg_to_close: int = 0

        # mean of the minutes between ticket taken and closed
        self.avg_time_created_taken : int = 0

        # how many ticket have been closed by each user:str
        self.closed_by_ops: dict = {}
        self.closed_by_ops_count: int = 0

        # how many ticket have been opened by each user:str
        self.open_by_user: dict = {}

        # primo tempo di risposta
        # Time between creating a ticket and a operator’s first message.
        self.avg_first_time_op_answer: int = 0

        self.ticket_per_day: dict = {}
        # count per day and hours
        # {'01-01-2022': {'total': int, 'hours': {0: int, ... 23: int}}}
        self.ticket_per_day_hour: dict = {}

        # {'monday': int, ''}
        self.ticket_per_weekday: dict = {
            calendar.day_name[wd]: [0 for i in STATS_TIME_SLOTS.keys()]
            for wd in range(0,7)
        }

    def ticket_data_query(self):
        _q = {}

        if self.structure_slug:
            _q[
                'input_module'
                '__ticket_category'
                '__organizational_structure'
                '__slug'
            ] = self.structure_slug

        if self.office_slug:
            _q[
                'input_module'
                '__ticket_category'
                '__organizational_office'
                '__slug'
            ] = self.office_slug

        if self.category_slug:
            _q[
                'input_module'
                '__ticket_category'
                '__slug'
            ] = self.category_slug

        return _q

    def get_operators_pks(self):
        _q = {}

        if self.structure_slug:
            _q[
                'office'
                '__organizational_structure'
                '__slug'
            ] = self.structure_slug

        return OrganizationalStructureOfficeEmployee.objects.filter(**_q).values_list(
            "employee__pk", flat=True
        )

    def load(self):
        """
            this method MAY be forked to a standalone process
            the js on the web and the API will get a uuid of the processing
            the serialized result of these statistics will be stored in a Redis with a TTL of 30mins

            the call to the ticket will give the result or a 404 if the TTL is expired
        """
        self.tickets = Ticket.objects.select_related(
            'input_module'
        ).filter(**self.ticket_data_query()).filter(
            Q(created__gte = self.date_start, created__lte=self.date_end) |
            Q(closed_date__gte = self.date_start, closed_date__lte=self.date_end) |
            Q(assigned_date__gte = self.date_start, assigned_date__lte=self.date_end)
        )

        self.closed_tickets = self.tickets.filter(
            closed_date__lte = self.date_end
        )

        self.assigned_tickets = self.tickets.filter(assigned_date__gte = self.date_start)

        self.closed = self.closed_tickets.count()
        self.closed_by_users: int = 0

        # in minutes (time between open and assignment)
        avg_pre_processing = [0]

        # in minutes (time between open and close)
        avg_full_processing = [0]

        # how many messages before closing the tickets
        avg_msg_to_close = [0]

        # how many minutes between taken by operators and closed
        avg_time_created_taken = [0]

        # Time between creating a ticket and operator first message.
        first_time_op_answer = [0]

        # in a single loop I have to process
        # whatever, otherwise it will takes too long. Efficiency may be huge, we know.
        tmsgs = TicketReply.objects.filter(
            ticket__pk__in = self.tickets.values_list("pk", flat=True)
        ).values_list("ticket__pk", "created", "owner")

        operators_pks = self.get_operators_pks()

        for i in self.tickets:

            ticket_time = i.created.strftime("%d-%m-%Y %H")
            ticket_day, ticket_hour = ticket_time.split(" ")
            ticket_day_eu = i.created.strftime("%Y-%m-%d")
            if not self.ticket_per_day_hour.get(ticket_day):
                # {'01-01-2022': {'total': int, 'hours': {0: int, ... 23: int}}}
                self.ticket_per_day_hour[ticket_day] = {'total': 0, 'hours': {}}

            self.ticket_per_day_hour[ticket_day]['total'] += 1
            if not self.ticket_per_day_hour[ticket_day]["hours"].get(ticket_hour):
                self.ticket_per_day_hour[ticket_day]["hours"][ticket_hour] = 0
            self.ticket_per_day_hour[ticket_day]["hours"][ticket_hour] += 1

            if not self.ticket_per_day.get(ticket_day_eu):
                self.ticket_per_day[ticket_day_eu] = 0
            self.ticket_per_day[ticket_day_eu] += 1

            # put the ticket in a configured time slot
            for slot, hour_range in STATS_TIME_SLOTS.items():
                if int(ticket_hour) in hour_range:
                    self.ticket_per_weekday[
                        i.created.strftime(calendar.day_name.format)
                    ][slot - 1] += 1
                    break

            if i.is_notification:
                self.notifications += 1
            else:
                _msgs = tmsgs.filter(ticket=i)
                op_msgs = _msgs.filter(
                    owner__pk__in = operators_pks
                ).values_list("created", flat=True)
                if _msgs and op_msgs:
                    first_time_op_answer.append(
                        (op_msgs[0] - i.created).seconds
                    )

            if not i.has_been_taken():
                self.open += 1
                if not self.open_day_serie.get(ticket_day):
                    self.open_day_serie[ticket_day] = 0
                self.open_day_serie[ticket_day] += 1
            else:
                self.assigned += 1
                avg_pre_processing.append(
                    (i.taken_date - i.created).seconds
                )
                if not self.assigned_day_serie.get(ticket_day):
                    self.assigned_day_serie[ticket_day] = 0
                self.assigned_day_serie[ticket_day] += 1

            if i.closed_date and not i.is_closed:
                self.reopened += 1
                if not self.reopened_day_serie.get(ticket_day):
                    self.reopened_day_serie[ticket_day] = 0
                self.reopened_day_serie[ticket_day] += 1
            elif i.closed_date:
                # is closed
                if not self.closed_day_serie.get(ticket_day):
                    self.closed_day_serie[ticket_day] = 0
                self.closed_day_serie[ticket_day] += 1

                if i.closed_by:
                    # otherwise the user closed by himself
                    _op_name = i.closed_by.__str__()
                    if not self.closed_by_ops.get(_op_name, None):
                        self.closed_by_ops[_op_name] = 0
                    self.closed_by_ops[_op_name] += 1
                    self.closed_by_ops_count += 1
                else:
                    self.closed_by_users += 1

                avg_full_processing.append(
                    (i.closed_date - i.created).seconds
                )
                if i.taken_date:
                    avg_time_created_taken.append(
                        (i.closed_date - i.taken_date).seconds
                    )

                # get how many messages has been taken to close this ticket
                # excluding the closing message
                _mcount = tmsgs.filter(ticket=i).count()
                avg_msg_to_close.append(_mcount)

            _user_name = i.created_by.__str__()
            if not self.open_by_user.get(_user_name, None):
                self.open_by_user[_user_name] = 0
            self.open_by_user[_user_name] += 1

        # aggregation and details in hours
        self.avg_pre_processing_seconds = statistics.mean(avg_pre_processing)
        self.avg_pre_processing = int(self.avg_pre_processing_seconds / 60)

        self.avg_full_processing = int(statistics.mean(avg_full_processing) / 60)
        self.avg_msg_to_close = statistics.mean(avg_msg_to_close)
        self.first_time_op_answer_seconds = statistics.mean(first_time_op_answer)
        self.avg_first_time_op_answer = int(self.first_time_op_answer_seconds / 60)
        self.avg_time_created_taken = int(statistics.mean(avg_time_created_taken) / 60)

        # sort descending
        self.open_by_user = {k: v for k, v in sorted(self.open_by_user.items(), key=lambda item: item[1])}
        self.closed_by_ops = {k: v for k, v in sorted(self.closed_by_ops.items(), key=lambda item: item[1])}

import json
import logging

from unittest import mock

from django.urls import reverse

from uni_ticket.models import Ticket, TicketAssignment

from . base_ticket_env import BaseTicketEnvironment


logger = logging.getLogger('my_logger')


def _dt_args(search="", column=0, direction="asc", length=10, start=0):
    return {"args": json.dumps({"draw": 1,
                                "order": [{"column": column, "dir": direction}],
                                "start": start,
                                "length": length,
                                "search": {"value": search, "regex": False}})}


def _search(year="", text="", category="", structure=""):
    return json.dumps({"year": year,
                       "text": text,
                       "category": category,
                       "structure": structure})


class Test_DatatablesExtra(BaseTicketEnvironment):

    def _post(self, url_name, data, **kwargs):
        response = self.client.post(reverse(url_name, kwargs=kwargs), data)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _manager_all(self, data):
        return self._post('uni_ticket:manager_all_tickets_json',
                          data,
                          structure_slug=self.structure_1.slug)

    def test_search_by_numeric_year(self):
        self.structure_1_manager_login()
        year = str(self.ticket.created.year)
        result = self._manager_all(_dt_args(search=_search(year=year)))
        self.assertEqual(result['recordsFiltered'], 2)
        result = self._manager_all(_dt_args(search=_search(year="1999")))
        self.assertEqual(result['recordsFiltered'], 0)
        self.assertEqual(result['data'], [])

    def test_search_by_relative_period(self):
        self.structure_1_manager_login()
        for period in ("last_week", "last_month"):
            result = self._manager_all(_dt_args(search=_search(year=period)))
            self.assertEqual(result['recordsFiltered'], 2)

    def test_search_by_category_and_text(self):
        self.structure_1_manager_login()
        search = _search(category=self.category_1_str_1.slug,
                         structure=self.structure_1.slug)
        result = self._manager_all(_dt_args(search=search))
        self.assertEqual(result['recordsFiltered'], 2)

        search = _search(category="not-existent",
                         structure=self.structure_1.slug)
        result = self._manager_all(_dt_args(search=search))
        self.assertEqual(result['recordsFiltered'], 0)

        result = self._manager_all(_dt_args(search=_search(text=self.ticket.code)))
        self.assertEqual(result['recordsFiltered'], 1)
        self.assertIn(self.ticket.code, result['data'][0])

        result = self._manager_all(_dt_args(search=_search(text="no-match-text")))
        self.assertEqual(result['recordsFiltered'], 0)

    def test_ordering_asc_desc(self):
        self.structure_1_manager_login()
        # column 1 is "subject"
        asc = self._manager_all(_dt_args(column=1, direction="asc"))
        desc = self._manager_all(_dt_args(column=1, direction="desc"))
        self.assertEqual([r[1] for r in asc['data']], ['Ticket 1', 'Ticket 2'])
        self.assertEqual([r[1] for r in desc['data']], ['Ticket 2', 'Ticket 1'])

    def test_length_all_records(self):
        self.structure_1_manager_login()
        result = self._manager_all(_dt_args(length=-1))
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['recordsTotal'], 2)

    def test_empty_value_column(self):
        self.structure_1_manager_login()
        # falsy attribute values are rendered as empty strings
        Ticket.objects.filter(pk=self.ticket.pk).update(subject='', priority=99)
        result = self._manager_all(_dt_args(search=_search(text=self.ticket.code)))
        self.assertEqual(result['data'][0][1], '')
        # callable columns returning None (get_priority with an unknown
        # priority level) are rendered as empty strings
        self.assertEqual(result['data'][0][6], '')

    def test_user_draft_ticket(self):
        self.structure_1_manager_login()
        result = self._post('uni_ticket:user_draft_ticket_json', _dt_args())
        self.assertEqual(result['recordsTotal'], 0)

        Ticket.objects.filter(pk=self.ticket.pk).update(draft=True)
        result = self._post('uni_ticket:user_draft_ticket_json', _dt_args())
        self.assertEqual(result['recordsTotal'], 1)
        self.assertEqual(result['data'][0][2], self.ticket.code)

    def test_user_views_show_priority(self):
        self.structure_1_manager_login()
        Ticket.objects.filter(pk=self.ticket.pk).update(is_closed=True)
        url_names = ('uni_ticket:user_all_tickets_json',
                     'uni_ticket:user_draft_ticket_json',
                     'uni_ticket:user_unassigned_ticket_json',
                     'uni_ticket:user_opened_ticket_json',
                     'uni_ticket:user_closed_ticket_json')
        with mock.patch('uni_ticket.views.datatables.SIMPLE_USER_SHOW_PRIORITY', True):
            for url_name in url_names:
                result = self._post(url_name, _dt_args())
                for row in result['data']:
                    # priority column added
                    self.assertEqual(len(row), 8)
        # all tickets / closed tickets with default columns
        result = self._post('uni_ticket:user_closed_ticket_json', _dt_args())
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(len(result['data'][0]), 7)

    def test_user_ticket_queryset_search(self):
        self.structure_1_manager_login()
        Ticket.objects.filter(pk=self.ticket.pk).update(is_closed=True)
        # user_closed_ticket/user_draft_ticket build a Ticket queryset:
        # search filters must work without the "ticket__" prefix
        url_name = 'uni_ticket:user_closed_ticket_json'
        result = self._post(url_name, _dt_args(search=_search(text=self.ticket.code)))
        self.assertEqual(result['recordsFiltered'], 1)
        self.assertEqual(result['data'][0][2], self.ticket.code)
        result = self._post(url_name, _dt_args(search=_search(text="no-match")))
        self.assertEqual(result['recordsFiltered'], 0)
        year = str(self.ticket.created.year)
        result = self._post(url_name, _dt_args(search=_search(
            year=year,
            category=self.category_1_str_1.slug,
            structure=self.structure_1.slug)))
        self.assertEqual(result['recordsFiltered'], 1)
        result = self._post(url_name, _dt_args(search=_search(year="last_week")))
        self.assertEqual(result['recordsFiltered'], 1)

        # ordering works on Ticket querysets too (column 2 is the code)
        Ticket.objects.filter(pk=self.ticket_2.pk).update(is_closed=True)
        codes = sorted([str(self.ticket.code), str(self.ticket_2.code)])
        result = self._post(url_name, _dt_args(column=2, direction='asc'))
        self.assertEqual([row[2] for row in result['data']], codes)
        result = self._post(url_name, _dt_args(column=2, direction='desc'))
        self.assertEqual([row[2] for row in result['data']], codes[::-1])

    def test_operator_and_manager_ordering(self):
        # take ticket so that operator views have data
        self.structure_1_manager_login()
        assignment = TicketAssignment.objects.filter(ticket=self.ticket).first()
        response = self.client.post(reverse('uni_ticket:manager_manage_ticket',
                                            kwargs={'structure_slug': self.structure_1.slug,
                                                    'ticket_id': self.ticket.code}),
                                    {'priority': 0, 'office': assignment.office},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        result = self._post('uni_ticket:manager_my_opened_ticket_json',
                            _dt_args(column=1, direction="desc"),
                            structure_slug=self.structure_1.slug)
        self.assertEqual([r[2] for r in result['data']], [self.ticket.code])

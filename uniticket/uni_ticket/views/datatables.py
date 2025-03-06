import copy
import datetime
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from datatables_ajax.datatables import DjangoDatatablesServerProc
from uni_ticket.decorators import is_manager, is_operator
from uni_ticket.models import Ticket, TicketAssignment
from uni_ticket.settings import SIMPLE_USER_SHOW_PRIORITY
from uni_ticket.utils import get_datetime_delta, visible_tickets_to_user


_ticket_columns = [
    "pk",
    "subject",
    "code",
    "get_category",
    "created",
    "get_owners_html",
    "get_priority",
    "get_status_table",
]
_no_priority = [
    "pk",
    "subject",
    "code",
    "get_category",
    "created",
    "get_owners_html",
    "get_status_table",
]


class TicketDTD(DjangoDatatablesServerProc):

    def get_queryset(self):
        """
        Sets DataTable tickets common queryset
        """
        self.aqs = self.queryset
        if self.search_key:
            params = json.loads(self.search_key)
            year = params["year"]
            text = params["text"]
            category = params["category"]
            structure = params["structure"]
            if year:
                if year.isnumeric():
                    self.aqs = self.aqs.filter(ticket__created__year=year)
                else:
                    days = 7 if year == "last_week" else 30
                    delta_day = get_datetime_delta(days=days)
                    self.aqs = self.aqs.filter(ticket__created__gte=delta_day)
            if category:
                self.aqs = self.aqs.filter(
                    ticket__input_module__ticket_category__slug=category,
                    ticket__input_module__ticket_category__organizational_structure__slug=structure,
                )
            if text:
                self.aqs = self.aqs.filter(
                    Q(ticket__code__icontains=text)
                    | Q(ticket__subject__icontains=text)
                    | Q(ticket__created_by__last_name__icontains=text)
                    | Q(ticket__compiled_by__last_name__icontains=text)
                )

    def fill_data(self):
        """
        overload me if you need some clean up
        """
        if not self.fqs:
            self.get_paging()

        tickets = []
        for entry in self.fqs:
            t = Ticket.objects.filter(pk=entry)\
                                 .select_related('created_by',
                                                 'compiled_by',
                                                 'input_module__ticket_category',
                                                 'closed_by')
            tickets.append(t.first())

        for r in tickets:
            cleaned_data = []
            for e in self.columns:
                # this avoid null json value
                # v = getattr(r, e)
                v = r.get(e, None) if type(r) == dict else getattr(r,e)
                if v:
                    if isinstance(v, datetime.datetime):
                        default_datetime_format = settings.DEFAULT_DATETIME_FORMAT
                        vrepr = self._make_aware(v).strftime(default_datetime_format)
                    elif isinstance(v, datetime.date):
                        default_date_format = settings.DEFAULT_DATE_FORMAT
                        vrepr = v.strftime(default_date_format)
                    elif callable(v):
                        vrepr = str(v())
                    else:
                        vrepr = v.__str__()
                else:
                    vrepr = ''
                cleaned_data.append(vrepr)

            self.d['data'].append( cleaned_data )
        self.d['recordsTotal'] = self.queryset.count()
        self.d['recordsFiltered'] = self.aqs.count()

    def get_ordering(self):
        """
           overload me if you need different ordering approach
        """
        if not self.aqs:
            self.get_queryset()

        # if lenght is -1 means ALL the records, sliceless
        if self.lenght == -1:
            self.lenght = self.aqs.count()

        # fare ordinamento qui
        # 'order[0][column]': ['2'],
        # bisogna mappare la colonna con il numero di sequenza eppoi
        # fare order_by
        if self.order_col:
            self.col_name = f'ticket__{self.columns[self.order_col]}'
            if self.order_dir == 'asc':
                self.aqs = self.aqs.order_by(self.col_name)
            else:
                self.aqs = self.aqs.order_by('-'+self.col_name)


@csrf_exempt
@login_required
def user_all_tickets(request):
    """
    Returns all tickets opened by user

    :return: JsonResponse
    """
    columns = _no_priority
    if SIMPLE_USER_SHOW_PRIORITY:
        columns = _ticket_columns

    tickets = TicketAssignment.objects.filter(
        Q(ticket__created_by=request.user) |
        Q(ticket__compiled_by=request.user)
    ).values_list('ticket__pk', flat=True)\
    .order_by("ticket__priority", "-ticket__created")\
    .distinct()

    dtd = TicketDTD(request, tickets, columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
def user_unassigned_ticket(request):
    """
    Returns all unassigned tickets opened by user

    :return: JsonResponse
    """
    columns = _no_priority
    if SIMPLE_USER_SHOW_PRIORITY:
        columns = _ticket_columns

    tickets = TicketAssignment.objects.filter(
        Q(ticket__created_by=request.user) |
        Q(ticket__compiled_by=request.user),
        Q(taken_date__isnull=True) | Q(follow=False),
        ticket__is_closed=False,
    ).values_list('ticket__pk', flat=True)\
    .order_by("ticket__priority", "-ticket__created")\
    .distinct()

    to_exclude = TicketAssignment.objects.filter(
        Q(ticket__created_by=request.user) |
        Q(ticket__compiled_by=request.user),
        ticket__is_closed=False,
        follow=True,
        taken_date__isnull=False
    ).values_list('ticket__pk', flat=True)\
    .order_by("ticket__priority", "-ticket__created")\
    .distinct()

    tickets = tickets.exclude(ticket__pk__in=to_exclude)
    dtd = TicketDTD(request, tickets, columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
def user_opened_ticket(request):
    """
    Returns all assigned and not closed tickets opened by user

    :return: JsonResponse
    """
    columns = _no_priority
    if SIMPLE_USER_SHOW_PRIORITY:
        columns = _ticket_columns

    tickets = TicketAssignment.objects.filter(
        Q(ticket__created_by=request.user) |
        Q(ticket__compiled_by=request.user),
        ticket__is_closed=False,
        taken_date__isnull=False,
        follow=True
    ).values_list('ticket__pk', flat=True)\
    .order_by("ticket__priority", "-ticket__created")\
    .distinct()

    dtd = TicketDTD(request, tickets, columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
def user_closed_ticket(request):
    """
    Returns all closed tickets opened by user

    :return: JsonResponse
    """
    columns = _no_priority
    if SIMPLE_USER_SHOW_PRIORITY:
        columns = _ticket_columns

    tickets = TicketAssignment.objects.filter(
        Q(ticket__created_by=request.user) |
        Q(ticket__compiled_by=request.user),
        ticket__is_closed=True
    ).values_list('ticket__pk', flat=True)\
    .order_by("-ticket__created")\
    .distinct()

    dtd = TicketDTD(request, tickets, columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_manager
def manager_all_tickets(request, structure_slug, structure):
    """
    Returns all not closed tickets managed by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                        priority_first=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_manager
def manager_unassigned_ticket(request, structure_slug, structure):
    """
    Returns all unassigned tickets managed by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                        closed=False,
                                                        taken=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_manager
def manager_opened_ticket(request, structure_slug, structure):
    """
    Returns all assigned and not closed tickets managed by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                        closed=False,
                                                        taken=True)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_manager
def manager_my_opened_ticket(request, structure_slug, structure):
    """
    Returns all assigned and not closed tickets taken by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                        closed=False,
                                                        taken=True,
                                                        taken_by=request.user)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_manager
def manager_closed_ticket(request, structure_slug, structure):
    """
    Returns all closed tickets managed by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                        closed=True,
                                                        priority_first=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_operator
def operator_all_tickets(request, structure_slug, structure, office_employee):
    """
    Returns all not closed tickets managed by operator

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: operator structure slug
    :param structure: operator structure (from @is_operator)
    :param office_employee: queryset with operator and his offices (from @is_operator)

    :return: JsonResponse
    """
    tickets = visible_tickets_to_user(request.user, structure, office_employee)
    # is_closed=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_operator
def operator_unassigned_ticket(request, structure_slug, structure, office_employee):
    """
    Returns all unassigned tickets managed by operator

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: operator structure slug
    :param structure: operator structure (from @is_operator)
    :param office_employee: queryset with operator and his offices (from @is_operator)

    :return: JsonResponse
    """
    tickets = visible_tickets_to_user(user=request.user,
                                      structure=structure,
                                      office_employee=office_employee,
                                      closed=False,
                                      taken=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_operator
def operator_opened_ticket(request, structure_slug, structure, office_employee):
    """
    Returns all assigned and not closed tickets managed by operator

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: operator structure slug
    :param structure: operator structure (from @is_operator)
    :param office_employee: queryset with operator and his offices (from @is_operator)

    :return: JsonResponse
    """
    tickets = visible_tickets_to_user(user=request.user,
                                      structure=structure,
                                      office_employee=office_employee,
                                      closed=False,
                                      taken=True)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_operator
def operator_my_opened_ticket(request, structure_slug, structure, office_employee):
    """
    Returns all assigned and not closed tickets taken by operator

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: operator structure slug
    :param structure: operator structure (from @is_operator)
    :param office_employee: queryset with operator and his offices (from @is_operator)

    :return: JsonResponse
    """
    tickets = visible_tickets_to_user(user=request.user,
                                      structure=structure,
                                      office_employee=office_employee,
                                      closed=False,
                                      taken=True,
                                      taken_by=request.user)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())


@csrf_exempt
@login_required
@is_operator
def operator_closed_ticket(request, structure_slug, structure, office_employee):
    """
    Returns all closed tickets managed by operator

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: operator structure slug
    :param structure: operator structure (from @is_operator)
    :param office_employee: queryset with operator and his offices (from @is_operator)

    :return: JsonResponse
    """
    tickets = visible_tickets_to_user(user=request.user,
                                      structure=structure,
                                      office_employee=office_employee,
                                      closed=True,
                                      priority_first=False)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())

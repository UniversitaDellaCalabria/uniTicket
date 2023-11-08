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
    def __init__(self, request, queryset, columns, direct_queryset=False):
        super().__init__(request, queryset, columns)
        self.direct_queryset = direct_queryset

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
                    | Q(ticket__description__icontains=text)
                    | Q(ticket__created_by__first_name__icontains=text)
                    | Q(ticket__created_by__last_name__icontains=text)
                    | Q(ticket__compiled_by__first_name__icontains=text)
                    | Q(ticket__compiled_by__last_name__icontains=text)
                    #| Q(taken_by__first_name__icontains=text)
                    #| Q(taken_by__last_name__icontains=text)
                    | Q(ticket__closed_by__first_name__icontains=text)
                    | Q(ticket__closed_by__last_name__icontains=text)
                    | Q(ticket__input_module__ticket_category__name__icontains=text)
                    | Q(ticket__created__icontains=text)
                )

    def fill_data(self):
        """
        overload me if you need some clean up
        """
        if not self.fqs:
            self.get_paging()

        queryset = self.fqs
        if not self.direct_queryset:
            queryset = Ticket.objects.filter(code__in=list(self.fqs))\
                                    .select_related('created_by',
                                                    'compiled_by',
                                                    'input_module__ticket_category',
                                                    'closed_by')

        # for r in self.fqs:
        for r in queryset:
            cleaned_data = []
            for e in self.columns:
                # this avoid null json value
                v = getattr(r, e)
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
    ticket_list = Ticket.objects.filter(
        Q(created_by=request.user) | Q(compiled_by=request.user)
    ).select_related('created_by',
                     'compiled_by',
                     'closed_by',
                     'input_module__ticket_category')
    dtd = TicketDTD(request, ticket_list, columns, True)
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
    ticket_list = Ticket.objects.filter(
        Q(created_by=request.user) | Q(compiled_by=request.user),
        is_closed=False,
        assigned_date__isnull=True
    ).select_related('created_by',
                     'compiled_by',
                     'input_module__ticket_category')
    dtd = TicketDTD(request, ticket_list, columns, True)
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
    ticket_list = Ticket.objects.filter(
        Q(created_by=request.user) | Q(compiled_by=request.user),
        is_closed=False,
        assigned_date__isnull=False
    ).select_related('created_by',
                     'compiled_by',
                     'input_module__ticket_category')
    dtd = TicketDTD(request, ticket_list, columns, True)
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
    ticket_list = Ticket.objects.filter(
        Q(created_by=request.user) | Q(compiled_by=request.user),
        is_closed=True
    ).select_related('created_by',
                     'compiled_by',
                     'closed_by',
                     'input_module__ticket_category')
    dtd = TicketDTD(request, ticket_list, columns, True)
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
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure)
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
                                                        closed=True)
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
                                      closed=True)
    dtd = TicketDTD(request, tickets, _ticket_columns)
    return JsonResponse(dtd.get_dict())

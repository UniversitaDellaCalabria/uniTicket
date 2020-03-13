import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from datatables_ajax.datatables import DjangoDatatablesServerProc
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOfficeEmployee)
from uni_ticket.decorators import is_manager, is_operator
from uni_ticket.models import Ticket, TicketAssignment
from uni_ticket.utils import visible_tickets_to_user


_ticket_columns = ['pk','code','subject','get_category',
                   'created','get_priority','get_status']
_no_priority = ['pk','code','subject','get_category',
                'created','get_status']


class TicketDTD(DjangoDatatablesServerProc):

    def get_queryset(self):
        """
        Sets DataTable tickets common queryset
        """
        if self.search_key:
            params = json.loads(self.search_key)
            year = params['year']
            text = params['text']
            if not year and not text:
                self.aqs = self.queryset
            if year:
                self.aqs = self.queryset.filter(created__year=year)
            if text:
                queryset = self.queryset
                if self.aqs: queryset = self.aqs
                self.aqs = queryset.filter(
                    Q(code__icontains=text) | \
                    Q(subject__icontains=text) | \
                    Q(input_module__ticket_category__name__icontains=text) | \
                    Q(created__icontains=text))
        else: self.aqs = self.queryset

@csrf_exempt
@login_required
def user_all_tickets(request):
    """
    Returns all tickets opened by user

    :return: JsonResponse
    """
    columns = _ticket_columns
    if settings.SIMPLE_USER_HIDE_PRIORITY:
        columns = _no_priority
    ticket_list = Ticket.objects.filter(created_by=request.user)
    dtd = TicketDTD( request, ticket_list, columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@login_required
def user_unassigned_ticket(request):
    """
    Returns all unassigned tickets opened by user

    :return: JsonResponse
    """
    columns = _ticket_columns
    if settings.SIMPLE_USER_HIDE_PRIORITY:
        columns = _no_priority
    ticket_list = Ticket.objects.filter(created_by=request.user,
                                        is_taken=False,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@login_required
def user_opened_ticket(request):
    """
    Returns all assigned and not closed tickets opened by user

    :return: JsonResponse
    """
    columns = _ticket_columns
    if settings.SIMPLE_USER_HIDE_PRIORITY:
        columns = _no_priority
    ticket_list = Ticket.objects.filter(created_by=request.user,
                                        is_taken=True,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@login_required
def user_closed_ticket(request):
    """
    Returns all closed tickets opened by user

    :return: JsonResponse
    """
    columns = _ticket_columns
    if settings.SIMPLE_USER_HIDE_PRIORITY:
        columns = _no_priority
    ticket_list = Ticket.objects.filter(created_by=request.user,
                                        is_closed=True)
    dtd = TicketDTD( request, ticket_list, columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@is_manager
def manager_not_closed_ticket(request, structure_slug, structure):
    """
    Returns all not closed tickets managed by manager

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: manager structure slug
    :param structure: manager structure (from @is_manager)

    :return: JsonResponse
    """
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure)
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
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
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure)
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_taken=False,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
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
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure)
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_taken=True,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
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
    tickets = TicketAssignment.get_ticket_per_structure(structure=structure)
    ticket_list = Ticket.objects.filter(code__in=tickets, is_closed=True)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@is_operator
def operator_not_closed_ticket(request, structure_slug,
                               structure, office_employee):
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
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@is_operator
def operator_unassigned_ticket(request, structure_slug,
                               structure, office_employee):
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
    tickets = visible_tickets_to_user(request.user, structure, office_employee)
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_taken=False,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@is_operator
def operator_opened_ticket(request, structure_slug,
                           structure, office_employee):
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
    tickets = visible_tickets_to_user(request.user,
                                      structure,
                                      office_employee)
    ticket_list = Ticket.objects.filter(code__in=tickets,
                                        is_taken=True,
                                        is_closed=False)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

@csrf_exempt
@is_operator
def operator_closed_ticket(request, structure_slug,
                           structure, office_employee):
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
    tickets = visible_tickets_to_user(request.user, structure, office_employee)
    ticket_list = Ticket.objects.filter(code__in=tickets, is_closed=True)
    dtd = TicketDTD( request, ticket_list, _ticket_columns )
    return JsonResponse(dtd.get_dict())

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee)

from .models import Ticket, TicketAssignment
from .utils import (custom_message,
                    user_is_manager,
                    user_is_operator,
                    user_is_office_operator,
                    user_offices_list)


def is_manager(func_to_decorate):
    """
    Check if user is manager in some OrganizationalStructure
    Employee of structure default office + staff in Django
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs['structure_slug']
        structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                           is_active=True).first()
        if user_is_manager(request.user, structure):
            original_kwargs['structure'] = structure
            return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(request,
                              _("Accesso da manager non consentito"),
                              structure_slug=structure_slug)
    return new_func

def is_operator(func_to_decorate):
    """
    Check if user is employee in some Office
    Not staff in Django + employee in structure default office
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs['structure_slug']
        structure = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        if user_is_manager(request.user, structure):
            return custom_message(request,
                                  _("Accesso da operatore non consentito."
                                    " Sei un manager."),
                                  structure_slug=structure_slug)
        oe = user_is_operator(request.user, structure)
        if oe:
            original_kwargs['office_employee'] = oe
            original_kwargs['structure'] = structure
            return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(request,
                              _("Accesso da operatore non consentito"),
                              structure_slug=structure_slug)
    return new_func

def is_the_owner(func_to_decorate):
    """
    Check if the current user is the owner of the ticket
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs['ticket_id']
        ticket = get_object_or_404(Ticket, code = ticket_id)
        user = request.user
        if not ticket.check_if_owner(user):
            return custom_message(request, _("Hai accesso solo ai ticket"
                                             " aperti da te!"))
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func

def has_admin_privileges(func_to_decorate):
    """
    Manager or Operator with privileges to manage ticket
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs['structure_slug']
        structure = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        original_kwargs['structure'] = structure
        ticket_id = original_kwargs['ticket_id']
        ticket = get_object_or_404(Ticket, code=ticket_id)
        is_manager = user_is_manager(request.user, structure)

        can_manage = False
        message_string = _("Permesso di accesso al ticket <b>{}</b> negato".format(ticket))

        if is_manager:
            can_manage = ticket.is_followed_in_structure(structure=structure)
            if not can_manage:
                messages.add_message(request, messages.ERROR,
                                     message_string)
                return redirect('uni_ticket:manage',
                                structure_slug=structure_slug)
            original_kwargs['can_manage'] = can_manage
            return func_to_decorate(*original_args, **original_kwargs)

        office_employee = user_is_operator(request.user, structure)
        offices = user_offices_list(office_employee)
        can_manage = ticket.is_followed_by_one_of_offices(offices=offices)

        if not can_manage:
            messages.add_message(request, messages.ERROR,
                                     message_string)
            return redirect('uni_ticket:manage',
                            structure_slug=structure_slug)

        original_kwargs['can_manage'] = can_manage
        # Check if user is operator of the ticket office
        is_operator = False
        for office in offices:
            if user_is_office_operator(request.user, office):
                is_operator = True
                break
        if is_operator: return func_to_decorate(*original_args, **original_kwargs)
        messages.add_message(request, messages.ERROR,
                             message_string)
        return redirect('uni_ticket:manage',
                        structure_slug=structure_slug)
    return new_func

def has_access_to_ticket(func_to_decorate):
    """
    Check if current user has access to the ticket
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs['ticket_id']
        ticket = get_object_or_404(Ticket, code=ticket_id)
        user = request.user
        original_kwargs['ticket'] = ticket
        # Se il ticket è stato creato da me, ok!
        if ticket.check_if_owner(user):
            return func_to_decorate(*original_args, **original_kwargs)

        structures = ticket.get_assigned_to_structures()
        # Check if user is manager of the ticket structure
        for struct in structures:
            if user_is_manager(user, struct):
                return func_to_decorate(*original_args, **original_kwargs)

        offices = ticket.get_assigned_to_offices()
        # Check if user is operator of the ticket office
        for office in offices:
            if user_is_office_operator(user, office):
                return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(request, _("Accesso al ticket negato."))
    return new_func

def ticket_is_not_taken(func_to_decorate):
    """
    Check if current ticket is not taken
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs['ticket_id']
        ticket = get_object_or_404(Ticket, code=ticket_id)
        if ticket.is_taken:
            return custom_message(request, _("Il ticket è stato preso in carico"))
        if ticket.is_closed:
            return custom_message(request, _("Il ticket è chiuso"))
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func

def ticket_assigned_to_structure(func_to_decorate):
    """
    Check if current ticket is assigned to a structure
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs['structure_slug']
        ticket_id = original_kwargs['ticket_id']
        ticket = get_object_or_404(Ticket, code=ticket_id)
        original_kwargs['ticket'] = ticket
        struct = get_object_or_404(OrganizationalStructure,
                                   slug=structure_slug,
                                   is_active=True)
        if struct not in ticket.get_assigned_to_structures():
            return custom_message(request, _("Il ticket non è stato assegnato"
                                             " a questa struttura"),
                                  structure_slug=structure_slug)
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func

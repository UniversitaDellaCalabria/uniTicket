from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _

from organizational_area.models import OrganizationalStructure
from uni_ticket.settings import READONLY_COMPETENCE_OVER_TICKET

from .models import Ticket, TicketAssignment
from .utils import (
    custom_message,
    user_is_in_default_office,
    user_is_manager,
    user_is_operator,
    user_manage_office,
    user_offices_list,
)


def is_manager(func_to_decorate):
    """
    Check if user is manager in some OrganizationalStructure
    Employee of structure default office + staff in Django
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs["structure_slug"]
        structure = OrganizationalStructure.objects.filter(
            slug=structure_slug, is_active=True
        ).first()
        if user_is_manager(request.user, structure):
            original_kwargs["structure"] = structure
            return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(
            request,
            _("Accesso da manager non consentito"),
            structure_slug=structure_slug,
        )

    return new_func


def is_operator(func_to_decorate):
    """
    Check if user is employee in some Office
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs["structure_slug"]
        structure = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )
        if user_is_manager(request.user, structure):
            return custom_message(
                request,
                _("Accesso da operatore non consentito." " Sei un manager."),
                structure_slug=structure_slug,
            )
        oe = user_is_operator(request.user, structure)
        if oe:
            original_kwargs["office_employee"] = oe
            original_kwargs["structure"] = structure
            return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(
            request,
            _("Accesso da operatore non consentito"),
            structure_slug=structure_slug,
        )

    return new_func


def is_the_owner(func_to_decorate):
    """
    Check if the current user is the owner of the ticket
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        user = request.user
        if not ticket.check_if_owner(user):
            return custom_message(
                request, _("Hai accesso solo ai ticket" " aperti da te!")
            )
        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def has_admin_privileges(func_to_decorate):
    """
    Manager or Operator with privileges to manage ticket
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs["structure_slug"]
        structure = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )
        original_kwargs["structure"] = structure
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        # is_manager = user_is_manager(request.user, structure)

        can_manage = {}
        message_string = _(
            "Permesso di accesso al ticket " "<b>{}</b> negato".format(ticket)
        )

        # if is_manager:
        if user_is_in_default_office(request.user, structure):
            can_manage = ticket.is_followed_in_structure(structure=structure)

            if not can_manage:
                messages.add_message(request, messages.ERROR, message_string)
                return redirect("uni_ticket:manage", structure_slug=structure_slug)
            original_kwargs["can_manage"] = can_manage
            return func_to_decorate(*original_args, **original_kwargs)

        office_employee_list = user_is_operator(request.user, structure)
        offices = user_offices_list(office_employee_list)
        can_manage = ticket.is_followed_by_one_of_offices(offices=offices)

        if not can_manage:
            messages.add_message(request, messages.ERROR, message_string)
            return redirect("uni_ticket:manage", structure_slug=structure_slug)

        original_kwargs["can_manage"] = can_manage
        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def has_access_to_ticket(func_to_decorate):
    """
    Check if current user has access to the ticket
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        user = request.user
        original_kwargs["ticket"] = ticket

        # Se il ticket è stato creato da me, ok!
        if ticket.check_if_owner(user):
            return func_to_decorate(*original_args, **original_kwargs)

        # Select all offices that follow the ticket (readonly too)
        offices = ticket.get_assigned_to_offices(ignore_follow=False)
        # Check if user is operator of the ticket office
        for office in offices:
            if user_manage_office(user, office):
                return func_to_decorate(*original_args, **original_kwargs)
        return custom_message(request, _("Accesso al ticket negato."))

    return new_func


def ticket_is_not_taken_and_not_closed(func_to_decorate):
    """
    Check if current ticket is not taken
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        assignments_count = TicketAssignment.objects.filter(
            ticket=ticket).count()
        if ticket.has_been_taken() or assignments_count > 1:
            return custom_message(request, _("Il ticket è stato assegnato"))
        if ticket.is_closed:
            return custom_message(request, _("Il ticket è chiuso"))
        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def ticket_is_taken_and_not_closed(func_to_decorate):
    """
    Check if current ticket is taken
    """

    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        if not ticket.has_been_taken():
            return custom_message(request, _("Il ticket non è assegnato"))
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
        structure_slug = original_kwargs["structure_slug"]
        ticket_id = original_kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, code=ticket_id)
        original_kwargs["ticket"] = ticket
        struct = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )
        if struct not in ticket.get_assigned_to_structures():
            return custom_message(
                request,
                _("Il ticket non è stato assegnato" " a questa struttura"),
                structure_slug=structure_slug,
            )
        return func_to_decorate(*original_args, **original_kwargs)

    return new_func


def ticket_is_taken_for_employee(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure_slug = original_kwargs["structure_slug"]
        ticket_id = original_kwargs["ticket_id"]

        can_manage = original_kwargs["can_manage"]
        if can_manage["follow"] and can_manage["readonly"]:
            messages.add_message(
                request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )

        ticket = get_object_or_404(Ticket, code=ticket_id)
        if not ticket.has_been_taken(  # user=request.user,
            structure=original_kwargs["structure"], exclude_readonly=True
        ):
            m = _(
                "Il ticket deve essere prima preso in carico"
                " per poter essere gestito"
            )
            messages.add_message(request, messages.ERROR, m)
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        return func_to_decorate(*original_args, **original_kwargs)

    return new_func

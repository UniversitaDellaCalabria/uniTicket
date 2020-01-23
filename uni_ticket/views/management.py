import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from django_form_builder.utils import get_as_dict, get_labeled_errors
from organizational_area.models import *
from uni_ticket.decorators import (has_admin_privileges,
                                   ticket_assigned_to_structure,
                                   ticket_is_not_taken)
from uni_ticket.forms import *
from uni_ticket.models import *
from uni_ticket.settings import (NO_MORE_COMPETENCE_OVER_TICKET,
                                 PRIORITY_LEVELS,
                                 READONLY_COMPETENCE_OVER_TICKET)
from uni_ticket.utils import *


@login_required
def manage_opened_ticket_url(request, structure_slug):
    """
    Makes URL redirect to opened ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_opened_ticket'.format(user_type),
                    structure_slug)

@login_required
def manage_unassigned_ticket_url(request, structure_slug):
    """
    Makes URL redirect to unassigned ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_unassigned_ticket'.format(user_type),
                    structure_slug)

@login_required
def manage_closed_ticket_url(request, structure_slug):
    """
    Makes URL redirect to closed ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_closed_ticket'.format(user_type),
                    structure_slug)

@login_required
def manage_not_closed_ticket_url(request, structure_slug):
    """
    Makes URL redirect to not closed ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_not_closed_ticket'.format(user_type),
                    structure_slug)

@login_required
def manage_ticket_url(request, structure_slug):
    """
    Builds a fake URL to ticket detail page for datatables <href> tags

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: render
    """
    return custom_message(request, _("Permesso negato"), structure_slug)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def manage_ticket_url_detail(request, structure_slug, ticket_id,
                             structure, can_manage, ticket):
    """
    Redirects URL ticket detail page depending of user role

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket(from @ticket_assigned_to_structure)

    :param structure_slug: slug of structure to manage
    :param ticket_id: code of ticket
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    user = request.user
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_manage_ticket'.format(user_type),
                    structure_slug=structure_slug,
                    ticket_id=ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_detail(request, structure_slug, ticket_id,
                  structure, can_manage, ticket, office_employee=None):
    """
    Ticket detail management page

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: slug of structure to manage
    :param ticket_id: code
    :param structure: OrganizationalStructure (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param office_employee: operator offices queryset (from @is_operator)
    :param ticket: Ticket (from @ticket_assigned_to_structure)

    :return: render
    """
    title = _("Gestione ticket")
    sub_title = ticket
    user = request.user
    user_type = get_user_type(request.user, structure)
    json_dict = json.loads(ticket.modulo_compilato)
    ticket_details = get_as_dict(compiled_module_json=json_dict,
                                 allegati=False,
                                 formset_management=False)
    priority = ticket.get_priority()
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path_allegato(ticket)
    ticket_form = ticket.input_module.get_form(files=allegati,
                                               remove_filefields=False)
    ticket_logs = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(ticket).pk,
                                          object_id=ticket.pk)
    ticket_task = Task.objects.filter(ticket=ticket)
    ticket_dependences = ticket.get_dependences()
    assigned_to = []
    ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)
    form = PriorityForm(data={'priorita':ticket.priority})
    if request.method == 'POST':
        if can_manage['readonly']:
            messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)
        if ticket.is_closed:
            messages.add_message(request, messages.ERROR,
                                 _("Impossibile modificare un ticket chiuso"))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)

        form = PriorityForm(request.POST)
        if form.is_valid():
            priority = request.POST.get('priorita')
            priority_text = dict(PRIORITY_LEVELS).get(priority)
            if not ticket.is_taken:
                ticket.is_taken = True
                ticket.save(update_fields = ['is_taken'])
                msg = _("Preso in carico. Priorità assegnata: {}".format(priority_text))
            else:
                msg = _("Priorità assegnata: {}".format(priority_text))
            ticket.priority = priority
            ticket.save(update_fields = ['priority'])
            ticket.update_log(user=request.user,
                                  note=msg)
            messages.add_message(request, messages.SUCCESS,
                                 _("Ticket <b>{}</b> aggiornato"
                                   " con successo".format(ticket.code)))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d = {'allegati': allegati,
         'dependences': ticket_dependences,
         'details': ticket_details,
         'form': form,
         'path_allegati': path_allegati,
         'priority': priority,
         'structure': structure,
         'sub_title': sub_title,
         'ticket': ticket,
         'ticket_assignments': ticket_assignments,
         'ticket_form': ticket_form,
         'logs': ticket_logs,
         'ticket_task': ticket_task,
         'title': title,}
    template = "{}/ticket_detail.html".format(user_type)
    return render(request, template, d)

@login_required
def tickets(request, structure_slug, structure, office_employee=None):
    """
    All tickets to manage

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: the slug of structure to manage
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/tickets.html".format(user_type)
    title = _('Gestione ticket')
    sub_title = _("Aperti o non ancora presi in carico")
    structure_ticket = TicketAssignment.get_ticket_per_structure(structure)
    non_gestiti = Ticket.objects.filter(pk__in=structure_ticket,
                                        is_taken=False,
                                        is_closed=False)
    aperti = Ticket.objects.filter(pk__in=structure_ticket,
                                   is_taken=True,
                                   is_closed=False)
    chiusi = Ticket.objects.filter(pk__in=structure_ticket,
                                   is_closed=True)

    d = {'ticket_aperti': aperti,
         'ticket_chiusi': chiusi,
         'ticket_non_gestiti': non_gestiti,
         'structure': structure,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
@ticket_is_not_taken
def ticket_take(request, structure_slug, ticket_id,
                structure, can_manage, ticket,
                office_employee=None):
    """
    Take ticket

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: the slug of structure to manage
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    user = request.user
    ticket.is_taken = True
    ticket.save(update_fields=['is_taken'])
    ticket.update_log(user=request.user,
                          note= _("Preso in carico"))
    messages.add_message(request, messages.SUCCESS,
                         _("Ticket <b>{}</b> preso in carico"
                           " correttamente".format(ticket.code)))
    return redirect('uni_ticket:manage', structure_slug)

@login_required
def ticket_dependence_add_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to add ticket dependence by user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_add_ticket_dependence'.format(user_type),
                    structure_slug, ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_dependence_add_new(request, structure_slug, ticket_id,
                              structure, can_manage, ticket, office_employee=None):
    """
    Adds ticket dependence

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    # Se il ticket non è aperto non è possibile aggiungere dipendenze
    if ticket.is_closed:
        return custom_message(request,
                              _("Il ticket {} è chiuso".format(master_ticket)),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_dependence.html".format(user_type)
    title = _('Aggiungi dipendenza ticket')
    sub_title = '{} ({})'.format(ticket.subject, ticket_id)
    # Lista dei pk dei ticket da cui quello corrente dipende
    ticket_dependences = ticket.get_dependences()
    ticket_dependences_id_list = []
    for td in ticket_dependences:
        if td.master_ticket.pk not in ticket_dependences_id_list:
            ticket_dependences_id_list.append(td.master_ticket.pk)
    form = TicketDependenceForm(structure=structure,
                                ticket_id=ticket.pk,
                                ticket_dependences=ticket_dependences_id_list)
    if request.method == 'POST':
        form = TicketDependenceForm(request.POST,
                                    structure=structure,
                                    ticket_id=ticket.pk,
                                    ticket_dependences=ticket_dependences_id_list)
        if form.is_valid():
            ticket_master_pk = request.POST.get('ticket')
            note = request.POST.get('note')
            master_ticket = get_object_or_404(Ticket, pk=ticket_master_pk)
            # Se il ticket scelto come master dipende da altri ticket
            if Ticket2Ticket.master_is_already_used(master_ticket) or ticket.blocks_some_ticket():
                messages.add_message(request, messages.ERROR,
                                     "Il ticket <b>{}</b> non può essere"
                                     " selezionato poichè risulta già"
                                     " utilizzato in altre dipendenze".format(master_ticket))
                return redirect('uni_ticket:add_ticket_dependence_url',
                                structure_slug=structure_slug,
                                ticket_id=ticket_id)
            t2t = Ticket2Ticket(slave_ticket=ticket,
                                master_ticket=master_ticket,
                                note=note)
            t2t.save()
            ticket.update_log(user = request.user,
                                  note = _("Aggiunta dipendenza dal ticket:"
                                           " <b>{}</b>".format(master_ticket)))
            messages.add_message(request, messages.SUCCESS,
                                 _("Dipendenza dal ticket <b>{}</b>"
                                   " aggiunta con successo".format(master_ticket.code)))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id = ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d = {'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_dependence_remove(request, structure_slug,
                             ticket_id, master_ticket_id,
                             structure, can_manage, ticket):
    """
    Removes ticket dependence

    :type structure_slug: String
    :type ticket_id: String
    :type master_ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param master_ticket_id: master ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    # Se il ticket non è aperto non è possibile rimuovere dipendenze
    if ticket.is_closed:
        return custom_message(request,
                              _("Il ticket {} è chiuso".format(master_ticket)),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    master_ticket = get_object_or_404(Ticket, code=master_ticket_id)
    to_remove = get_object_or_404(Ticket2Ticket,
                                  slave_ticket=ticket,
                                  master_ticket=master_ticket)
    # Se il ticket master che sto eliminando non è assegnato alla struttura corrente
    if structure not in master_ticket.get_assigned_to_structures():
        return custom_message(request,
                              _("Il ticket <b>{}</b> non è stato assegnato"
                                " a questa struttura, pertanto"
                                " non puoi gestirlo".format(master_ticket)),
                              structure_slug=structure.slug)
    else:
        to_remove.delete()
        ticket.update_log(user = request.user,
                              note = _("Rimossa dipendenza dal ticket:"
                                       " <b>{}</b>".format(master_ticket)))
        messages.add_message(request, messages.SUCCESS,
                             _("Dipendenza rimossa correttamente"))
    return redirect('uni_ticket:manage_ticket_url_detail',
                    structure_slug=structure_slug,
                    ticket_id = ticket_id)

@login_required
def ticket_close_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to closing ticket page depending of user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :render: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_close_ticket'.format(user_type),
                    structure_slug, ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_close(request, structure_slug, ticket_id,
                 structure, can_manage, ticket, office_employee=None):
    """
    Closes ticket

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    # Se il ticket non è chiudibile (per dipendenze attive)
    if not ticket.is_closable():
        return custom_message(request,
                              _("Non è possibile chiudere il ticket,"
                                " ci sono dipendenze attive!"),
                              structure_slug=structure.slug)
    title = _('Chiusura del ticket')
    sub_title = ticket
    form = ChiusuraForm()
    if request.method=='POST':
        form = ChiusuraForm(request.POST)
        if form.is_valid():
            motivazione = request.POST.get('note')
            ticket.is_closed = True
            ticket.motivazione_chiusura = motivazione
            ticket.data_chiusura = timezone.now()
            ticket.save(update_fields = ['is_closed',
                                         'motivazione_chiusura',
                                         'data_chiusura'])
            ticket.update_log(user = request.user,
                                  note = _("Chiusura ticket: {}".format(motivazione)))
            messages.add_message(request, messages.SUCCESS,
                                 _("Ticket {} chiuso correttamente".format(ticket)))
            return redirect('uni_ticket:manage', structure_slug)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))

    user_type = get_user_type(request.user, structure)
    template = "{}/ticket_close.html".format(user_type)
    d = {'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_reopen(request, structure_slug, ticket_id,
                  structure, can_manage, ticket):
    """
    Reopen ticket

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    if not ticket.is_closed:
        return custom_message(request, _("Il ticket {} è già aperto"),
                              structure_slug=structure.slug)
    if not ticket.is_taken:
        return custom_message(request, _("Il ticket {} è stato chiuso dall'utente, "
                                         " pertanto non può essere riaperto"),
                              structure_slug=structure.slug)
    ticket.is_closed = False
    ticket.save(update_fields = ['is_closed'])
    ticket.update_log(user=request.user,
                          note= _("Riapertura ticket"))
    messages.add_message(request, messages.SUCCESS,
                         _("Ticket {} riaperto correttamente".format(ticket)))
    return redirect('uni_ticket:manage_ticket_url_detail',
                    structure_slug=structure_slug,
                    ticket_id=ticket_id)

@login_required
def ticket_competence_add_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to adding ticket competence page depending of user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_add_ticket_competence'.format(user_type),
                    structure_slug, ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_competence_add_new(request, structure_slug, ticket_id,
                              structure, can_manage, ticket,
                              office_employee=None):
    """
    Adds new ticket competence (first step)

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    # Se il ticket è chiuso blocca
    if ticket.is_closed:
        return custom_message(request,
                              _("Il ticket {} è chiuso".format(master_ticket)),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_competence.html".format(user_type)
    title = _('Trasferisci competenza ticket')
    sub_title = '{} ({})'.format(ticket.subject, ticket_id)
    strutture = OrganizationalStructure.objects.filter(is_active=True)
    d = {'structure': structure,
         'strutture': strutture,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_competence_add_final(request, structure_slug, ticket_id,
                                str_slug, structure, can_manage, ticket,
                                office_employee=None):
    """
    Adds new ticket competence (second step)

    :type structure_slug: String
    :type ticket_id: String
    :type str_slug: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param str_slug: selected structure slug
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    # Se il ticket è chiuso blocca
    if ticket.is_closed:
        return custom_message(request,
                              _("Il ticket {} è chiuso".format(master_ticket)),
                              structure_slug=structure.slug)
    strutture = OrganizationalStructure.objects.filter(is_active = True)
    # Lista uffici ai quali il ticket è assegnato
    ticket_offices = ticket.get_assigned_to_offices(office_active=False)
    struttura = get_object_or_404(OrganizationalStructure,
                                  slug=str_slug,
                                  is_active=True)
    categorie = TicketCategory.objects.filter(organizational_structure=struttura.pk,
                                              is_active=True)
    if request.method == 'POST':
        category_slug = request.POST.get('category_slug')
        follow_value = request.POST.get('follow')
        readonly_value = request.POST.get('readonly')
        follow = True if follow_value == 'on' else False
        readonly = True if readonly_value == 'on' else False
        # La categoria passata in POST esiste?
        categoria = get_object_or_404(TicketCategory,
                                      slug=category_slug,
                                      organizational_structure=struttura,
                                      is_active=True)
        new_office = structure.get_default_office()
        if categoria.organizational_office:
            new_office = categoria.organizational_office

        if new_office in ticket_offices:
            messages.add_message(request, messages.ERROR,
                                 _("Il ticket è già di competenza"
                                   " dell'ufficio <b>{}</b>, responsabile"
                                   " della categoria <b>{}</b>".format(new_office,
                                                                       categoria)))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)

        messages.add_message(request, messages.SUCCESS,
                             _("Competenza <b>{}</b> aggiunta"
                               " correttamente".format(new_office)))

        # If not follow anymore
        if not follow:
            abandoned_offices = ticket.block_competence(user=request.user,
                                                        structure=structure,
                                                        allow_readonly=False)
            for off in abandoned_offices:
                ticket.update_log(user=request.user,
                                  note= _("Competenza abbandonata da"
                                          " Ufficio: {}".format(off)))

        # If follow but readonly
        if readonly:
            abandoned_offices = ticket.block_competence(user=request.user,
                                                        structure=structure)
            for off in abandoned_offices:
                ticket.update_log(user=request.user,
                                  note= _("Competenza trasferita da"
                                          " (accesso in sola lettura)"
                                          " Ufficio: {}".format(off)))
        # If follow and want to manage
        ticket.add_competence(office=new_office, user=request.user)
        ticket.update_log(user=request.user,
                          note= _("Nuova competenza: {} - {}"
                                  " - Categoria: {}".format(struttura,
                                                            new_office,
                                                            categoria)))

        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)

    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_competence.html".format(user_type)
    title = _('Trasferisci competenza ticket')
    sub_title = '{} ({})'.format(ticket.subject, ticket_id)
    d = {'can_manage': can_manage,
         'categorie': categorie,
         'structure': structure,
         'structure_slug': str_slug,
         'strutture': strutture,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
def ticket_message_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to add ticket message by user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_ticket_message'.format(user_type),
                    structure_slug, ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def ticket_message(request, structure_slug, ticket_id,
                   structure, can_manage, ticket, office_employee=None):
    """
    View ticket messages

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    title = _("Messaggi")
    sub_title = ticket
    user = request.user
    user_type = get_user_type(request.user, structure)
    # Conversazione utente-operatori
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    form = ReplyForm()

    if ticket.is_open() and can_manage:
        user_replies = ticket_replies.filter(owner=ticket.created_by,
                                             structure=None,
                                             read_by=None)
        for reply in user_replies:
            reply.read_by = request.user
            reply.read_date = timezone.now()
            reply.save(update_fields = ['read_by', 'read_date'])

    if request.method == 'POST':
        if can_manage['readonly']:
            messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)
        # Se il ticket non è aperto non è possibile scrivere
        if not ticket.is_open():
            return custom_message(request, _("Il ticket non è modificabile"),
                                  structure_slug=structure.slug)
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_reply = TicketReply()
            ticket_reply.subject = request.POST.get('subject')
            ticket_reply.text = request.POST.get('text')
            ticket_reply.attachment = request.FILES.get('attachment')
            ticket_reply.ticket = ticket
            ticket_reply.structure = structure
            ticket_reply.owner = request.user
            ticket_reply.save()

            # Send mail to ticket owner
            mail_params = {'hostname': settings.HOSTNAME,
                           'status': _('received'),
                           'ticket': ticket,
                           'user': ticket.created_by
                          }
            m_subject = _('{} - ticket {} message received'.format(settings.HOSTNAME,
                                                                   ticket))
            send_custom_mail(subject=m_subject,
                             body=USER_TICKET_MESSAGE.format(**mail_params),
                             recipient=ticket.created_by)
            # END Send mail to ticket owner

            messages.add_message(request, messages.SUCCESS,
                                 _("Messaggio inviato con successo"))
            return redirect('uni_ticket:manage_ticket_message_url',
                            structure_slug=structure_slug,
                            ticket_id = ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d = {'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'ticket': ticket,
         'ticket_replies': ticket_replies,
         'title': title,}
    template = "{}/ticket_assistance.html".format(user_type)
    return render(request, template, d)

@login_required
def task_add_new_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to add new ticket task according to user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_add_ticket_task'.format(user_type),
                    structure_slug, ticket_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_add_new(request, structure_slug, ticket_id,
                 structure, can_manage, ticket, office_employee=None):
    """
    Add new ticket task

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_task.html".format(user_type)
    title = _('Aggiungi Attività')
    sub_title = '{} ({})'.format(ticket.subject, ticket_id)
    form = TaskForm()
    if request.method == 'POST':
        form = TaskForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_task = Task()
            new_task.subject = request.POST.get('subject')
            new_task.description = request.POST.get('description')
            new_task.attachment = request.FILES.get('attachment')
            new_task.ticket = ticket
            new_task.priority = request.POST.get('priority')
            new_task.created_by = request.user
            new_task.code = uuid_code()
            new_task.save()
            ticket.update_log(user = request.user,
                                  note = _("Aggiunto task:"
                                           " {}".format(new_task)))
            messages.add_message(request, messages.SUCCESS,
                                 _("Task {} creato con successo".format(new_task)))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket.code)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d = {'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_remove(request, structure_slug,
                ticket_id, task_id,
                structure, can_manage, ticket):
    """
    Remove ticket task

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)
    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    delete_file(file_name=task.attachment)
    task.delete()
    ticket.update_log(user = request.user,
                          note = _("Rimosso task: {}".format(task)))
    messages.add_message(request, messages.SUCCESS,
                         _("Task {} rimosso correttamente".format(task)))
    return redirect('uni_ticket:manage_ticket_url_detail',
                    structure_slug=structure_slug,
                    ticket_id = ticket_id)

@login_required
def task_detail_url(request, structure_slug, ticket_id, task_id):
    """
    Makes URL redirect to view ticket task details according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_task_detail'.format(user_type),
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                    task_id=task_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_detail(request, structure_slug, ticket_id, task_id,
                structure, can_manage, ticket, office_employee=None):
    """
    View task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    title = _("Dettaglio attività")
    priority = task.get_priority()
    # allegati = ticket.get_allegati_dict()
    task_logs = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(task).pk,
                                        object_id=task.pk)
    form = PriorityForm(data={'priorita': task.priority})
    if request.method == 'POST':
        if can_manage['readonly']:
            messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)
        if task.is_closed:
            messages.add_message(request, messages.ERROR,
                                 _("Impossibile modificare un'attività chiusa"))
            return redirect('uni_ticket:manage_task_detail_url',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id,
                            task_id=task_id)

        form = PriorityForm(request.POST)
        if form.is_valid():
            priority = request.POST.get('priorita')
            priority_text = dict(PRIORITY_LEVELS).get(priority)
            msg = _("Task {} - Priorità assegnata: {}".format(task,
                                                              priority_text))
            task.priority = priority
            task.save(update_fields = ['priority'])
            task.update_log(user=request.user,
                                note=msg)
            ticket.update_log(user=request.user,
                                  note=msg)
            messages.add_message(request, messages.SUCCESS,
                                 _("Attività aggiornata con successo"))
            return redirect('uni_ticket:manage_task_detail_url',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id,
                            task_id=task_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d={'form': form,
       'priority': priority,
       'structure': structure,
       'sub_title': task,
       'task': task,
       'logs': task_logs,
       'title': title}
    user_type = get_user_type(request.user, structure)
    template = "{}/task_detail.html".format(user_type)
    return render(request, template, d)

@login_required
def task_close_url(request, structure_slug, ticket_id, task_id):
    """
    Makes URL redirect to close ticket task details according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_close_task'.format(user_type),
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                    task_id=task_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_close(request, structure_slug, ticket_id, task_id,
               structure, can_manage, ticket, office_employee=None):
    """
    Closes task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)

    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    # Se il ticket non è chiudibile (per dipendenze attive)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    if task.is_closed:
        return custom_message(request, _("Task già chiuso!"),
                              structure_slug=structure.slug)
    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    title = _('Chiusura del task')
    sub_title = task
    form = ChiusuraForm()
    if request.method=='POST':
        form = ChiusuraForm(request.POST)
        if form.is_valid():
            motivazione = request.POST.get('note')
            task.is_closed = True
            task.motivazione_chiusura = motivazione
            task.data_chiusura = timezone.now()
            task.save(update_fields = ['is_closed',
                                       'motivazione_chiusura',
                                       'data_chiusura'])
            msg = _("Chiusura task: {} - {}".format(task, motivazione))
            task.update_log(user = request.user,
                                note = msg)
            ticket.update_log(user = request.user,
                                  note = msg)
            messages.add_message(request, messages.SUCCESS,
                                 _("Task {} chiuso correttamente".format(task)))
            return redirect('uni_ticket:manage_ticket_url_detail',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    user_type = get_user_type(request.user, structure)
    template = "{}/task_close.html".format(user_type)
    d = {'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'task': task,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_reopen(request, structure_slug, ticket_id, task_id,
                structure, can_manage, ticket):
    """
    Reopen task

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)

    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    # Se il ticket non è chiuso blocca
    if not task.is_closed:
        return custom_message(request, _("Il task è già aperto"),
                              structure_slug=structure.slug)
    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    task.is_closed = False
    task.save(update_fields = ['is_closed'])
    msg = _("Riapertura task {}".format(task))
    task.update_log(user=request.user,
                        note=msg)
    ticket.update_log(user=request.user,
                          note=msg)
    messages.add_message(request, messages.SUCCESS,
                         _("Task {} riaperto correttamente".format(task)))
    return redirect('uni_ticket:manage_ticket_url_detail',
                    structure_slug=structure_slug,
                    ticket_id=ticket_id)

@login_required
def task_edit_url(request, structure_slug, ticket_id, task_id):
    """
    Makes URL redirect to edit ticket task according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect('uni_ticket:{}_edit_task'.format(user_type),
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                    task_id=task_id)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_edit(request, structure_slug, ticket_id, task_id,
              structure, can_manage, ticket, office_employee=None):
    """
    Edit task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)

    if ticket.is_closed:
        return custom_message(request, _("Il ticket {} è chiuso".format(ticket)),
                              structure_slug=structure.slug)

    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    usertype = get_user_type(request.user, structure)
    data = {'subject': task.subject,
            'description': task.description,
            'priority': task.priority,}
    form = TaskForm(initial=data)
    if request.method == 'POST':
        if task.is_closed:
            messages.add_message(request, messages.ERROR,
                                 _("Impossibile modificare un task chiuso"))
            return redirect('uni_ticket:manage_task_detail_url',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id,
                            task_id=task_id)

        form = TaskForm(data=request.POST,
                        files=request.FILES)
        if form.is_valid():
            msg = _("Modifica attività {}".format(task))
            task.subject = request.POST.get('subject')
            task.description = request.POST.get('description')
            if task.priority != request.POST.get('priority'):
                msg = msg + _(" e Priorità assegnata: {}"
                              "".format(dict(PRIORITY_LEVELS).get(request.POST.get('priority'))))
            task.priority = request.POST.get('priority')
            if request.FILES.get('attachment'):
                task.attachment = request.FILES.get('attachment')
            task.save(update_fields = ['subject',
                                       'description',
                                       'priority',
                                       'attachment'])

            task.update_log(user=request.user,
                                note=msg)
            ticket.update_log(user=request.user,
                                  note=msg)
            messages.add_message(request, messages.SUCCESS,
                                 _("Attività aggiornata con successo"))
            return redirect('uni_ticket:edit_task',
                            structure_slug=structure_slug,
                            ticket_id=ticket_id,
                            task_id=task_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    template = '{}/task_edit.html'.format(usertype)
    title = _('Modifica attività')
    sub_title = task
    allegati = {}
    if task.attachment:
        allegati[form.fields['attachment'].label.lower()] = os.path.basename(task.attachment.name)
        del form.fields['attachment']

    d = {'allegati': allegati,
         'form': form,
         'structure': structure,
         'sub_title': sub_title,
         'task': task,
         'title': title,}
    return render(request, template, d)

@login_required
@has_admin_privileges
@ticket_assigned_to_structure
def task_attachment_delete(request, structure_slug,
                           ticket_id, task_id,
                           structure, can_manage, ticket, office_employee=None):
    """
    Delete a task attachment (it must be called by a dialog to confirm action)

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_admin_privileges)
    :type can_manage: Dictionary (from @has_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: redirect
    """
    if can_manage['readonly']:
        messages.add_message(request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET)
        return redirect('uni_ticket:manage_ticket_url_detail',
                        structure_slug=structure_slug,
                        ticket_id=ticket_id)

    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    if task.created_by != request.user:
        return custom_message(request, _("Permessi di modifica del task mancanti"),
                              structure_slug=structure.slug)

    # Rimuove il riferimento all'allegato dalla base dati
    path_allegato = get_path_allegato_task(task)

    # Rimuove l'allegato dal disco
    delete_file(file_name=os.path.basename(task.attachment.name),
                path=path_allegato)

    task.attachment=None
    task.save(update_fields = ['attachment'])

    msg = _("Allegato task {} eliminato".format(task.code))
    task.update_log(user=request.user,
                          note=_("Allegato eliminato"))
    ticket.update_log(user=request.user,
                          note=msg)
    messages.add_message(request, messages.SUCCESS, msg)
    return redirect('uni_ticket:edit_task',
                    structure_slug=structure.slug,
                    ticket_id=ticket_id,
                    task_id=task_id)

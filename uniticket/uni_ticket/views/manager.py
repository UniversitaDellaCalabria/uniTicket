import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import gettext as _

from django_form_builder.utils import get_labeled_errors
from organizational_area.models import *

from uni_ticket.decorators import is_manager
from uni_ticket.forms import *
from uni_ticket.models import *
from uni_ticket.protocol_utils import ticket_protocol
from uni_ticket.utils import (
    base_context,
    custom_message,
    office_can_be_deleted,
    user_is_manager,
    uuid_code,
)


logger = logging.getLogger(__name__)


@login_required
@is_manager
def dashboard(request, structure_slug, structure):
    """
    Manager Dashboard

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Pannello di Controllo")
    sub_title = _(
        "Gestisci le richieste per la struttura {}").format(structure)
    template = "manager/dashboard.html"

    # ta = TicketAssignment
    # structure_tickets = ta.get_ticket_per_structure(structure=structure)
    # tickets = Ticket.objects.filter(code__in=structure_tickets)

    assignments = TicketAssignment.objects.filter(
        office__organizational_structure=structure,
        office__is_active=True,
        follow=True
    ).select_related('ticket')

    chiusi = assignments.filter(ticket__is_closed=True).values('ticket__code').annotate(total=Count('ticket__code')).count()
    opened = assignments.filter(ticket__assigned_date__isnull=False, ticket__is_closed=False).values('ticket__code').annotate(total=Count('ticket__code')).count()
    unassigned = assignments.filter(ticket__assigned_date__isnull=True, ticket__is_closed=False).values('ticket__code').annotate(total=Count('ticket__code')).count()
    my_opened = assignments.filter(ticket__assigned_date__isnull=False, ticket__is_closed=False, taken_by=request.user).values('ticket__code').annotate(total=Count('ticket__code')).count()
    om = OrganizationalStructureOffice
    offices = om.objects.filter(organizational_structure=structure)\
                        .values('is_active','is_default','name','description','slug')\
                        .prefetch_related('organizationalstructureofficeemployee_set')\
                        .prefetch_related('ticketassignment_set')\
                        .prefetch_related('ticketcategory_set')

    cm = TicketCategory
    categories = cm.objects.filter(organizational_structure=structure)\
                           .select_related('organizational_office')\
                           .values('description','name','slug')\
                           .prefetch_related('ticketcategorycondition_set')\
                           .prefetch_related('ticketcategorytask_set')
    # disabled_expired_items(categories)

    # messages = TicketReply.get_unread_messages_count(tickets=tickets)
    ticket_codes = assignments.values_list('ticket',flat=True).distinct()
    messages = TicketReply.get_unread_messages_count(tickets=ticket_codes)
    d = {
        "categories": categories,
        "offices": offices,
        "structure": structure,
        "sub_title": sub_title,
        "ticket_aperti": opened,
        "ticket_assegnati_a_me": my_opened,
        "ticket_chiusi": chiusi,
        "ticket_messages": messages,
        "ticket_non_gestiti": unassigned,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def offices(request, structure_slug, structure):
    """
    Retrieves structure offices list

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Gestione uffici")
    template = "manager/offices.html"
    os = OrganizationalStructureOffice
    offices = os.objects.filter(organizational_structure=structure)\
                        .prefetch_related('organizationalstructureofficeemployee_set')\
                        .prefetch_related('ticketassignment_set')\
                        .prefetch_related('ticketcategory_set')

    d = {
        "offices": offices,
        "structure": structure,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def office_add_new(request, structure_slug, structure):
    """
    Adds new office to structure

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuovo ufficio")
    sub_title = _("Crea un nuovo ufficio nella struttura {}").format(structure)
    form = OfficeForm()
    if request.method == "POST":
        form = OfficeForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            slug = slugify(name)
            os = OrganizationalStructureOffice
            slug_name_exist = os.objects.filter(
                Q(name=name) | Q(slug=slug), organizational_structure=structure
            )
            if slug_name_exist:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Esiste già un ufficio con"
                        " nome {} o slug {}".format(name, slug)
                    ),
                )
            else:
                new_office = form.save(commit=False)
                new_office.slug = slug
                new_office.organizational_structure = structure
                new_office.save()

                # log action
                logger.info(
                    "[{}] manager of structure {}"
                    " {} created new office {}".format(
                        timezone.localtime(), structure, request.user, new_office
                    )
                )

                messages.add_message(
                    request, messages.SUCCESS, _("Ufficio creato con successo")
                )
                return redirect(
                    "uni_ticket:manager_office_detail",
                    structure_slug=structure_slug,
                    office_slug=new_office.slug,
                )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "{}: {}".format(k, strip_tags(v))
                )
    template = "manager/office_add_new.html"
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def office_edit(request, structure_slug, office_slug, structure):
    """
    Edits office details

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )

    title = _("Modifica ufficio")
    sub_title = office.name

    form = OfficeForm(instance=office)
    if request.method == "POST":
        form = OfficeForm(instance=office, data=request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            slug = slugify(name)
            oso = OrganizationalStructureOffice
            slug_name_exist = oso.objects.filter(
                Q(name=name) | Q(slug=slug), organizational_structure=structure
            ).exclude(pk=office.pk)
            if slug_name_exist:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Esiste già un ufficio con questo" " nome o slug"),
                )
            else:
                edited_office = form.save(commit=False)
                edited_office.slug = slug
                edited_office.save()
                messages.add_message(
                    request, messages.SUCCESS, _(
                        "Ufficio modificato con successo")
                )

                # log action
                logger.info(
                    "[{}] manager of structure {}"
                    " {} edited office {}".format(
                        timezone.localtime(), structure, request.user, edited_office
                    )
                )

                return redirect(
                    "uni_ticket:manager_office_detail",
                    structure_slug=structure_slug,
                    office_slug=edited_office.slug,
                )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    template = "manager/office_edit.html"
    d = {
        "form": form,
        "office": office,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def office_detail(request, structure_slug, office_slug, structure):
    """
    Views office details

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    title = _("Gestione ufficio")
    template = "manager/office_detail.html"
    sub_title = office.name
    form = OfficeAddOperatorForm(structure=structure, office_slug=office_slug)
    category_form = OfficeAddCategoryForm(structure=structure, office=office)
    if request.method == "POST":
        form = OfficeAddOperatorForm(
            request.POST, structure=structure, office_slug=office_slug
        )

        if form.is_valid():
            employee = form.cleaned_data["operatore"]
            description = form.cleaned_data["description"]
            osoe = OrganizationalStructureOfficeEmployee
            new_officeemployee = osoe(
                employee=employee, office=office, description=description
            )
            new_officeemployee.save()
            messages.add_message(
                request, messages.SUCCESS, _(
                    "Operatore assegnato con successo")
            )

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} added employee {}"
                " to office {}".format(
                    timezone.localtime(), structure, request.user, employee, office
                )
            )

            return redirect(
                "uni_ticket:manager_office_detail",
                structure_slug=structure_slug,
                office_slug=office_slug,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    em = OrganizationalStructureOfficeEmployee
    employees = em.objects.filter(office=office, employee__is_active=True)
    d = {
        "category_form": category_form,
        "employees": employees,
        "form": form,
        "office": office,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def office_add_category(request, structure_slug, office_slug, structure):
    """
    Assings new category to office competences

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    if request.method == "POST":
        office = get_object_or_404(
            OrganizationalStructureOffice,
            organizational_structure=structure,
            slug=office_slug,
        )
        form = OfficeAddCategoryForm(
            request.POST, structure=structure, office=office)
        if form.is_valid():
            category = form.cleaned_data["category"]
            if category.organizational_office:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "La tipologia di richiesta <b>{}</b> risulta "
                        "già assegnato all'ufficio <b>{}</b>. "
                        "Rimuovere la competenza per "
                        "procedere"
                    ).format(category, category.organizational_office),
                )
                return redirect(
                    "uni_ticket:manager_office_detail",
                    structure_slug=structure_slug,
                    office_slug=office_slug,
                )
            category.organizational_office = office
            category.save(update_fields=["organizational_office"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Competenza ufficio impostata con successo"),
            )

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} added category {}"
                " to office {}".format(
                    timezone.localtime(), structure, request.user, category, office
                )
            )

        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
        return redirect(
            "uni_ticket:manager_office_detail",
            structure_slug=structure_slug,
            office_slug=office_slug,
        )
    return custom_message(
        request,
        _("Impossibile accedere a questo URL " "senza passare dal form collegato."),
        structure_slug=structure.slug,
    )


@login_required
@is_manager
def office_remove_category(
    request, structure_slug, office_slug, category_slug, structure
):
    """
    Remove category from office competences

    :type structure_slug: String
    :type office_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )

    if category.organizational_office != office:
        messages.add_message(
            request,
            messages.ERROR,
            _("La tipologia di richiesta non è di competenza di" " questo ufficio"),
        )
    else:
        category.organizational_office = None
        category.is_active = False
        category.save(update_fields=["organizational_office", "is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _(
                "La tipologia di richiesta <b>{}</b> non è più di competenza "
                " dell'ufficio <b>{}</b> ed è stato disattivato".format(
                    category, office
                )
            ),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} removed category {}"
            " from office {}".format(
                timezone.localtime(), structure, request.user, category, office
            )
        )

    return redirect(
        "uni_ticket:manager_office_detail",
        structure_slug=structure_slug,
        office_slug=office_slug,
    )


@login_required
@is_manager
def office_remove_operator(
    request, structure_slug, office_slug, employee_id, structure
):
    """
    Remove employee from office

    :type structure_slug: String
    :type office_slug: String
    :type employee_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param employee_id: employee_id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    user_model = get_user_model()
    employee = user_model.objects.get(pk=employee_id)
    usertype = get_user_type(employee, structure)
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )

    # Try to delete manager user from help-desk office (default)
    if usertype == "manager" and office.is_default:
        return custom_message(
            request,
            _(
                "Eliminando l'afferenza dell'utente"
                " a questo ufficio, egli perderà i"
                " privilegi di Amministratore."
                " Questa operazione, pertanto,"
                " non può essere eseguita in autonomia."
                " Contattare l'assistenza tecnica."
            ),
            structure_slug=structure.slug,
        )
    m = OrganizationalStructureOfficeEmployee
    office_employee = m.objects.get(office=office, employee=employee)
    if not office_employee:
        messages.add_message(
            request, messages.ERROR, _(
                "L'operatore non è assegnato a questo ufficio")
        )
    else:
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} removed employee {}"
            " from office {}".format(
                timezone.localtime(), structure, request.user, employee, office
            )
        )
        office_employee.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Operatore {} rimosso correttamente").format(employee),
        )
    return redirect(
        "uni_ticket:manager_office_detail",
        structure_slug=structure_slug,
        office_slug=office_slug,
    )


@login_required
@is_manager
def office_disable(request, structure_slug, office_slug, structure):
    """
    Disables an office

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    one_tickets_for_this_office = False
    office_tickets = TicketAssignment.objects.filter(
        office=office,
        # ticket__is_closed=False,
        follow=True,
    )
    one_tickets_for_this_office = False
    for ot in office_tickets:
        other_offices_for_ticket = TicketAssignment.objects.filter(
            office__is_active=True, ticket=ot.ticket, follow=True, readonly=False
        ).exclude(office=office)
        if not other_offices_for_ticket:
            one_tickets_for_this_office = True
            break

    if office.is_default:
        messages.add_message(
            request, messages.ERROR, _(
                "Impossibile disattivare questo ufficio")
        )
    elif one_tickets_for_this_office:
        messages.add_message(
            request,
            messages.ERROR,
            _(
                "Impossibile disattivare questo ufficio."
                " Alcuni ticket potrebbero rimanere privi di gestione"
            ),
        )
    elif office.is_active:
        assigned_categories = TicketCategory.objects.filter(
            organizational_office=office
        )
        for cat in assigned_categories:
            cat.is_active = False
            cat.save(update_fields=["is_active"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Categoria {} disattivata correttamente").format(cat),
            )
        office.is_active = False
        office.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Ufficio {} disattivato con successo").format(office),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled office {}".format(
                timezone.localtime(), structure, request.user, office
            )
        )

    else:
        messages.add_message(
            request, messages.ERROR, _(
                "Ufficio {} già disattivato").format(office)
        )
    return redirect(
        "uni_ticket:manager_office_detail",
        structure_slug=structure_slug,
        office_slug=office_slug,
    )


@login_required
@is_manager
def office_enable(request, structure_slug, office_slug, structure):
    """
    Enables an office

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    if office.is_active:
        messages.add_message(
            request, messages.ERROR, _(
                "Ufficio {} già attivato").format(office)
        )
    else:
        office.is_active = True
        office.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Ufficio {} attivato con successo").format(office),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled office {}".format(
                timezone.localtime(), structure, request.user, office
            )
        )

    return redirect(
        "uni_ticket:manager_office_detail",
        structure_slug=structure_slug,
        office_slug=office_slug,
    )


@login_required
@is_manager
def office_delete(request, structure_slug, office_slug, structure):
    """
    Deletes an office

    :type structure_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    if office_can_be_deleted(office):
        assigned_categories = TicketCategory.objects.filter(
            organizational_office=office
        )
        for cat in assigned_categories:
            cat.is_active = False
            cat.save(update_fields=["is_active"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Categoria {} disattivata correttamente").format(cat),
            )
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Ufficio {} eliminato correttamente").format(office),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} deleted office {}".format(
                timezone.localtime(), structure, request.user, office
            )
        )

        office.delete()
        return redirect("uni_ticket:manager_dashboard", structure_slug=structure_slug)
    messages.add_message(
        request,
        messages.ERROR,
        _(
            "Impossibile eliminare l'ufficio {}."
            " Ci sono ticket assegnati"
            " o è l'ufficio predefinito della struttura."
        ).format(office),
    )
    return redirect(
        "uni_ticket:manager_office_detail",
        structure_slug=structure_slug,
        office_slug=office_slug,
    )


@login_required
@is_manager
def category_detail(request, structure_slug, category_slug, structure):
    """
    Shows category details

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    # category.disable_if_expired()

    title = _("Gestione tipologia di richiesta")
    template = "manager/category_detail.html"
    sub_title = category
    form = CategoryAddOfficeForm(structure=structure)
    if request.method == "POST":
        if category.organizational_office:
            messages.add_message(
                request, messages.ERROR, _("Competenza ufficio già presente")
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
            )
        form = CategoryAddOfficeForm(request.POST, structure=structure)
        if form.is_valid():
            office = form.cleaned_data["office"]
            category.organizational_office = office
            category.save(update_fields=["organizational_office"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Competenza ufficio impostata con successo"),
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    slug_url = request.build_absolute_uri(
        reverse(
            "uni_ticket:add_new_ticket",
            kwargs={"structure_slug": structure.slug,
                    "category_slug": category.slug},
        )
    )
    pk_url = request.build_absolute_uri(
        reverse(
            "uni_ticket:add_new_ticket",
            kwargs={"structure_slug": structure.pk,
                    "category_slug": category.pk},
        )
    )
    category_urls = (slug_url, pk_url)
    d = {
        "category": category,
        "category_urls": category_urls,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_remove_office(
    request, structure_slug, category_slug, office_slug, structure
):
    """
    Remove office competence from category

    :type structure_slug: String
    :type category_slug: String
    :type office_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param office_slug: office slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    office = get_object_or_404(
        OrganizationalStructureOffice,
        organizational_structure=structure,
        slug=office_slug,
    )
    if category.organizational_office != office:
        messages.add_message(
            request,
            messages.ERROR,
            _("La tipologia di richiesta non è di competenza di" " questo ufficio"),
        )
    else:
        category.organizational_office = None
        category.is_active = False
        category.save(update_fields=["is_active", "organizational_office"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Competenza ufficio {} rimossa correttamente").format(office),
        )
        messages.add_message(
            request,
            messages.ERROR,
            _(
                "Tipo di richieste {} disattivato poichè" " priva di ufficio competente"
            ).format(category),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} removed office {}"
            " from category {}"
            " (now disabled)".format(
                timezone.localtime(), structure, request.user, office, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_add_new(request, structure_slug, structure):
    """
    Adds new category

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuova tipologia di richiesta")
    sub_title = _("Crea una nuova tipologia di richieste nella struttura {}").format(
        structure
    )
    form = CategoryForm()
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            slug = slugify(name)
            m = TicketCategory
            slug_name_exist = m.objects.filter(
                Q(name=name) | Q(slug=slug), organizational_structure=structure
            )
            if slug_name_exist:
                # log action
                logger.error(
                    "[{}] manager of structure {}"
                    " {} tried to add a new category"
                    " with existent name {} or slug {}".format(
                        timezone.localtime(), structure, request.user, name, slug
                    )
                )
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Esiste già una tipologia di richiesta con" " nome {} o slug {}"
                    ).format(name, slug),
                )
            else:
                new_category = form.save(commit=False)

                # check if protocol can be activated
                protocol_required = form.cleaned_data["protocol_required"]
                # if protocol_required and not
                # OrganizationalStructureWSProtocollo.get_active_protocol_configuration(organizational_structure=structure):
                if protocol_required:
                    protocol_required = False
                    messages.add_message(
                        request,
                        messages.INFO,
                        _(
                            "Prima di attivare il protocollo "
                            "obbligatorio è necessario "
                            "configurare i parametri"
                        ),
                    )

                new_category.protocol_required = protocol_required
                new_category.slug = slug
                new_category.organizational_structure = structure
                new_category.save()
                messages.add_message(
                    request, messages.SUCCESS, _(
                        "Categoria creata con successo")
                )

                # log action
                logger.info(
                    "[{}] manager of structure {}"
                    " {} added a new category"
                    " with name {} and slug {}".format(
                        timezone.localtime(), structure, request.user, name, slug
                    )
                )

                return redirect(
                    "uni_ticket:manager_category_detail",
                    structure_slug=structure_slug,
                    category_slug=new_category.slug,
                )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    template = "manager/category_add_new.html"
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_edit(request, structure_slug, category_slug, structure):
    """
    Edits category details

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    form = CategoryForm(instance=category)
    if request.method == "POST":
        form = CategoryForm(instance=category, data=request.POST)
        if form.is_valid():

            name = form.cleaned_data["name"]

            # check if protocol can be activated
            protocol_required = form.cleaned_data["protocol_required"]
            if protocol_required:
                # denied to anonymous users
                if form.cleaned_data["allow_anonymous"]:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _(
                            "Il protocollo non può essere attivato se "
                            "la tipologia di richiesta è "
                            "accessibile a utenti anonimi"
                        ),
                    )
                    return redirect(
                        "uni_ticket:manager_category_edit",
                        structure_slug=structure_slug,
                        category_slug=category.slug,
                    )
                # no active category protocol configuration
                if not category.get_active_protocol_configuration():
                    protocol_required = False
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _(
                            "Il protocollo non può essere attivato. "
                            "Controlla che ci sia una configurazione valida "
                            "sia per la tipologia e che per la struttura"
                        ),
                    )

            slug = slugify(name)
            slug_name_exist = TicketCategory.objects.filter(
                Q(name=name) | Q(slug=slug), organizational_structure=structure
            ).exclude(pk=category.pk)
            if slug_name_exist:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Esiste già una tipologia di richiesta con questo"
                        " nome o slug"
                    ),
                )
            else:
                edited_category = form.save(commit=False)
                edited_category.slug = slug
                edited_category.protocol_required = protocol_required
                edited_category.save(
                    update_fields=[
                        "name",
                        "slug",
                        "description",
                        "show_heading_text",
                        "is_notification",
                        "confirm_message_text",
                        "footer_text",
                        "not_available_message",
                        "date_start",
                        "date_end",
                        "allow_anonymous",
                        "allow_guest",
                        "allow_user",
                        "allow_employee",
                        "receive_email",
                        "protocol_required",
                        "user_multiple_open_tickets",
                        "modified",
                        "is_hidden"
                    ]
                )
                form.save_m2m()
                # log action
                logger.info(
                    "[{}] manager of structure {}"
                    " {} edited the category {}".format(
                        timezone.localtime(), structure, request.user, category
                    )
                )

                messages.add_message(
                    request, messages.SUCCESS, _(
                        "Categoria modificata con successo")
                )
                return redirect(
                    "uni_ticket:manager_category_detail",
                    structure_slug=structure_slug,
                    category_slug=edited_category.slug,
                )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    template = "manager/category_edit.html"
    title = _("Modifica tipologia di richiesta")
    sub_title = category
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_disable(request, structure_slug, category_slug, structure):
    """
    Disables a category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    if category.is_active:
        category.is_active = False
        category.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Tipo di richieste {} disattivato con successo" "").format(category),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled the category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("Tipo di richieste {} già disattivato" "").format(category),
        )
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_enable(request, structure_slug, category_slug, structure):
    """
    Enables a category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    problem = category.something_stops_activation()
    if category.is_active:
        messages.add_message(
            request,
            messages.ERROR,
            _("Tipo di richieste {} già attivato" "").format(category),
        )
    elif problem:
        messages.add_message(request, messages.ERROR, problem)
    else:
        category.is_active = True
        category.save(update_fields=["is_active"])
        if category.is_started():
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Tipo di richieste {} attivato con successo" "").format(category),
            )
        else:
            start = timezone.localtime(category.date_start)
            start_string = start.strftime(settings.DEFAULT_DATETIME_FORMAT)
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    "Tipo di richieste {} attivato con successo. " "Data di inizio {}"
                ).format(category, start_string),
            )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled the category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_delete(request, structure_slug, category_slug, structure):
    """
    Deletes a category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    if category.can_be_deleted():

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} deleted the category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            _("Categoria {} eliminata correttamente" "").format(category),
        )

        category.delete()
        return redirect("uni_ticket:manager_dashboard", structure_slug=structure_slug)
    messages.add_message(
        request,
        messages.ERROR,
        _(
            "Impossibile eliminare la tipologia di richiesta {}."
            " Ci sono ticket assegnati."
        ).format(category),
    )
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_input_module_new(request, structure_slug, category_slug, structure):
    """
    Creates new input module for category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    title = _("Nuovo modulo di inserimento")
    sub_title = _("Crea un nuovo modulo per la tipologia di richiesta {}").format(
        category.name
    )
    form = CategoryInputModuleForm()
    if request.method == "POST":
        form = CategoryInputModuleForm(request.POST)
        if form.is_valid():
            new_module = form.save(commit=False)
            new_module.ticket_category = category
            new_module.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the module {}"
                " in the category {}".format(
                    timezone.localtime(), structure, request.user, new_module, category
                )
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Modulo di inserimento <b>{}</b>" " creato con successo").format(
                    new_module.name
                ),
            )
            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=new_module.pk,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/category_input_module_add_new.html"
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_module_edit(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Edits input module details

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    form = CategoryInputModuleForm(instance=module)
    if request.method == "POST":
        form = CategoryInputModuleForm(data=request.POST, instance=module)
        if form.is_valid():
            module_edited = form.save(commit=False)
            module_edited.save(update_fields=["name"])

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited the module {}"
                " of the category {}".format(
                    timezone.localtime(), structure, request.user, module, category
                )
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Modulo di inserimento modificato con successo"),
            )
            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=module_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    title = _("Rinomina modulo [{}]").format(module)
    sub_title = "{} - {}".format(category, structure)
    template = "manager/category_input_module_edit.html"
    d = {
        "category": category,
        "form": form,
        "module": module,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_module_enable(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Enables input module

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    if module.is_active:
        messages.add_message(
            request, messages.ERROR, _("Modulo {} già attivato").format(module)
        )
    else:
        module.is_active = True
        module.save(update_fields=["is_active"])
        module.disable_other_modules()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Modulo {} attivato con successo").format(module),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled the module {}"
            " of the category {}".format(
                timezone.localtime(), structure, request.user, module, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_input_module_disable(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Disables input module

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    if not module.is_active:
        messages.add_message(
            request, messages.ERROR, _(
                "Modulo {} già disattivato").format(module)
        )
    else:
        category.is_active = False
        category.save(update_fields=["is_active"])
        module.is_active = False
        module.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Modulo {} disattivato con successo").format(module),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled the module {}"
            " and the category {}".format(
                timezone.localtime(), structure, request.user, module, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_input_module_delete(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Deletes input module

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    if not module.can_be_deleted():

        # log action
        logger.error(
            "[{}] manager of structure {}"
            " {} tried to delete"
            " the module {} of category {}".format(
                timezone.localtime(), structure, request.user, module, category
            )
        )

        messages.add_message(
            request,
            messages.ERROR,
            _(
                "Impossibile eliminare il modulo {}."
                " Ci sono delle richieste collegate"
            ).format(module),
        )
    else:
        if module.is_active:
            category.is_active = False
            category.save(update_fields=["is_active"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "Modulo <b>{}</b> eliminato con successo"
                    " e tipologia di richiesta <b>{}</b> disattivata"
                    " (nessun modulo attivo)"
                ).format(module, category),
            )
        else:
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Modulo {} eliminato con successo").format(module),
            )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} deleted"
            " the module {} of category {}".format(
                timezone.localtime(), structure, request.user, module, category
            )
        )

        module.delete()
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_input_module_details(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Shows category input module details

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(TicketCategoryModule, pk=module_id)
    form = CategoryInputListForm()
    if request.method == "POST":
        if not module.can_be_deleted():
            messages.add_message(
                request, messages.ERROR, _("Impossibile modificare il modulo")
            )
            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=module.pk,
            )
        form = CategoryInputListForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            if TicketCategoryInputList.field_exist(module, name):
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Esiste già un campo con questo" " nome: <b>{}</b>".format(name)),
                )
            else:
                # is_required_value = form.cleaned_data['is_required']
                # is_required = False
                # if is_required_value == 'on': is_required=True
                input_list = form.save(commit=False)
                input_list.category_module = module
                input_list.pre_text = strip_tags(form.cleaned_data["pre_text"])
                input_list.save()
                messages.add_message(
                    request, messages.SUCCESS, _(
                        "Campo di input creato con successo")
                )

                # log action
                logger.info(
                    "[{}] manager of structure {}"
                    " {} inserted the field {}"
                    " in the module {} of category {}".format(
                        timezone.localtime(),
                        structure,
                        request.user,
                        name,
                        module,
                        category,
                    )
                )

            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=module.pk,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    title = _("Gestione modulo [{}]").format(module)
    template = "manager/category_input_module_detail.html"
    sub_title = "{} - {}".format(category, structure)
    d = {
        "category": category,
        "form": form,
        "module": module,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_field_delete(
    request, structure_slug, category_slug, module_id, field_id, structure
):
    """
    Deletes a field from a category input module

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type field_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param field_id: module field id
    :param structure: structure object (from @is_manager)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    if not module.can_be_deleted():

        # log action
        logger.error(
            "[{}] manager of structure {}"
            " {} tried to delete a field"
            " from module {} of category {}".format(
                timezone.localtime(), structure, request.user, module, category
            )
        )

        messages.add_message(
            request,
            messages.ERROR,
            _(
                "Impossibile eliminare il modulo {}."
                " Ci sono delle richieste collegate"
            ).format(module),
        )
    else:
        field = get_object_or_404(
            TicketCategoryInputList, pk=field_id, category_module=module
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} deleted the field {}"
            " from module {} of category {}".format(
                timezone.localtime(), structure, request.user, field, module, category
            )
        )
        field.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Campo {} eliminato con successo").format(field.name),
        )
    return redirect(
        "uni_ticket:manager_category_input_module",
        structure_slug=structure_slug,
        category_slug=category_slug,
        module_id=module_id,
    )


@login_required
@is_manager
def category_input_module_preview(
    request, structure_slug, category_slug, module_id, structure
):
    """
    Shows input module form preview

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    form = module.get_form(show_conditions=True)
    title = _("Anteprima modulo di inserimento")
    sub_title = "{} in {}".format(module, category)
    template = "manager/category_input_module_preview.html"
    clausole_categoria = category.get_conditions()
    d = {
        "categoria": category,
        "category_conditions": clausole_categoria,
        "form": form,
        "struttura": structure,
        "sub_title": sub_title,
        "title": title,
    }
    if request.POST:
        form = module.get_form(
            data=request.POST, files=request.FILES, show_conditions=True
        )
        d["form"] = form
        if form.is_valid():
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Dati inseriti nel modulo formalmente corretti"),
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_field_edit(
    request, structure_slug, category_slug, module_id, field_id, structure
):
    """
    Edits field details from a category input module

    :type structure_slug: String
    :type category_slug: String
    :type module_id: Integer
    :type field_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param module_id: input module id
    :param field_id: module field id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    field = get_object_or_404(
        TicketCategoryInputList, pk=field_id, category_module=module
    )
    form = CategoryInputListForm(instance=field)
    if request.method == "POST":
        if not module.can_be_deleted():

            # log action
            logger.error(
                "[{}] manager of structure {}"
                " {} tried to edit a field"
                " from module {} of category {}".format(
                    timezone.localtime(), structure, request.user, module, category
                )
            )

            messages.add_message(
                request, messages.ERROR, _("Impossibile modificare il campo")
            )
            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=module_id,
            )
        form = CategoryInputListForm(data=request.POST, instance=field)
        if form.is_valid():
            field = form.save(commit=False)
            field.pre_text = strip_tags(form.cleaned_data["pre_text"])
            field.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited the field {}"
                " from module {} of category {}".format(
                    timezone.localtime(),
                    structure,
                    request.user,
                    field,
                    module,
                    category,
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Campo di input modificato con successo")
            )
            return redirect(
                "uni_ticket:manager_category_input_module",
                structure_slug=structure_slug,
                category_slug=category_slug,
                module_id=module.pk,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    title = _("Modifica campo di input [{}]").format(field.name)
    sub_title = "{} - {} - {}".format(module,
                                      module.ticket_category, structure)
    template = "manager/category_input_field_edit.html"
    d = {
        "category": category,
        "field": field,
        "form": form,
        "module": module,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_condition_new(request, structure_slug, category_slug, structure):
    """
    Creates a new condition for category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuova clausola per inserimento ticket")
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    form = CategoryConditionForm()
    if request.method == "POST":
        form = CategoryConditionForm(request.POST, request.FILES)
        if form.is_valid():
            condition = form.save(commit=False)
            condition.text = strip_tags(form.cleaned_data["text"])
            condition.category = category
            condition.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the new condition {}"
                " for category {}".format(
                    timezone.localtime(), structure, request.user, condition, category
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _("Clausola creata con successo")
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/category_condition_add_new.html"
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": category,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_condition_edit(
    request, structure_slug, category_slug, condition_id, structure
):
    """
    Edits condition details

    :type structure_slug: String
    :type category_slug: String
    :type condition_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param condition_id: condition id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    condition = get_object_or_404(
        TicketCategoryCondition, pk=condition_id, category=category
    )
    form = CategoryConditionForm(instance=condition)
    if request.method == "POST":
        form = CategoryConditionForm(
            instance=condition, data=request.POST, files=request.FILES
        )
        if form.is_valid():
            edited_condition = form.save(commit=False)
            edited_condition.text = strip_tags(form.cleaned_data["text"])
            edited_condition.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited a condition"
                " for category {}".format(
                    timezone.localtime(), structure, request.user, category
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Clausola modificata con successo")
            )
            return redirect(
                "uni_ticket:manager_category_condition_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
                condition_id=condition_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    template = "manager/category_condition_edit.html"
    title = _("Modifica clausola")
    sub_title = condition
    d = {
        "condition": condition,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_condition_delete(
    request, structure_slug, category_slug, condition_id, structure
):
    """
    Deletes condition from a category

    :type structure_slug: String
    :type category_slug: String
    :type condition_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param condition_id: condition id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    condition = get_object_or_404(
        TicketCategoryCondition, pk=condition_id, category=category
    )
    messages.add_message(
        request,
        messages.SUCCESS,
        _("Clausola {} eliminata correttamente").format(condition),
    )

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} deleted a condition"
        " for category {}".format(
            timezone.localtime(), structure, request.user, category
        )
    )

    condition.delete()
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_condition_disable(
    request, structure_slug, category_slug, condition_id, structure
):
    """
    Disables a condition from a category

    :type structure_slug: String
    :type category_slug: String
    :type condition_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param condition_id: condition id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    condition = get_object_or_404(
        TicketCategoryCondition, pk=condition_id, category=category
    )
    if condition.is_active:
        condition.is_active = False
        condition.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Clausola {} disattivata con successo").format(condition),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled a condition"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )
    else:
        messages.add_message(
            request, messages.ERROR, _(
                "Clausola {} già disattivata").format(condition)
        )
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_condition_enable(
    request, structure_slug, category_slug, condition_id, structure
):
    """
    Enables a condition from a category

    :type structure_slug: String
    :type category_slug: String
    :type condition_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param condition_id: condition id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    condition = get_object_or_404(
        TicketCategoryCondition, pk=condition_id, category=category
    )
    if condition.is_active:
        messages.add_message(
            request, messages.ERROR, _(
                "Clausola {} già attivata").format(condition)
        )
    else:
        condition.is_active = True
        condition.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Clausola {} attivata con successo").format(condition),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled a condition"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_condition_detail(
    request, structure_slug, category_slug, condition_id, structure
):
    """
    Shows condition details

    :type structure_slug: String
    :type category_slug: String
    :type condition_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param condition_id: condition id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Gestione dettaglio clausola")
    template = "manager/category_condition_detail.html"
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    condition = get_object_or_404(
        TicketCategoryCondition, pk=condition_id, category=category
    )
    d = {
        "category": category,
        "condition": condition,
        "structure": structure,
        "sub_title": condition,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def categories(request, structure_slug, structure):
    """
    Retrieves structure categories list

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Gestione tipologie di richieste")
    template = "manager/categories.html"
    # sub_title = _("gestione ufficio livello manager")
    categories = TicketCategory.objects\
                               .filter(organizational_structure=structure)\
                               .select_related('organizational_office')\
                               .prefetch_related('ticketcategorycondition_set')\
                               .prefetch_related('ticketcategorytask_set')
    # disabled_expired_items(categories)

    d = {
        "categories": categories,
        "structure": structure,
        # 'sub_title': sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_module_clone_preload(
    request,
    structure_slug,
    category_slug,
    module_id,
    selected_structure_slug=None,
    selected_category_slug=None,
    structure=None,
):
    """ """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    structures = OrganizationalStructure.objects.filter(is_active=True)
    my_structures = []
    categories = []
    for struct in structures:
        if user_is_manager(request.user, struct):
            my_structures.append(struct)
    title = _(
        "Clona modulo [{}] ({} - {})").format(module, category, structure)
    template = "manager/category_input_module_clone.html"
    sub_title = _("Seleziona la struttura")
    if selected_structure_slug:
        selected_structure = get_object_or_404(
            OrganizationalStructure, slug=selected_structure_slug, is_active=True
        )

        # another check if user is a manager of selected structure
        if not user_is_manager(request.user, selected_structure):
            return custom_message(
                request,
                _("Non sei un manager della struttura selezionata"),
                structure_slug=structure.slug,
            )

        categories = TicketCategory.objects.filter(
            organizational_structure=selected_structure
        )
        sub_title = _("Seleziona la Categoria")
    if selected_category_slug:
        get_object_or_404(
            TicketCategory,
            organizational_structure=selected_structure,
            slug=selected_category_slug,
        )

    d = {
        "categories": categories,
        "category": category,
        "module": module,
        "my_structures": my_structures,
        "selected_category_slug": selected_category_slug,
        "selected_structure_slug": selected_structure_slug,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_input_module_clone(
    request,
    structure_slug,
    category_slug,
    module_id,
    selected_structure_slug,
    selected_category_slug,
    structure,
):
    """ """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    module = get_object_or_404(
        TicketCategoryModule, pk=module_id, ticket_category=category
    )
    selected_structure = get_object_or_404(
        OrganizationalStructure, slug=selected_structure_slug, is_active=True
    )

    # check if user is manager of selected structure
    if not user_is_manager(request.user, selected_structure):
        return custom_message(
            request,
            _("Non sei un manager della struttura selezionata"),
            structure_slug=structure.slug,
        )

    selected_category = get_object_or_404(
        TicketCategory,
        organizational_structure=selected_structure,
        slug=selected_category_slug,
    )
    # create new module in selected category with main module name
    new_module = TicketCategoryModule.objects.create(
        name=module.name, ticket_category=selected_category
    )

    # get all input fields of main module and clone these in new module
    main_module_inputlist = TicketCategoryInputList.objects.filter(
        category_module=module
    )
    for module_input in main_module_inputlist:
        input_dict = module_input.__dict__
        del input_dict["_state"]
        del input_dict["id"]
        input_dict["category_module_id"] = new_module.pk
        TicketCategoryInputList.objects.create(**input_dict)

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} cloned the module {} of category {}"
        " in the category {} ({})".format(
            timezone.localtime(),
            structure,
            request.user,
            module,
            category,
            selected_category,
            selected_structure,
        )
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        _(
            "Modulo di input <b>{}</b> clonato con successo"
            " nella tipologia di richieste <b>{}</b>"
            ""
        ).format(module.name, selected_category),
    )
    return redirect(
        "uni_ticket:manager_category_input_module",
        structure_slug=selected_structure.slug,
        category_slug=selected_category.slug,
        module_id=new_module.pk,
    )


@login_required
@is_manager
def category_task_new(request, structure_slug, category_slug, structure):
    """
    Creates a new task for category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuova attività per inserimento ticket")
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    form = CategoryTaskForm()
    if request.method == "POST":
        form = CategoryTaskForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.category = category
            new_task.created_by = request.user
            new_task.code = uuid_code()
            new_task.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the new task {}"
                " for category {}".format(
                    timezone.localtime(), structure, request.user, new_task, category
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _("Attività creata con successo")
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/category_task_add_new.html"
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": category,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_task_detail(request, structure_slug, category_slug, task_id, structure):
    """
    Shows task details

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: task code
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Gestione dettaglio attività")
    template = "manager/category_task_detail.html"
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)
    d = {
        "category": category,
        "structure": structure,
        "sub_title": task,
        "task": task,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_task_download_attachment(
    request, structure_slug, category_slug, task_id, structure
):
    """
    Downloads category task attachment

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: task code
    :param structure: structure object (from @is_manager)

    :return: file
    """
    # get task
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)
    # if task has attachment
    if task.attachment:
        # get ticket folder path
        path_allegato = get_path(task.get_folder())
        # get file
        result = download_file(
            path_allegato, os.path.basename(task.attachment.name))
        return result
    raise Http404


@login_required
@is_manager
def category_task_edit(request, structure_slug, category_slug, task_id, structure):
    """
    Edits condition details

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: task code
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)

    form = CategoryTaskForm(instance=task)

    template = "manager/category_task_edit.html"
    title = _("Modifica attività")
    sub_title = task

    allegati = {}
    if task.attachment:
        allegati[form.fields["attachment"].label.lower()] = os.path.basename(
            task.attachment.name
        )
        del form.fields["attachment"]

    if request.method == "POST":
        form = CategoryTaskForm(
            instance=task, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited a task"
                " for category {}".format(
                    timezone.localtime(), structure, request.user, category
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Attività modificata con successo")
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    d = {
        "allegati": allegati,
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "task": task,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_task_attachment_delete(
    request, structure_slug, category_slug, task_id, structure
):
    """
     Delete a task attachment (it must be called by a dialog to confirm action)

    :type structure_slug: String
     :type category_slug: String
     :type task_id: String
     :type structure: OrganizationalStructure (from @is_manager)

     :param structure_slug: structure slug
     :param category_slug: category slug
     :param task_id: task code
     :param structure: structure object (from @is_manager)

     :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)

    # Rimuove l'allegato dal disco
    delete_directory(task.get_folder())

    task.attachment = None
    task.save(update_fields=["attachment"])

    msg = _("Allegato attività {} eliminato").format(task)

    # log action
    logger.info(
        "[{}] {} deleted attachment"
        " from task {} of category {}".format(
            timezone.localtime(), request.user, task, category
        )
    )

    messages.add_message(request, messages.SUCCESS, msg)
    return redirect(
        "uni_ticket:manager_category_task_edit",
        structure_slug=structure.slug,
        category_slug=category.slug,
        task_id=task.code,
    )


@login_required
@is_manager
def category_task_enable(request, structure_slug, category_slug, task_id, structure):
    """
    Enables a task from a category

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: task code
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)
    if task.is_active:
        messages.add_message(
            request, messages.ERROR, _("Attività {} già attivata").format(task)
        )
    else:
        task.is_active = True
        task.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Attività {} attivata con successo").format(task),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled a task"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_task_disable(request, structure_slug, category_slug, task_id, structure):
    """
    Disables a task from a category

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: tak code
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)
    if task.is_active:
        task.is_active = False
        task.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Attività {} disattivata con successo").format(task),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled a task"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )
    else:
        messages.add_message(
            request, messages.ERROR, _(
                "Attività {} già disattivata").format(task)
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_task_delete(request, structure_slug, category_slug, task_id, structure):
    """
    Deletes task from a category

    :type structure_slug: String
    :type category_slug: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param task_id: task code
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    task = get_object_or_404(
        TicketCategoryTask, code=task_id, category=category)
    messages.add_message(
        request, messages.SUCCESS, _(
            "Attività {} eliminata correttamente").format(task)
    )

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} deleted a task"
        " for category {}".format(
            timezone.localtime(), structure, request.user, category
        )
    )

    delete_directory(task.get_folder())
    task.delete()

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def manager_settings(request, structure_slug, structure):
    """
    Gets manager settings (personal and structure)

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)

    :return: response
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/user_settings.html".format(user_type)
    title = _("Configurazione impostazioni")
    sub_title = _("dati personali e della struttura")

    manager_users = structure.get_structure_managers()

    form = OrganizationalStructureAddManagerForm(
        structure=structure, manager_users=manager_users
    )
    protocol_configurations = OrganizationalStructureWSProtocollo.objects.filter(
        organizational_structure=structure
    )

    alerts = OrganizationalStructureAlert.objects.filter(
        organizational_structure=structure
    )
    # disabled_expired_items(alerts)

    if request.method == "POST":
        form = OrganizationalStructureAddManagerForm(
            request.POST, structure=structure, manager_users=manager_users
        )
        if form.is_valid():
            manager = form.cleaned_data["manager"]
            osoe = OrganizationalStructureOfficeEmployee
            default_office = OrganizationalStructureOffice.objects.get(
                organizational_structure=structure, is_default=True
            )
            # add user to default office
            operator_exists = osoe.objects.filter(
                employee=manager, office=default_office
            ).first()
            if not operator_exists:
                new_officeemployee = osoe(
                    employee=manager, office=default_office)
                new_officeemployee.save()

            # add user to structure managers
            new_manager = UserManageOrganizationalStructure(
                user=manager, organizational_structure=structure
            )
            new_manager.save()

            messages.add_message(
                request, messages.SUCCESS, _("Manager creato con successo")
            )

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} added new manager {}".format(
                    timezone.localtime(), structure, request.user, manager
                )
            )

            return redirect(
                "uni_ticket:manager_user_settings", structure_slug=structure_slug
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    d = {
        "alerts": alerts,
        "form": form,
        "manager_users": manager_users,
        "protocol_configurations": protocol_configurations,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    response = render(request, template, base_context(d))
    return response


@login_required
@is_manager
def structure_protocol_configuration_detail(
    request, structure_slug, configuration_id, structure
):
    """
    Structure protocol configuration details

    :type structure_slug: String
    :type configuration_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param configuration_id: protocol configuration pk
    :param structure: structure object (from @is_manager/@is_operator)

    :return: response
    """
    configuration = get_object_or_404(
        OrganizationalStructureWSProtocollo,
        organizational_structure=structure,
        pk=configuration_id,
    )

    template = "manager/structure_protocol_configuration.html"
    title = _("Configurazione protocollo informatico")

    form = OrganizationalStructureWSProtocolloModelForm(instance=configuration)

    # POST ACTION DISABLED
    # FORM FIELDS DISABLED
    # if request.method == 'POST':
    # form = OrganizationalStructureWSProtocolloModelForm(instance=configuration,
    # data=request.POST)
    # if form.is_valid():
    # configuration = form.save(commit=False)
    # if not configuration.protocollo_email:
    # configuration.protocollo_email = settings.PROTOCOL_EMAIL_DEFAULT
    # configuration.save()

    # messages.add_message(request, messages.SUCCESS,
    # _("Configurazione protocollo informatico aggiornata"))
    # return redirect('uni_ticket:manager_structure_protocol_configuration_detail',
    # structure_slug=structure_slug,
    # configuration_id=configuration.pk)
    # else:
    # for k,v in get_labeled_errors(form).items():
    # messages.add_message(request, messages.ERROR,
    # "<b>{}</b>: {}".format(k, strip_tags(v)))
    d = {
        "configuration": configuration,
        "form": form,
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    response = render(request, template, base_context(d))
    return response


# FRONTEND ACTION DISABLED
# @login_required
# @is_manager
# def structure_protocol_configuration_new(request, structure_slug,
# structure):
# """
# New structure protocol configuration

# :type structure_slug: String
# :type structure: OrganizationalStructure (from @is_manager)

# :param structure_slug: structure slug
# :param structure: structure object (from @is_manager/@is_operator)

# :return: response
# """
# template = "manager/structure_protocol_configuration_new.html"
# title = _("Nuova configurazione protocollo informatico")

# initial_data = {'protocollo_template': settings.PROTOCOL_XML, }
# form = OrganizationalStructureWSProtocolloModelForm(initial_data)

# if request.method == 'POST':
# form = OrganizationalStructureWSProtocolloModelForm(data=request.POST)
# if form.is_valid():
# configuration = form.save(commit=False)
# if not configuration.protocollo_email:
# configuration.protocollo_email = settings.PROTOCOL_EMAIL_DEFAULT
# configuration.organizational_structure=structure
# configuration.save()

# messages.add_message(request, messages.SUCCESS,
# _("Configurazione protocollo informatico creata"))
# return redirect('uni_ticket:manager_user_settings',
# structure_slug=structure_slug)
# else:
# for k,v in get_labeled_errors(form).items():
# messages.add_message(request, messages.ERROR,
# "<b>{}</b>: {}".format(k, strip_tags(v)))
# d = {'form': form,
# 'structure': structure,
# 'sub_title': structure,
# 'title': title,}
# response = render(request, template, d)
# return response

# FRONTEND ACTION DISABLED
# @login_required
# @is_manager
# def structure_protocol_configuration_delete(request, structure_slug,
# configuration_id, structure):
# """
# Deletes a structure protocol configuration

# :type structure_slug: String
# :type configuration_id: Integer
# :type structure: OrganizationalStructure (from @is_manager)

# :param structure_slug: structure slug
# :param configuration_id: protocol configuration pk
# :param structure: structure object (from @is_manager/@is_operator)

# :return: redirect
# """
# configuration = get_object_or_404(OrganizationalStructureWSProtocollo,
# organizational_structure=structure,
# pk=configuration_id)

# #effettuare tutti i controlli sui moduli che
# #hanno il protocollo obbligatorio e che ereditano questa
# #configurazione del protocollo!
# categories = TicketCategory.objects.filter(organizational_structure=structure,
# protocol_required=True)
# for cat in categories:
# if not cat.get_active_protocol_configuration():
# cat.protocol_required = False
# cat.save(update_fields=['protocol_required',])
# messages.add_message(request, messages.INFO,
# _("Nessuna configurazione di protocollo "
# "valida per la tipologia <b>{}</b>. "
# "Protocollo obbligatorio disabilitato."
# "").format(cat))

# messages.add_message(request, messages.SUCCESS,
# _("Configurazione <b>{}</b> eliminata correttamente"
# "").format(configuration))
# configuration.delete()
# return redirect('uni_ticket:manager_user_settings',
# structure_slug=structure_slug)

# FRONTEND ACTION DISABLED
# @login_required
# @is_manager
# def structure_protocol_configuration_disable(request, structure_slug,
# configuration_id, structure):
# """
# Disables a structure protocol configuration

# :type structure_slug: String
# :type configuration_id: Integer
# :type structure: OrganizationalStructure (from @is_manager)

# :param structure_slug: structure slug
# :param configuration_id: protocol configuration pk
# :param structure: structure object (from @is_manager/@is_operator)

# :return: redirect
# """
# configuration = get_object_or_404(OrganizationalStructureWSProtocollo,
# organizational_structure=structure,
# pk=configuration_id)

# if configuration.is_active:
# configuration.is_active = False
# configuration.save(update_fields = ['is_active', 'modified'])
# messages.add_message(request, messages.SUCCESS,
# _("Configurazione <b>{}</b> disattivata con successo"
# "").format(configuration))

# #effettuare tutti i controlli sui moduli che
# #hanno il protocollo obbligatorio e che ereditano questa
# #configurazione del protocollo!
# categories = TicketCategory.objects.filter(organizational_structure=structure,
# protocol_required=True)
# for cat in categories:
# if not cat.get_active_protocol_configuration():
# cat.protocol_required = False
# cat.save(update_fields=['protocol_required',])
# messages.add_message(request, messages.INFO,
# _("Nessuna configurazione di protocollo "
# "valida per la tipologia  <b>{}</b>. "
# "Protocollo obbligatorio disabilitato."
# "".format(cat)))

# #log action
# logger.info('[{}] manager of structure {}'
# ' {} disabled the protocol configuration {}'
# ''.format(timezone.localtime(),
# structure,
# request.user,
# configuration))
# else:
# messages.add_message(request, messages.ERROR,
# _("Configurazione {} già disattivata"
# "").format(configuration))

# return redirect('uni_ticket:manager_user_settings',
# structure_slug=structure_slug)

# FRONTEND ACTION DISABLED
# @login_required
# @is_manager
# def structure_protocol_configuration_enable(request, structure_slug,
# configuration_id, structure):
# """
# Enables a structure protocol configuration

# :type structure_slug: String
# :type configuration_id: Integer
# :type structure: OrganizationalStructure (from @is_manager)

# :param structure_slug: structure slug
# :param configuration_id: protocol configuration pk
# :param structure: structure object (from @is_manager/@is_operator)

# :return: redirect
# """
# configuration = get_object_or_404(OrganizationalStructureWSProtocollo,
# organizational_structure=structure,
# pk=configuration_id)
# if configuration.is_active:
# messages.add_message(request,
# messages.ERROR,
# _("Configurazione {} già attivata"
# "".format(configuration)))
# else:
# configuration.is_active = True
# configuration.save(update_fields = ['is_active', 'modified'])

# #only one
# #MADE BY SIGNAL!
# #configuration.disable_other_configurations()

# messages.add_message(request, messages.SUCCESS,
# _("Configurazione <b>{}</b> attivata con successo"
# "").format(configuration))

# #log action
# logger.info('[{}] manager of structure {}'
# ' {} enabled the protocol configuration {}'
# ''.format(timezone.localtime(),
# structure,
# request.user,
# configuration))

# return redirect('uni_ticket:manager_user_settings',
# structure_slug=structure_slug)


@login_required
@is_manager
def category_protocol_configuration_detail(
    request, structure_slug, category_slug, configuration_id, structure
):
    """
    Category protocol configuration detail

    :type structure_slug: String
    :type category_slug: String
    :type configuration_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param configuration_id: protocol configuration pk
    :param structure: structure object (from @is_manager/@is_operator)

    :return: response
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    configuration = TicketCategoryWSProtocollo.objects.filter(
        ticket_category=category, pk=configuration_id
    ).first()

    template = "manager/category_protocol_configuration_detail.html"
    title = _("Configurazione protocollo informatico")

    form = CategoryWSProtocolloModelForm(instance=configuration)

    if request.method == "POST":
        form = CategoryWSProtocolloModelForm(
            instance=configuration, data=request.POST)
        if form.is_valid():
            configuration.name = form.cleaned_data.get("name")
            configuration.protocollo_cod_titolario = form.cleaned_data.get(
                "protocollo_cod_titolario"
            )
            configuration.protocollo_uo = form.cleaned_data.get(
                "protocollo_uo")
            configuration.protocollo_uo_rpa = form.cleaned_data.get(
                "protocollo_uo_rpa")
            configuration.protocollo_uo_rpa_username = form.cleaned_data.get(
                "protocollo_uo_rpa_username"
            )
            configuration.protocollo_uo_rpa_matricola = form.cleaned_data.get(
                "protocollo_uo_rpa_matricola"
            )
            configuration.protocollo_send_email = form.cleaned_data.get(
                "protocollo_send_email"
            )
            configuration.protocollo_email = form.cleaned_data.get(
                "protocollo_email")
            configuration.protocollo_fascicolo_numero = form.cleaned_data.get(
                "protocollo_fascicolo_numero"
            )
            configuration.protocollo_fascicolo_anno = form.cleaned_data.get(
                "protocollo_fascicolo_anno"
            )
            configuration.save(
                update_fields=[
                    "name",
                    "modified",
                    "protocollo_cod_titolario",
                    "protocollo_uo",
                    "protocollo_uo_rpa",
                    "protocollo_uo_rpa_username",
                    "protocollo_uo_rpa_matricola",
                    "protocollo_send_email",
                    "protocollo_email",
                    "protocollo_fascicolo_numero",
                    "protocollo_fascicolo_anno",
                ]
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Configurazione protocollo informatico aggiornata"),
            )
            return redirect(
                "uni_ticket:manager_category_protocol_configuration_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
                configuration_id=configuration.pk,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "category": category,
        "configuration": configuration,
        "form": form,
        "structure": structure,
        "sub_title": category,
        "title": title,
    }
    response = render(request, template, base_context(d))
    return response


@login_required
@is_manager
def category_protocol_configuration_new(
    request, structure_slug, category_slug, structure
):
    """
    Creates a new protocol configuration for category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuova configuratione del protocollo informatico")
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    form = CategoryWSProtocolloModelForm()

    if request.method == "POST":
        form = CategoryWSProtocolloModelForm(data=request.POST)

        if form.is_valid():
            configuration = form.save(commit=False)
            configuration.ticket_category = category
            configuration.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the new protocol configuration {}"
                " for category {}".format(
                    timezone.localtime(),
                    structure,
                    request.user,
                    configuration,
                    category,
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Configurazione creata con successo")
            )

            return redirect(
                "uni_ticket:manager_category_protocol_configuration_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
                configuration_id=configuration.pk,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/category_protocol_configuration_new.html"
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": category,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_protocol_configuration_delete(
    request, structure_slug, category_slug, configuration_id, structure
):
    """
    Deletes a category protocol configuration

    :type structure_slug: String
    :type category_slug: String
    :type configuration_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param configuration_id: protocol configuration pk
    :param structure: structure object (from @is_manager/@is_operator)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    configuration = TicketCategoryWSProtocollo.objects.filter(
        ticket_category=category, pk=configuration_id
    ).first()

    if not category.get_active_protocol_configuration():
        category.protocol_required = False
        category.save(update_fields=["protocol_required", "modified"])
        messages.add_message(
            request,
            messages.INFO,
            _(
                "Nessuna configurazione di protocollo "
                "valida per la tipologia. "
                "Protocollo obbligatorio disabilitato."
                ""
            ).format(category),
        )

    messages.add_message(
        request,
        messages.SUCCESS,
        _("Configurazione <b>{}</b> eliminata correttamente" "").format(configuration),
    )
    configuration.delete()
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_protocol_configuration_disable(
    request, structure_slug, category_slug, configuration_id, structure
):
    """
    Disables a category protocol configuration

    :type structure_slug: String
    :type category_slug: String
    :type configuration_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param configuration_id: protocol configuration pk
    :param structure: structure object (from @is_manager/@is_operator)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    configuration = TicketCategoryWSProtocollo.objects.filter(
        ticket_category=category, pk=configuration_id
    ).first()
    if configuration.is_active:
        configuration.is_active = False
        configuration.save(update_fields=["is_active", "modified"])

        category.protocol_required = False
        category.save(update_fields=["protocol_required", "modified"])

        # signal active here to disable category protocol flag

        messages.add_message(
            request,
            messages.SUCCESS,
            _("Configurazione <b>{}</b> disattivata con successo" "").format(
                configuration
            ),
        )
        messages.add_message(
            request,
            messages.INFO,
            _(
                "Nessuna configurazione di protocollo "
                "valida per la tipologia. "
                "Protocollo obbligatorio disabilitato."
                ""
            ).format(category),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled the category {} protocol configuration {}"
            "".format(
                timezone.localtime(), structure, request.user, category, configuration
            )
        )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("Configurazione {} già disattivata" "").format(configuration),
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_protocol_configuration_enable(
    request, structure_slug, category_slug, configuration_id, structure
):
    """
    Enables a category protocol configuration

    :type structure_slug: String
    :type category_slug: String
    :type configuration_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param configuration_id: protocol configuration pk
    :param structure: structure object (from @is_manager/@is_operator)

    :return: redirect
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    configuration = TicketCategoryWSProtocollo.objects.filter(
        ticket_category=category, pk=configuration_id
    ).first()

    if configuration.is_active:
        messages.add_message(
            request,
            messages.ERROR,
            _("Configurazione {} già attivata" "").format(configuration),
        )

    else:
        configuration.is_active = True
        configuration.save(update_fields=["is_active", "modified"])

        # only one
        # MADE BY SIGNAL!
        # configuration.disable_other_configurations()

        messages.add_message(
            request,
            messages.SUCCESS,
            _("Configurazione <b>{}</b> attivata con successo" "").format(
                configuration
            ),
        )

        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled the category {} protocol configuration {}"
            "".format(
                timezone.localtime(), structure, request.user, category, configuration
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def manager_settings_check_protocol(request, structure_slug, structure):
    """
    Test the protocol system

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)

    :return: redirect
    """
    try:
        protocol_number = ticket_protocol(
            user=request.user, subject="test {}".format(request.user), test=True
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Il sistema di protocollo ha risposto correttamente."),
        )
    except Exception as e:
        logger.error("Errore Protocollazione: {} - {}".format(request.user, e))
        messages.add_message(
            request, messages.ERROR, _(
                "<b>Errore protocollo</b>: {}").format(e)
        )
    return redirect("uni_ticket:manager_user_settings", structure_slug=structure_slug)


@login_required
@is_manager
def category_default_reply_new(request, structure_slug, category_slug, structure):
    """
    Creates a new default ticket reply for category

    :type structure_slug: String
    :type category_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuova risposta predefinita per chiusura ticket")
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    form = CategoryDefaultReplyForm()
    if request.method == "POST":
        form = CategoryDefaultReplyForm(request.POST)
        if form.is_valid():
            default_reply = form.save(commit=False)
            default_reply.text = strip_tags(form.cleaned_data["text"])
            default_reply.ticket_category = category
            default_reply.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the new default reply {}"
                " for category {}".format(
                    timezone.localtime(),
                    structure,
                    request.user,
                    default_reply,
                    category,
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Risposta predefinita creata con successo")
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/category_default_reply_add_new.html"
    d = {
        "category": category,
        "form": form,
        "structure": structure,
        "sub_title": category,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def category_default_reply_delete(
    request, structure_slug, category_slug, default_reply_id, structure
):
    """
    Deletes default_reply from a category

    :type structure_slug: String
    :type category_slug: String
    :type default_reply_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param default_reply_id: default_reply id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    default_reply = get_object_or_404(
        TicketCategoryDefaultReply, pk=default_reply_id, ticket_category=category
    )
    messages.add_message(
        request, messages.SUCCESS, _(
            "Risposta predefinita eliminata correttamente")
    )

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} deleted a default reply"
        " for category {}".format(
            timezone.localtime(), structure, request.user, category
        )
    )

    default_reply.delete()
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_default_reply_disable(
    request, structure_slug, category_slug, default_reply_id, structure
):
    """
    Disables a default_reply from a category

    :type structure_slug: String
    :type category_slug: String
    :type default_reply_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param default_reply_id: default_reply id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    default_reply = get_object_or_404(
        TicketCategoryDefaultReply, pk=default_reply_id, ticket_category=category
    )
    if default_reply.is_active:
        default_reply.is_active = False
        default_reply.save(update_fields=["is_active"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Risposta predefinita disattivata con successo"),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled a default reply"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )
    else:
        messages.add_message(
            request, messages.ERROR, _("Risposta predefinita già disattivata")
        )
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_default_reply_enable(
    request, structure_slug, category_slug, default_reply_id, structure
):
    """
    Enables a default_reply from a category

    :type structure_slug: String
    :type category_slug: String
    :type default_reply_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param default_reply_id: default_reply id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    default_reply = get_object_or_404(
        TicketCategoryDefaultReply, pk=default_reply_id, ticket_category=category
    )
    if default_reply.is_active:
        messages.add_message(
            request, messages.ERROR, _("Risposta predefinita già attivata")
        )
    else:
        default_reply.is_active = True
        default_reply.save(update_fields=["is_active"])
        messages.add_message(
            request, messages.SUCCESS, _(
                "Risposta predefinita attivata con successo")
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled a default reply"
            " for category {}".format(
                timezone.localtime(), structure, request.user, category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def category_default_reply_detail(
    request, structure_slug, category_slug, default_reply_id, structure
):
    """
    Shows default_reply details

    :type structure_slug: String
    :type category_slug: String
    :type default_reply_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param category_slug: category slug
    :param default_reply_id: default_reply id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Gestione dettaglio risposta predefinita")
    template = "manager/category_default_reply_detail.html"
    category = get_object_or_404(
        TicketCategory, organizational_structure=structure, slug=category_slug
    )
    default_reply = get_object_or_404(
        TicketCategoryDefaultReply, pk=default_reply_id, ticket_category=category
    )
    form = CategoryDefaultReplyForm(instance=default_reply)
    if request.method == "POST":
        form = CategoryDefaultReplyForm(
            instance=default_reply, data=request.POST)
        if form.is_valid():
            # edited_default_reply = form.save(commit=False)
            default_reply.text = strip_tags(form.cleaned_data["text"])
            default_reply.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited a default_reply"
                " for category {}".format(
                    timezone.localtime(), structure, request.user, category
                )
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Risposta predefinita modificata con successo"),
            )
            return redirect(
                "uni_ticket:manager_category_default_reply_detail",
                structure_slug=structure_slug,
                category_slug=category_slug,
                default_reply_id=default_reply_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "category": category,
        "default_reply": default_reply,
        "form": form,
        "structure": structure,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def structure_alert_new(request, structure_slug, structure):
    """
    Creates a new alert for organizational structure

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager)

    :return: render
    """
    title = _("Nuovo alert per gli utenti")
    form = OrganizationalStructureAlertForm()
    if request.method == "POST":
        form = OrganizationalStructureAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.organizational_structure = structure
            alert.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} created the new alert {}"
                "".format(timezone.localtime(), structure, request.user, alert)
            )

            messages.add_message(
                request, messages.SUCCESS, _("Alert creato con successo")
            )
            return redirect(
                "uni_ticket:manager_user_settings", structure_slug=structure_slug
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    template = "manager/structure_alert_add_new.html"
    d = {
        "form": form,
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
@is_manager
def structure_alert_delete(request, structure_slug, alert_id, structure):
    """
    Deletes alert from a structure

    :type structure_slug: String
    :type alert_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param alert_id: alert id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    alert = get_object_or_404(
        OrganizationalStructureAlert, pk=alert_id, organizational_structure=structure
    )
    messages.add_message(
        request, messages.SUCCESS, _(
            "Alert {} eliminato correttamente").format(alert)
    )

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} deleted alert {}".format(
            timezone.localtime(), structure, request.user, alert
        )
    )

    alert.delete()
    return redirect("uni_ticket:manager_user_settings", structure_slug=structure_slug)


@login_required
@is_manager
def structure_alert_edit(request, structure_slug, alert_id, structure):
    """
    Edits alert details

    :type structure_slug: String
    :type alert_id: Integer
    :type structure: OrganizationalStructure (from @is_manager)

    :param structure_slug: structure slug
    :param alert_id: alert id
    :param structure: structure object (from @is_manager)

    :return: render
    """
    alert = get_object_or_404(
        OrganizationalStructureAlert, pk=alert_id, organizational_structure=structure
    )
    # alert.disable_if_expired()
    form = OrganizationalStructureAlertForm(instance=alert)
    if request.method == "POST":
        form = OrganizationalStructureAlertForm(
            instance=alert, data=request.POST)
        if form.is_valid():
            alert_condition = form.save(commit=False)
            alert_condition.text = strip_tags(form.cleaned_data["text"])
            alert_condition.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited alert {}".format(
                    timezone.localtime(), structure, request.user, alert
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _("Alert modificato con successo")
            )
            return redirect(
                "uni_ticket:manager_user_settings", structure_slug=structure_slug
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    template = "manager/structure_alert_edit.html"
    title = _("Modifica alert")
    sub_title = alert
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))

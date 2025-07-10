import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from django_form_builder.utils import get_labeled_errors

from uni_ticket.decorators import is_manager
from uni_ticket.models import TicketCategory
from uni_ticket.utils import base_context

from . forms import IOServiceTicketCategoryForm
from . models import IOServiceTicketCategory


logger = logging.getLogger(__name__)


@login_required
@is_manager
def new(request, structure_slug, category_slug, structure):
    """
    """
    if not structure.app_io_enabled:
        raise PermissionDenied

    category = get_object_or_404(
        TicketCategory,
        organizational_structure=structure,
        slug=category_slug
    )
    title = _("Nuovo servizo App IO")
    sub_title = _("Aggiungi un nuovo servizio alla tipologia di richiesta {}").format(
        category.name
    )
    template = "manager/category_app_io_service_new.html"
    form = IOServiceTicketCategoryForm(category=category)

    if request.method == "POST":
        form = IOServiceTicketCategoryForm(category=category, data=request.POST)
        if form.is_valid():
            new_service = form.save(commit=False)
            new_service.category = category
            new_service.save()

            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} added the App IO Service {}"
                " in the category {}".format(
                    timezone.localtime(),
                    structure,
                    request.user,
                    new_service.service,
                    category
                )
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Servizio App IO <b>{}</b>" " aggiunto con successo").format(
                    new_service.service
                ),
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

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
def edit(request, structure_slug, category_slug, service_id, structure):
    """
    """
    if not structure.app_io_enabled:
        raise PermissionDenied

    category = get_object_or_404(
        TicketCategory,
        organizational_structure=structure,
        slug=category_slug
    )
    service = get_object_or_404(
        IOServiceTicketCategory,
        category=category,
        pk=service_id
    )
    title = _("Modifica servizo App IO")
    sub_title = _("Modifica il servizio {}").format(service.service)
    template = "manager/category_app_io_service_edit.html"
    form = IOServiceTicketCategoryForm(category=category, instance=service)

    if request.method == "POST":
        form = IOServiceTicketCategoryForm(category=category,
                                           instance=service,
                                           data=request.POST)
        if form.is_valid():
            service = form.save()
            # log action
            logger.info(
                "[{}] manager of structure {}"
                " {} edited the App IO Service {}"
                " in the category {}".format(
                    timezone.localtime(),
                    structure,
                    request.user,
                    service.service,
                    category
                )
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Servizio App IO <b>{}</b>" " modificato con successo").format(
                    service.service
                ),
            )
            return redirect(
                "uni_ticket:manager_category_detail",
                structure_slug=structure_slug,
                category_slug=category_slug
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

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
def enable(request, structure_slug, category_slug, service_id, structure):
    """
    """
    if not structure.app_io_enabled:
        raise PermissionDenied

    category = get_object_or_404(
        TicketCategory,
        organizational_structure=structure,
        slug=category_slug
    )
    service = get_object_or_404(
        IOServiceTicketCategory,
        category=category,
        pk=service_id
    )

    if service.is_active:
        messages.add_message(
            request, messages.ERROR, _(
                "Servizio App IO <b>{}</b> già attivato").format(service.service)
        )
    else:
        service.disable_other_services()
        service.is_active = True
        service.save(update_fields=["is_active", "modified"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Servizio App IO <b>{}</b> attivato con successo").format(service.service),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} enabled the App IO Service {}"
            " for category {}".format(
                timezone.localtime(),
                structure,
                request.user,
                service.service,
                category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def disable(request, structure_slug, category_slug, service_id, structure):
    """
    """
    if not structure.app_io_enabled:
        raise PermissionDenied

    category = get_object_or_404(
        TicketCategory,
        organizational_structure=structure,
        slug=category_slug
    )
    service = get_object_or_404(
        IOServiceTicketCategory,
        category=category,
        pk=service_id
    )

    if not service.is_active:
        messages.add_message(
            request, messages.ERROR, _(
                "Servizio App IO <b>{}</b> già disattivato").format(service.service)
        )
    else:
        service.is_active = False
        service.save(update_fields=["is_active", "modified"])
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Servizio App IO <b>{}</b> disattivato con successo").format(service.service),
        )
        # log action
        logger.info(
            "[{}] manager of structure {}"
            " {} disabled the App IO Service {}"
            " for category {}".format(
                timezone.localtime(),
                structure,
                request.user,
                service.service,
                category
            )
        )

    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )


@login_required
@is_manager
def delete(request, structure_slug, category_slug, service_id, structure):
    """
    """
    if not structure.app_io_enabled:
        raise PermissionDenied

    category = get_object_or_404(
        TicketCategory,
        organizational_structure=structure,
        slug=category_slug
    )
    service = get_object_or_404(
        IOServiceTicketCategory,
        category=category,
        pk=service_id
    )
    messages.add_message(
        request,
        messages.SUCCESS,
        _("Servizio App IO <b>{}</b> eliminato correttamente").format(service.service),
    )

    # log action
    logger.info(
        "[{}] manager of structure {}"
        " {} deleted the App IO Service {}"
        " for category {}".format(
            timezone.localtime(),
            structure,
            request.user,
            service.service,
            category
        )
    )

    service.delete()
    return redirect(
        "uni_ticket:manager_category_detail",
        structure_slug=structure_slug,
        category_slug=category_slug,
    )

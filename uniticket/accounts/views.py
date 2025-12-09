from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from uni_ticket.jwts import encrypt_to_jwe, decrypt_from_jwe
from uni_ticket.settings import MSG_FOOTER, MSG_HEADER
from uni_ticket.utils import base_context, send_custom_mail

from . forms import UserDataForm
from . settings import *


@login_required
def changeData(request): # pragma: no cover
    initial = {}
    for field in EDITABLE_FIELDS:
        initial[field] = getattr(request.user, field)
    form = UserDataForm(initial=initial)
    template = "change_user_data.html"
    user = request.user
    user_email = user.email

    if request.POST:
        form = UserDataForm(request.POST, instance=user)
        if form.is_valid():
            email = form.cleaned_data.pop('email', '')
            if len(form.cleaned_data) > 1:
                user = form.save(commit=False)
                user.manual_user_update = timezone.now()
                user.save()
                messages.add_message(
                    request, messages.SUCCESS, _("Dati salvati con successo")
                )

            if 'email' in EDITABLE_FIELDS and email != user_email:
                base_url = request.build_absolute_uri(
                    reverse("accounts:confirm_email")
                )
                token = f'{request.user.id}|{email}|{timezone.now()}'
                encrypted_data = encrypt_to_jwe(token)
                url = f'{base_url}?token={encrypted_data}'
                body=_("Conferma la tua email cliccando qui:\n\n<{}>").format(url)
                msg_body = f'{MSG_HEADER.format(hostname=settings.HOSTNAME)}{body}{MSG_FOOTER}'
                result = send_mail(
                    subject=_("Conferma email"),
                    message=msg_body,
                    from_email=settings.EMAIL_SENDER,
                    recipient_list=[email],
                    fail_silently=True,
                )
                messages.add_message(
                    request, messages.INFO, _("E' stata inviata un'email all'indirizzo di posta che hai indicato. Clicca sul link contenuto nel messaggio per confermare i nuovi dati")
                )
            return redirect("accounts:change_data")
        else:
            messages.add_message(
                request, messages.ERROR, _("Dati errati")
            )

    d = base_context({'form': form, 'title': _("Modifica dati personali"),})
    return render(request, template, d)


@login_required
def confirmEmail(request): # pragma: no cover
    token = request.GET.get('token')
    if not token:
        messages.add_message(
            request, messages.ERROR, _("Token mancante")
        )
        return redirect("accounts:change_data")

    try:
        data = decrypt_from_jwe(token).decode()
        items = data.split("|")
    except:
        messages.add_message(
            request, messages.ERROR, _("Token non valido")
        )
        return redirect("accounts:change_data")

    user_id = items[0]
    email = items[1]
    timestamp = items[2]

    user = get_object_or_404(get_user_model(), pk=user_id)
    token_date = parse_datetime(timestamp)
    time_diff = timezone.now() - token_date

    token_life_expired = time_diff.total_seconds() / 60 > CHANGE_EMAIL_TOKEN_LIFE
    token_invalid = user.manual_user_update and token_date < user.manual_user_update

    if token_life_expired or token_invalid:
        messages.add_message(
            request, messages.ERROR, _("Token scaduto")
        )
        return redirect("accounts:change_data")

    user.email = email
    user.manual_user_update = timezone.now()
    user.save(update_fields=['email', 'manual_user_update'])
    messages.add_message(
        request, messages.SUCCESS, _("Email aggiornata con successo")
    )
    return redirect("uni_ticket:user_settings")

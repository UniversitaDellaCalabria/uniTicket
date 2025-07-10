import ast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from uni_ticket.jwts import encrypt_to_jwe, decrypt_from_jwe
from uni_ticket.settings import MSG_FOOTER, MSG_HEADER
from uni_ticket.utils import base_context, send_custom_mail

from . forms import *
from . settings import *


@login_required
def changeData(request):
    initial = {}
    for field in EDITABLE_FIELDS:
        initial[field] = getattr(request.user, field)
    form = UserDataForm(initial=initial)
    template = "change_user_data.html"
    user = request.user
    user_email = user.email

    if request.method == 'POST':
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
                body=_("Conferma la tua email cliccando qui {}").format(url)
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
def confirmEmail(request):
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


def registration(request):
    if request.user.is_authenticated:
        return redirect("/")
    form = RegistrationForm()
    template = "user_registration.html"

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            if get_user_model().objects.filter(taxpayer_id__iexact=form.cleaned_data['taxpayer_id']).exists():
                messages.add_message(
                    request, messages.ERROR, _("Questo codice fiscale è già presente in anagrafica")
                )
            else:
                base_url = request.build_absolute_uri(
                    reverse("accounts:confirm_registration")
                )
                token = f'{form.cleaned_data}|{timezone.now()}'
                encrypted_data = encrypt_to_jwe(token)
                url = f'{base_url}?token={encrypted_data}'
                body=_("Conferma la tua registrazione cliccando qui {}").format(url)
                msg_body = f'{MSG_HEADER.format(hostname=settings.HOSTNAME)}{body}{MSG_FOOTER}'
                result = send_mail(
                    subject=_("Conferma registrazione"),
                    message=msg_body,
                    from_email=settings.EMAIL_SENDER,
                    recipient_list=[form.cleaned_data['email']],
                    fail_silently=True,
                )
                messages.add_message(
                    request, messages.INFO, _("E' stata inviata un'email all'indirizzo di posta che hai indicato. Clicca sul link contenuto nel messaggio per completare la registrazione")
                )
                return redirect("accounts:registration")
        else:
            messages.add_message(
                request, messages.ERROR, _("Dati errati")
            )

    d = base_context(
        {'form': form,
         'title': _("Crea il tuo account"),}
    )
    return render(request, template, d)


def confirmRegistration(request):
    if request.user.is_authenticated:
        return redirect("/")
    token = request.GET.get('token')
    if not token:
        messages.add_message(
            request, messages.ERROR, _("Token mancante")
        )
        return redirect("accounts:registration")

    try:
        data = decrypt_from_jwe(token).decode()
        items = data.split("|")
    except:
        messages.add_message(
            request, messages.ERROR, _("Token non valido")
        )
        return redirect("accounts:registration")

    cleaned_data = ast.literal_eval(items[0])
    timestamp = items[1]

    user_exists = get_user_model().objects.filter(taxpayer_id__iexact=cleaned_data['taxpayer_id']).exists()

    if user_exists:
        messages.add_message(
            request, messages.ERROR, _("Questo codice fiscale è già presente in anagrafica")
        )
        return redirect("accounts:change_data")

    token_date = parse_datetime(timestamp)
    time_diff = timezone.now() - token_date
    token_life_expired = time_diff.total_seconds() / 60 > USER_REGISTRATION_TOKEN_LIFE

    if token_life_expired:
        messages.add_message(
            request, messages.ERROR, _("Token scaduto")
        )
        return redirect("accounts:change_data")

    get_user_model().objects.create(
        username=cleaned_data['taxpayer_id'],
        first_name=cleaned_data['first_name'],
        last_name=cleaned_data['last_name'],
        taxpayer_id=cleaned_data['taxpayer_id'].upper(),
        email=cleaned_data['email'],
        is_active=True,
        password = make_password(cleaned_data['password'])
    )
    messages.add_message(
        request, messages.SUCCESS, _("Registrazione avvenuta con successo")
    )
    return redirect("/")


def passwordReset(request):
    template = "change_password.html"
    title = _("Imposta la nuova password")

    if request.user.is_authenticated:
        form = RegisteredUserPasswordForm()
        user = request.user
    else:
        token = request.GET.get('token')

        if not token:
            return redirect("accounts:password_reset_email")
        try:
            data = decrypt_from_jwe(token).decode()
            items = data.split("|")
        except:
            messages.add_message(
                request, messages.ERROR, _("Token non valido")
            )
            return redirect("login")

        taxpayer_id = items[0]
        timestamp = items[1]

        user = get_user_model().objects.filter(taxpayer_id__iexact=taxpayer_id).first()

        if not user:
            messages.add_message(
                request, messages.ERROR, _("Questo codice fiscale non è associato ad alcun utente registrato")
            )
            return redirect("/")

        token_date = parse_datetime(timestamp)
        time_diff = timezone.now() - token_date
        token_life_expired = time_diff.total_seconds() / 60 > CHANGE_EMAIL_TOKEN_LIFE
        token_invalid = user.manual_user_update and token_date < user.manual_user_update

        if token_invalid:
            messages.add_message(
                request, messages.ERROR, _("Token scaduto")
            )
            return redirect("login")

        form = PasswordForm()

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = RegisteredUserPasswordForm(data=request.POST)
        else:
            form = PasswordForm(data=request.POST)
        if form.is_valid():
            if 'old_password' in form.cleaned_data:
                if not user.check_password(form.cleaned_data['old_password']):
                    messages.add_message(
                        request, messages.ERROR, _("Password attuale errata")
                    )
                    return redirect("accounts:password_reset")
            user.password = make_password(form.cleaned_data['password'])
            user.manual_user_update = timezone.now()
            user.save(update_fields=['password', 'manual_user_update'])
            messages.add_message(
                request, messages.SUCCESS, _("Password aggiornata con successo")
            )
            body=_("La password è stata correttamente aggiornata")
            msg_body = f'{MSG_HEADER.format(hostname=settings.HOSTNAME)}{body}{MSG_FOOTER}'
            send_mail(
                subject=_("Password aggiornata con successo"),
                message=msg_body,
                from_email=settings.EMAIL_SENDER,
                recipient_list=[user.email],
                fail_silently=True,
            )
            return redirect("/")
        else:
            messages.add_message(
                request, messages.ERROR, _("Dati errati")
            )

    d = base_context({'form': form, 'title': title})
    return render(request, template, d)


def passwordResetEmail(request):
    template = "change_password.html"
    title = _("Inserisci il tuo codice fiscale")

    if request.user.is_authenticated:
        return redirect("login")
    else:
        form = PasswordEmailForm()

        if request.method == 'POST':
            form = PasswordEmailForm(data=request.POST)
            if form.is_valid():
                base_url = request.build_absolute_uri(
                    reverse("accounts:password_reset")
                )
                token = f'{form.cleaned_data["taxpayer_id"]}|{timezone.now()}'
                encrypted_data = encrypt_to_jwe(token)
                url = f'{base_url}?token={encrypted_data}'
                body=_("Resetta la tua password cliccando qui {}").format(url)
                msg_body = f'{MSG_HEADER.format(hostname=settings.HOSTNAME)}{body}{MSG_FOOTER}'
                user = get_user_model().objects.filter(taxpayer_id__iexact=form.cleaned_data['taxpayer_id']).first()
                if user and user.email:
                    result = send_mail(
                        subject=_("Reset password"),
                        message=msg_body,
                        from_email=settings.EMAIL_SENDER,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                messages.add_message(
                    request, messages.INFO, _("E' stata inviata un'email all'indirizzo di posta associato al codice fiscale che hai indicato. Clicca sul link contenuto nel messaggio per resettare la tua password")
                )
                return redirect("/")
            else:
                messages.add_message(
                    request, messages.ERROR, _("Dati errati")
                )

    d = base_context({'form': form, 'title': title,})
    return render(request, template, d)

import copy

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


from django_form_builder import dynamic_fields

from . settings import EDITABLE_FIELDS, REQUIRED_FIELDS


class UserDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in EDITABLE_FIELDS:
            if field in REQUIRED_FIELDS:
                self.fields[field].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'email' in EDITABLE_FIELDS:
            instance.email = self.initial['email']
        if commit:
            instance.save()
        return instance

    class Meta:
        model = get_user_model()
        fields = EDITABLE_FIELDS
        labels = {'email': 'E-mail'}

from django_form_builder.forms import BaseDynamicForm
class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label=_("Password")
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label=_("Ripeti Password")
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'taxpayer_id', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['taxpayer_id'].required = True
        self.fields['email'].required = True

        captcha_data = {
            "label": _('Codice di verifica'),
            "captcha_name": dynamic_fields.format_field_name('captcha'),
            "captcha_hidden_name": dynamic_fields.format_field_name(
                'hidden_captcha'
            ),
        }
        captcha_field = getattr(dynamic_fields, "CustomCaptchaComplexField")(
            **captcha_data
        )
        captcha_field.define_value(custom_value="")
        for single_field in captcha_field.get_fields():
            self.fields[single_field.name] = single_field


    def clean(self):
        cleaned_data = super().clean()

        self.data = copy.deepcopy(self.data)

        # CaPTCHA MUST BE ALWAYS RENEWED!
        for field_name, field_obj in self.fields.items():
            if type(field_obj) in (dynamic_fields.CaptchaField,
                                   dynamic_fields.CaptchaHiddenField):
                self.data[field_name] = self.fields[field_name].widget.attrs['value']
        # end CAPTCHA

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("password", _("Le password non coincidono."))
            self.add_error("confirm_password", _("Le password non coincidono."))

        captcha_errors = self.fields['captcha'].parent.raise_error('captcha', cleaned_data)
        for captcha_error in captcha_errors:
            self.add_error('captcha', captcha_error)

        return cleaned_data

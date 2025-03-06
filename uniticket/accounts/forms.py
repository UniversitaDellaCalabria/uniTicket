from django.contrib.auth import get_user_model
from django.forms import ModelForm

from . settings import EDITABLE_FIELDS, REQUIRED_FIELDS


class UserDataForm(ModelForm):
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

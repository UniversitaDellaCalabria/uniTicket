from django.contrib.auth import get_user_model
from django.forms import ModelForm

from . settings import EDITABLE_FIELDS, REQUIRED_FIELDS


class UserDataForm(ModelForm):
    """Form to edit the user fields listed in EDITABLE_FIELDS.

    A new email is not saved by the form: it becomes effective only after
    the user confirms it (see views.changeData and views.confirmEmail).
    """
    def __init__(self, *args, **kwargs):
        """Mark as required the editable fields listed in REQUIRED_FIELDS.

        Args:
            *args: Positional arguments for ModelForm.
            **kwargs: Keyword arguments for ModelForm.

        Returns:
            None.
        """
        super().__init__(*args, **kwargs)
        for field in EDITABLE_FIELDS:
            if field in REQUIRED_FIELDS:
                self.fields[field].required = True

    def save(self, commit=True):
        """Save the user data, keeping the current email.

        Args:
            commit: If True, the user is also saved to the database.

        Returns:
            The updated User instance.
        """
        instance = super().save(commit=False)
        if 'email' in EDITABLE_FIELDS:
            # The submitted email is replaced with the initial one:
            # it is updated only by the confirmation link.
            instance.email = self.initial['email']
        if commit:
            instance.save()
        return instance

    class Meta:
        model = get_user_model()
        fields = EDITABLE_FIELDS
        labels = {'email': 'E-mail'}

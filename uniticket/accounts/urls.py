from django.urls import path

from . settings import EDITABLE_FIELDS
from . views import changeData, confirmEmail


app_name = "accounts"

# The personal data pages exist only if some field is editable.
if EDITABLE_FIELDS:
    urlpatterns = [
        path('account/edit/', changeData, name='change_data'),
        path('account/edit/confirm-email/', confirmEmail, name='confirm_email'),
    ]
else:
    urlpatterns = []

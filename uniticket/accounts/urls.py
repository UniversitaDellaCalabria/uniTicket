"""betaCRM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path

from . settings import EDITABLE_FIELDS
from . views import changeData, confirmEmail


app_name = "accounts"

if EDITABLE_FIELDS:
    urlpatterns = [
        # url(r'^login/$', Login, name='login'),
        # path('logout', Logout, name='logout'),
        path('account/edit/', changeData, name='change_data'),
        path('account/edit/confirm-email/', confirmEmail, name='confirm_email'),
    ]
else:
    urlpatterns = []

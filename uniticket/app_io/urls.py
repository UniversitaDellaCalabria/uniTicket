from django.urls import path

from uni_ticket.settings import MANAGEMENT_URL_PREFIX

from . views import *


app_name = "app_io"


base = f"{MANAGEMENT_URL_PREFIX['manager']}/<str:structure_slug>/categories/<str:category_slug>/app-io/services"


urlpatterns = [
    path(f'{base}/new/', new, name='app_io_services_new'),
    path(f'{base}/<int:service_id>/edit/', edit, name='app_io_services_edit'),
    path(f'{base}/<int:service_id>/enable/', enable, name='app_io_services_enable'),
    path(f'{base}/<int:service_id>/disable/', disable, name='app_io_services_disable'),
    path(f'{base}/<int:service_id>/delete/', delete, name='app_io_services_delete'),
]

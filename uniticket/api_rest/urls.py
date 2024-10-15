from django.urls import path, re_path
from rest_framework import routers
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas import get_schema_view

from api_rest.views import generic, manager, operator, user


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register('users', generic.UserViewSet)
router.register('groups', generic.GroupViewSet)

app_name = "api_rest"

urlpatterns = [
    # path('api/', include(router.urls)),
    # path('api-auth/', include(rest_framework.urls, 'rest_framework',)),

    re_path('^openapi/$',  get_schema_view(**{}), name='openapi-schema'),
    re_path('^openapi.json/$', get_schema_view(renderer_classes = [JSONOpenAPIRenderer], **{}), name='openapi-schema-json'),
    path('api/<slug:structure_slug>/<slug:category_slug>/ticket/new/', user.TicketAPIView.as_view(), name='api-new-ticket'),
    path('api/ticket/<str:ticket_uid>/', user.TicketAPIDetail.as_view(), name='api-view-ticket'),
    path('api/strutture/list/', generic.TicketAPIStruttureList.as_view(), name='api-strutture-list'),
    path('api/ticket/category/list/', generic.TicketAPITicketCategoryList.as_view(),name='api-ticket-category-list'),
    path('api/ticket/user/list/', user.TicketAPIListCreated.as_view(), name='api-ticket-user-list'),
    path('api/ticket/close/<str:ticket_id>/', user.TicketAPIClose.as_view(), name='api-ticket-close'),

    # manager
    path('api/manager/<slug:structure_slug>/tickets/count/', manager.TicketAPICounter.as_view(), name='api-manager-tickets-count'),

    # operator
    path('api/operator/<slug:structure_slug>/tickets/count/', operator.TicketAPICounter.as_view(), name='api-operator-tickets-count'),]

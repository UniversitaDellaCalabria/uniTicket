from django.urls import path, re_path
from rest_framework import routers
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas import get_schema_view

from api_rest.views import *

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register('groups', GroupViewSet)


urlpatterns = [
  # path('api/', include(router.urls)),
  # path('api-auth/', include(rest_framework.urls, 'rest_framework',)),

  re_path('^openapi$',  get_schema_view(**{}), name='openapi-schema'),
  re_path('^openapi.json$', get_schema_view(renderer_classes = [JSONOpenAPIRenderer], **{}), name='openapi-schema-json'),
  path('api/<slug:structure_slug>/<slug:category_slug>/ticket/new', TicketAPIView.as_view(), name='api-new-ticket'),
  path('api/ticket/<str:ticket_uid>', TicketAPIDetail.as_view(), name='api-view-ticket'),
  path('api/strutture/list', TicketAPIStruttureList.as_view(), name='api-strutture-list'),
  path('api/ticket/category/list', TicketAPITicketCategoryList.as_view(),name='api-ticket-category-list'),
  path('api/ticket/user/list', TicketAPIListCreated.as_view(), name='api-ticket-user-list'),
  path('api/ticket/close/<str:ticket_id>', TicketAPIClose.as_view(), name='api-ticket-close'),

  path('api/manager/<slug:structure_slug>/tickets/unassigned/count/', TicketAPIManagerUnassignedCount.as_view(), name='api-manager-tickets-unassigned-count'),
  path('api/manager/<slug:structure_slug>/tickets/open/count/', TicketAPIManagerOpenCount.as_view(), name='api-manager-tickets-open-count'),
  path('api/manager/<slug:structure_slug>/tickets/my-open/count/', TicketAPIManagerMyOpenCount.as_view(), name='api-manager-tickets-my-open-count'),

  path('api/operator/<slug:structure_slug>/tickets/unassigned/count/', TicketAPIOperatorUnassignedCount.as_view(), name='api-operator-tickets-unassigned-count'),
  path('api/operator/<slug:structure_slug>/tickets/open/count/', TicketAPIOperatorOpenCount.as_view(), name='api-operator-tickets-open-count'),
  path('api/operator/<slug:structure_slug>/tickets/my-open/count/', TicketAPIOperatorMyOpenCount.as_view(), name='api-operator-tickets-my-open-count'),

]

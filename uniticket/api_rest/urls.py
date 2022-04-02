from django.urls import path, include

from api_rest.views import GroupViewSet, UserViewSet
from rest_framework import routers

import rest_framework.urls

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register('groups', GroupViewSet)


urlpatterns = [
  path('api/', include(router.urls)),
  # path('api-auth/', include(rest_framework.urls, 'rest_framework',)),
]

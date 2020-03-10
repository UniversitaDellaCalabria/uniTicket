from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter

from . api import ChatMessageModelViewSet, UserModelViewSet
from . import views

router = DefaultRouter()
router.register(r'message', ChatMessageModelViewSet, basename='message-api')
router.register(r'user', UserModelViewSet, basename='user-api')

app_name="chat"

urlpatterns = [
    path(r'api/v1/', include(router.urls)),

    # path('', views.index, name='index'),
    path('chat/<str:room_name>/', views.room, name='room'),
]

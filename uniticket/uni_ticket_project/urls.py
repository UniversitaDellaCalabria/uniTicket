"""uni_ticket_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import uni_ticket.urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path, include

from djangosaml2 import views


@login_required
def test500(request):
    from django.http import HttpResponse

    # this avoid conflicts with unit tests
    if not hasattr(request, "META"):
        return HttpResponse(status=500)
    raise Exception()


urlpatterns = [
    path("{}/".format(getattr(settings, "ADMIN_PATH", "admin")), admin.site.urls),
    path("test500/", test500, name="test500"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += (path("", include(uni_ticket.urls, namespace="uni_ticket")),)

if settings.DEBUG:
    # STATICS FILE SERVE
    from django.views.static import serve

    urlpatterns.append(
        path(
            "{}/<path>".format(settings.STATIC_URL[1:-1]),
            serve,
            {"document_root": settings.STATIC_ROOT, "show_indexes": True},
        )
    )

if "nested_admin" in settings.INSTALLED_APPS:
    urlpatterns += (path("nested_admin/", include("nested_admin.urls")),)

if "saml2_sp" in settings.INSTALLED_APPS:
    import saml2_sp.urls

    # saml2_url_prefix = 'saml2'

    urlpatterns += (
        path(
            "",
            include(
                (
                    saml2_sp.urls,
                    "sp",
                )
            ),
        ),
    )

    urlpatterns += (
        path(
            "{}/login/".format(settings.SAML2_URL_PREFIX),
            views.LoginView.as_view(),
            name="login",
        ),
    )
    urlpatterns += (
        path(
            "{}/acs/".format(settings.SAML2_URL_PREFIX),
            views.AssertionConsumerServiceView.as_view(),
            name="saml2_acs",
        ),
    )
    urlpatterns += (
        path(
            "{}/logout/".format(settings.SAML2_URL_PREFIX),
            views.LogoutInitView.as_view(),
            name="logout",
        ),
    )
    urlpatterns += (
        path(
            "{}/ls/".format(settings.SAML2_URL_PREFIX),
            views.LogoutView.as_view(),
            name="saml2_ls",
        ),
    )
    urlpatterns += (
        path(
            "{}/ls/post/".format(settings.SAML2_URL_PREFIX),
            views.LogoutView.as_view(),
            name="saml2_ls_post",
        ),
    )
    urlpatterns += (
        path(
            "{}/metadata/".format(settings.SAML2_URL_PREFIX),
            views.MetadataView.as_view(),
            name="saml2_metadata",
        ),
    )

elif "spid_oidc_rp" in settings.INSTALLED_APPS:
    from django.views.generic.base import RedirectView

    urlpatterns += (
        path(
            "",
            include(("spid_oidc_rp.urls", "spid_oidc_rp"),
                    namespace="spid_oidc_rp"),
            name="spid_oidc_rp",
        ),
    )
    urlpatterns += (
        path(
            "oidc/login",
            RedirectView.as_view(url=f"{settings.LOGIN_URL}"),
            name="login",
        ),
    )
    urlpatterns += (
        path(
            "oidc/logout",
            RedirectView.as_view(url=f"{settings.LOGOUT_URL}"),
            name="logout",
        ),
    )

else:
    # local_url_prefix = 'local'
    urlpatterns += (
        path(
            "{}/login/".format(settings.LOCAL_URL_PREFIX),
            auth_views.LoginView.as_view(template_name="login.html"),
            name="login",
        ),
    )
    urlpatterns += (
        path(
            "{}/logout/".format(settings.LOCAL_URL_PREFIX),
            auth_views.LogoutView.as_view(
                template_name="logout.html", next_page="/"),
            name="logout",
        ),
    )


if "djangosaml2" in settings.INSTALLED_APPS:
    import djangosaml2.urls

    urlpatterns += (path("", include(djangosaml2.urls)),)

if "rest_framework" in settings.INSTALLED_APPS:
    import api_rest.urls

    urlpatterns += (path("", include(api_rest.urls)),)

if "chat" in settings.INSTALLED_APPS:
    import chat.urls

    urlpatterns += (path("", include(chat.urls, "chat")),)

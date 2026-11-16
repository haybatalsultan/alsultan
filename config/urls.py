from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("core.urls")),
    path("account/", include("accounts.urls")),
    path(
        "accounts/signup/",
        RedirectView.as_view(pattern_name="accounts:register", permanent=False),
    ),
    path(
        "accounts/login/",
        RedirectView.as_view(pattern_name="accounts:login", permanent=False),
    ),
    path("accounts/", include("allauth.urls")),
    path("catalog/", include("catalog.urls")),
    path("orders/", include("orders.urls")),
    path("ambassador/", include("ambassadors.urls")),
]

# Standard Django admin is intentionally not mounted.
# Production administration is served exclusively through /management/.

from django.urls import path

from . import views

app_name = "ambassadors"
urlpatterns = [
    path("", views.account, name="account"),
    path("gift/request/", views.request_gift, name="request_gift"),
]

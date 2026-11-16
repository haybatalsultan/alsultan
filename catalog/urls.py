from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("<uuid:public_id>/", views.product_detail, name="detail"),
    path("<uuid:public_id>/viewers/", views.product_viewers, name="viewers"),
    path("<uuid:public_id>/wishlist/", views.wishlist_toggle, name="wishlist_toggle"),
]

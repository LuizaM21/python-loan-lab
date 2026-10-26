from django.urls import path

from . import views

urlpatterns = [
    path("products/", views.products, name="products"),
    path("products/stats/", views.product_stats, name="product-stats"),
    path("applications/", views.applications, name="applications"),
]

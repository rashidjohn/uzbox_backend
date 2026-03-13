from django.urls import path
from . import views

urlpatterns = [
    path("click/webhook/", views.click_webhook,       name="click_webhook"),
    path("payme/webhook/", views.payme_webhook,       name="payme_webhook"),
    path("click/create/",  views.click_create_url,    name="click_create"),
    path("payme/create/",  views.payme_create_url,    name="payme_create"),
    path("test/confirm/",  views.test_confirm_payment, name="test_confirm"),
]

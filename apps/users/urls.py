from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────
    path("register/",                      views.register_view,             name="register"),
    path("login/",                         views.login_view,                 name="login"),
    path("logout/",                        views.logout_view,                name="logout"),
    path("refresh/",                       TokenRefreshView.as_view(),       name="token_refresh"),
    path("change-password/",               views.change_password_view,       name="change_password"),
    # ── Email tekshirish ────────────────────────────────────────
    path("send-verify-email/",             views.send_verify_email_view,     name="send_verify_email"),
    path("verify-email/",                  views.verify_email_view,          name="verify_email"),
    # ── Profil ──────────────────────────────────────────────────
    path("profile/",                       views.ProfileView.as_view(),      name="profile"),
    # ── Manzillar ───────────────────────────────────────────────
    path("addresses/",                     views.AddressListCreateView.as_view(), name="addresses"),
    path("addresses/<int:pk>/",            views.AddressDetailView.as_view(),     name="address_detail"),
    # ── Sevimlilar ───────────────────────────────────────────────
    path("wishlist/",                      views.wishlist_view,              name="wishlist"),
    path("wishlist/<uuid:product_id>/toggle/", views.wishlist_toggle_view,   name="wishlist_toggle"),
    path("wishlist/clear/",                views.wishlist_clear_view,        name="wishlist_clear"),
]

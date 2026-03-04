
from django.urls import path
from . import views

app_name = "pharmacie"

urlpatterns = [
    path("", views.landing, name="landing"),          # page 1 (landing)
    path("home/", views.home, name="home"),           # liste medicaments (compte)
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("commander/<int:medicament_id>/", views.commander, name="commander"),
    path("mes-commandes/", views.mes_commandes, name="mes_commandes"),
]
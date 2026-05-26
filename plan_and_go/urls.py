from django.urls import path

from . import views

app_name = "plan_and_go"

urlpatterns = [
    path("", views.home, name="home"),
    path("registro/", views.register, name="register"),
    path("viajes/", views.trip_list, name="trip_list"),
    path("viajes/nuevo/", views.trip_create, name="trip_create"),
    path("viajes/<int:pk>/", views.trip_detail, name="trip_detail"),
    path("viajes/<int:pk>/editar/", views.trip_update, name="trip_update"),
    path("viajes/<int:pk>/eliminar/", views.trip_delete, name="trip_delete"),
    path("viajes/<int:pk>/invitar/", views.invite_traveler, name="invite_traveler"),
    path(
        "viajes/<int:trip_pk>/participantes/<int:user_pk>/eliminar/",
        views.remove_traveler,
        name="remove_traveler",
    ),
    path("viajes/<int:trip_pk>/etapas/nueva/", views.stop_create, name="stop_create"),
    path("viajes/<int:trip_pk>/etapas/<int:pk>/", views.stop_detail, name="stop_detail"),
    path("viajes/<int:trip_pk>/etapas/<int:pk>/editar/", views.stop_update, name="stop_update"),
    path("viajes/<int:trip_pk>/etapas/<int:pk>/eliminar/", views.stop_delete, name="stop_delete"),
    path(
        "viajes/<int:trip_pk>/etapas/<int:stop_pk>/gastos/nuevo/",
        views.expense_create,
        name="expense_create",
    ),
    path(
        "viajes/<int:trip_pk>/etapas/<int:stop_pk>/gastos/<int:pk>/editar/",
        views.expense_update,
        name="expense_update",
    ),
    path(
        "viajes/<int:trip_pk>/etapas/<int:stop_pk>/gastos/<int:pk>/eliminar/",
        views.expense_delete,
        name="expense_delete",
    ),
]

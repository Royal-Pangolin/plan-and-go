from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ExpenseForm, RegistrationForm, StopForm, TravelerInviteForm, TripForm
from .models import Expense, Stop, Traveler, Trip
from .services import get_trip_financial_summary, get_weather_forecast


def home(request):
    if request.user.is_authenticated:
        return redirect("plan_and_go:trip_list")
    return render(request, "plan_and_go/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("plan_and_go:trip_list")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cuenta creada correctamente.")
            return redirect("plan_and_go:trip_list")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def trip_list(request):
    trips = (
        Trip.objects.filter(travelers=request.user)
        .select_related("created_by")
        .prefetch_related("travelers")
        .annotate(stops_count=Count("stops", distinct=True))
        .order_by("-start_date", "name")
    )
    return render(request, "plan_and_go/trip_list.html", {"trips": trips})


@login_required
def trip_create(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                trip = form.save(commit=False)
                trip.created_by = request.user
                trip.save()
                Traveler.objects.create(trip=trip, user=request.user)
            messages.success(request, "Viaje creado correctamente.")
            return redirect(trip)
    else:
        form = TripForm()

    return render(
        request,
        "plan_and_go/trip_form.html",
        {"form": form, "title": "Nuevo viaje", "submit_label": "Crear viaje"},
    )


@login_required
def trip_detail(request, pk):
    trip = _get_member_trip(request.user, pk)
    stops = trip.stops.prefetch_related("expenses").order_by("order", "start_date")
    expenses = (
        Expense.objects.filter(stop__trip=trip)
        .select_related("stop", "paid_by")
        .order_by("-date", "-created_at")[:8]
    )
    summary = get_trip_financial_summary(trip)
    invite_form = TravelerInviteForm(trip=trip) if _is_creator(request.user, trip) else None

    return render(
        request,
        "plan_and_go/trip_detail.html",
        {
            "trip": trip,
            "stops": stops,
            "expenses": expenses,
            "summary": summary,
            "invite_form": invite_form,
            "can_manage_trip": _is_creator(request.user, trip),
        },
    )


@login_required
def trip_update(request, pk):
    trip = _get_creator_trip(request.user, pk)
    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Viaje actualizado correctamente.")
            return redirect(trip)
    else:
        form = TripForm(instance=trip)

    return render(
        request,
        "plan_and_go/trip_form.html",
        {"form": form, "trip": trip, "title": "Editar viaje", "submit_label": "Guardar cambios"},
    )


@login_required
def trip_delete(request, pk):
    trip = _get_creator_trip(request.user, pk)
    if request.method == "POST":
        trip.delete()
        messages.success(request, "Viaje eliminado correctamente.")
        return redirect("plan_and_go:trip_list")

    return render(
        request,
        "plan_and_go/confirm_delete.html",
        {
            "object_name": trip.name,
            "cancel_url": trip.get_absolute_url(),
            "title": "Eliminar viaje",
        },
    )


@login_required
def invite_traveler(request, pk):
    trip = _get_creator_trip(request.user, pk)
    if request.method != "POST":
        return redirect(trip)

    form = TravelerInviteForm(request.POST, trip=trip)
    if form.is_valid():
        user = form.user
        Traveler.objects.create(trip=trip, user=user)
        _send_invitation_email(request, request.user, user, trip)
        messages.success(request, f"{user.username} se ha unido al viaje.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(trip)


@login_required
def remove_traveler(request, trip_pk, user_pk):
    trip = _get_creator_trip(request.user, trip_pk)
    if request.method != "POST":
        return redirect(trip)

    if user_pk == trip.created_by_id:
        messages.error(request, "No puedes eliminar al creador del viaje.")
        return redirect(trip)

    membership = Traveler.objects.filter(trip=trip, user_id=user_pk).select_related("user").first()
    if membership is None:
        messages.error(request, "Ese participante no forma parte del viaje.")
        return redirect(trip)

    username = membership.user.username
    membership.delete()
    messages.success(request, f"{username} ya no forma parte del viaje.")
    return redirect(trip)


@login_required
def stop_create(request, trip_pk):
    trip = _get_member_trip(request.user, trip_pk)
    initial = {
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "order": (trip.stops.aggregate(max_order=Max("order"))["max_order"] or 0) + 1,
    }
    if request.method == "POST":
        form = StopForm(request.POST)
        form.instance.trip = trip
        if form.is_valid():
            stop = form.save()
            messages.success(request, "Etapa creada correctamente.")
            return redirect(stop)
    else:
        form = StopForm(initial=initial)

    return render(
        request,
        "plan_and_go/stop_form.html",
        {"form": form, "trip": trip, "title": "Nueva etapa", "submit_label": "Crear etapa"},
    )


@login_required
def stop_detail(request, trip_pk, pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(
        Stop.objects.select_related("trip").prefetch_related("expenses__paid_by"),
        pk=pk,
        trip=trip,
    )
    expenses = stop.expenses.select_related("paid_by").order_by("-date", "-created_at")
    weather = get_weather_forecast(stop)

    return render(
        request,
        "plan_and_go/stop_detail.html",
        {
            "trip": trip,
            "stop": stop,
            "expenses": expenses,
            "weather": weather,
        },
    )


@login_required
def stop_update(request, trip_pk, pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(Stop, pk=pk, trip=trip)
    if request.method == "POST":
        form = StopForm(request.POST, instance=stop)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa actualizada correctamente.")
            return redirect(stop)
    else:
        form = StopForm(instance=stop)

    return render(
        request,
        "plan_and_go/stop_form.html",
        {"form": form, "trip": trip, "stop": stop, "title": "Editar etapa", "submit_label": "Guardar cambios"},
    )


@login_required
def stop_delete(request, trip_pk, pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(Stop, pk=pk, trip=trip)
    if request.method == "POST":
        stop.delete()
        messages.success(request, "Etapa eliminada correctamente.")
        return redirect(trip)

    return render(
        request,
        "plan_and_go/confirm_delete.html",
        {
            "object_name": stop.name,
            "cancel_url": stop.get_absolute_url(),
            "title": "Eliminar etapa",
        },
    )


@login_required
def expense_create(request, trip_pk, stop_pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(Stop, pk=stop_pk, trip=trip)
    initial = {"date": stop.start_date, "paid_by": request.user}
    if request.method == "POST":
        form = ExpenseForm(request.POST, stop=stop)
        if form.is_valid():
            expense = form.save()
            messages.success(request, "Gasto registrado correctamente.")
            return redirect(expense)
    else:
        form = ExpenseForm(stop=stop, initial=initial)

    return render(
        request,
        "plan_and_go/expense_form.html",
        {"form": form, "trip": trip, "stop": stop, "title": "Nuevo gasto", "submit_label": "Registrar gasto"},
    )


@login_required
def expense_update(request, trip_pk, stop_pk, pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(Stop, pk=stop_pk, trip=trip)
    expense = get_object_or_404(Expense, pk=pk, stop=stop)
    if request.method == "POST":
        form = ExpenseForm(request.POST, stop=stop, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Gasto actualizado correctamente.")
            return redirect(expense)
    else:
        form = ExpenseForm(stop=stop, instance=expense)

    return render(
        request,
        "plan_and_go/expense_form.html",
        {"form": form, "trip": trip, "stop": stop, "expense": expense, "title": "Editar gasto", "submit_label": "Guardar cambios"},
    )


@login_required
def expense_delete(request, trip_pk, stop_pk, pk):
    trip = _get_member_trip(request.user, trip_pk)
    stop = get_object_or_404(Stop, pk=stop_pk, trip=trip)
    expense = get_object_or_404(Expense, pk=pk, stop=stop)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Gasto eliminado correctamente.")
        return redirect(stop)

    return render(
        request,
        "plan_and_go/confirm_delete.html",
        {
            "object_name": expense.description,
            "cancel_url": stop.get_absolute_url(),
            "title": "Eliminar gasto",
        },
    )


def _get_member_trip(user: User, pk):
    trip = get_object_or_404(
        Trip.objects.select_related("created_by").prefetch_related("travelers"),
        pk=pk,
    )
    if not trip.is_member(user):
        raise PermissionDenied("No tienes acceso a este viaje.")
    return trip


def _get_creator_trip(user: User, pk):
    trip = _get_member_trip(user, pk)
    if not _is_creator(user, trip):
        raise PermissionDenied("Solo el creador puede realizar esta acción.")
    return trip


def _is_creator(user: User, trip: Trip):
    return user.is_authenticated and trip.created_by_id == user.id


def _send_invitation_email(request, sender, invited_user, trip):
    if not invited_user.email:
        return
    detail_url = request.build_absolute_uri(
        reverse("plan_and_go:trip_detail", kwargs={"pk": trip.pk})
    )
    send_mail(
        subject=f"Te han invitado a {trip.name}",
        message=(
            f"{sender.username} te ha invitado a participar en el viaje {trip.name}.\n\n"
            f"Entra en Plan&Go y abre: {detail_url}"
        ),
        from_email=None,
        recipient_list=[invited_user.email],
        fail_silently=settings.EMAIL_FAIL_SILENTLY,
    )

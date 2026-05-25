from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Trip(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre del viaje")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_trips",
        verbose_name="Creador",
    )
    travelers = models.ManyToManyField(
        User,
        through="Traveler",
        related_name="joined_trips",
        verbose_name="Viajeros",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Viaje"
        verbose_name_plural = "Viajes"
        ordering = ["-start_date", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": "La fecha de fin no puede ser anterior a la fecha de inicio."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("plan_and_go:trip_detail", kwargs={"pk": self.pk})

    @property
    def duration_days(self):
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date - self.start_date).days + 1

    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return self.travelers.filter(pk=user.pk).exists()


class Traveler(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Viaje",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trip_memberships",
        verbose_name="Usuario",
    )
    joined_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Fecha de unión",
    )

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(fields=["trip", "user"], name="unique_traveler_per_trip")
        ]

    def __str__(self):
        return f"{self.user.username} en {self.trip.name}"


class Stop(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="stops",
        verbose_name="Viaje",
    )
    name = models.CharField(max_length=150, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Latitud",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Longitud",
    )
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    order = models.PositiveIntegerField(default=1, verbose_name="Orden")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ["order", "start_date", "name"]
        constraints = [
            models.UniqueConstraint(fields=["trip", "order"], name="unique_stop_order_per_trip")
        ]

    def __str__(self):
        return f"{self.order}. {self.name}"

    def clean(self):
        errors = {}
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["end_date"] = "La fecha de fin no puede ser anterior a la fecha de inicio."
        if self.trip_id and self.start_date and self.start_date < self.trip.start_date:
            errors["start_date"] = "La etapa no puede empezar antes que el viaje."
        if self.trip_id and self.end_date and self.end_date > self.trip.end_date:
            errors["end_date"] = "La etapa no puede terminar despues que el viaje."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("plan_and_go:stop_detail", kwargs={"trip_pk": self.trip_id, "pk": self.pk})


class Expense(models.Model):
    stop = models.ForeignKey(
        Stop,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="Etapa",
    )
    paid_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="paid_expenses",
        verbose_name="Pagado por",
    )
    description = models.CharField(max_length=180, verbose_name="Descripción")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Importe",
    )
    date = models.DateField(verbose_name="Fecha")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.description} - {self.amount} EUR"

    @property
    def trip(self):
        return self.stop.trip

    def clean(self):
        errors = {}
        if self.stop_id and self.date:
            if self.date < self.stop.start_date or self.date > self.stop.end_date:
                errors["date"] = "La fecha del gasto debe estar dentro de las fechas de la etapa."
        if self.stop_id and self.paid_by_id:
            is_member = Traveler.objects.filter(
                trip=self.stop.trip,
                user=self.paid_by,
            ).exists()
            if not is_member:
                errors["paid_by"] = "El pagador debe participar en el viaje."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return self.stop.get_absolute_url()

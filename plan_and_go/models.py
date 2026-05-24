from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Trip(models.Model):
    # Atributos principales
    name = models.CharField(max_length=150, verbose_name="Nombre del viaje")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")

    # Relaciones
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_trips",
        verbose_name="Creador",
    )

    # IMPORTANTE: Usamos 'Traveler' (texto) para no tener que importar la clase
    travelers = models.ManyToManyField(
        User, through="Traveler", related_name="joined_trips", verbose_name="Viajeros"
    )

    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )

    class Meta:
        verbose_name = "Viaje"
        verbose_name_plural = "Viajes"
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def clean(self):
        """Validación para asegurar que la fecha de fin no es anterior a la de inicio"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                "La fecha de inicio no puede ser posterior a la fecha de fin."
            )

    def get_duration(self):
        """Devuelve la cantidad de días totales del viaje"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0


# --- PARCHE TEMPORAL---


class Traveler(models.Model):
    trip = models.ForeignKey("Trip", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    


# ------------------------

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from plan_and_go.models import Expense, Stop, Traveler, Trip


class Command(BaseCommand):
    help = "Crea usuarios y datos de prueba para Plan&Go."

    def handle(self, *args, **options):
        with transaction.atomic():
            users = self._create_users()
            trip = self._create_trip(users["alonso"])
            for user in users.values():
                Traveler.objects.get_or_create(trip=trip, user=user)
            stops = self._create_stops(trip)
            self._create_expenses(stops, users)

        self.stdout.write(self.style.SUCCESS("Datos demo creados. Password: planandgo123"))

    def _create_users(self):
        data = {
            "alonso": "alonso@example.com",
            "mariam": "mariam@example.com",
            "ana": "ana@example.com",
            "pablo": "pablo@example.com",
        }
        users = {}
        for username, email in data.items():
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            user.email = email
            user.set_password("planandgo123")
            user.save()
            users[username] = user
        return users

    def _create_trip(self, creator):
        defaults = {
            "name": "Andalucía en ruta",
            "description": "Ruta de grupo con paradas urbanas, previsiones meteorológicas y gastos compartidos.",
            "start_date": date(2026, 6, 10),
            "end_date": date(2026, 6, 16),
        }
        legacy_name = defaults["name"].replace("í", "i")
        trip = Trip.objects.filter(
            created_by=creator,
            name__in=[defaults["name"], legacy_name],
        ).first()
        if trip is None:
            trip = Trip(created_by=creator)
        for field, value in defaults.items():
            setattr(trip, field, value)
        trip.save()
        return trip

    def _create_stops(self, trip):
        data = [
            {
                "order": 1,
                "name": "Sevilla",
                "description": "Llegada, alojamiento y primera cena del grupo.",
                "latitude": Decimal("37.389092"),
                "longitude": Decimal("-5.984459"),
                "start_date": date(2026, 6, 10),
                "end_date": date(2026, 6, 11),
                "notes": "Revisar temperatura antes de reservar actividades exteriores.",
            },
            {
                "order": 2,
                "name": "Granada",
                "description": "Visita cultural y desplazamientos internos.",
                "latitude": Decimal("37.177336"),
                "longitude": Decimal("-3.598557"),
                "start_date": date(2026, 6, 12),
                "end_date": date(2026, 6, 14),
                "notes": "Mantener margen para cambios si hay lluvia.",
            },
            {
                "order": 3,
                "name": "Málaga",
                "description": "Cierre del viaje y liquidación final.",
                "latitude": Decimal("36.721302"),
                "longitude": Decimal("-4.421637"),
                "start_date": date(2026, 6, 15),
                "end_date": date(2026, 6, 16),
                "notes": "Comprobar balances antes de volver.",
            },
        ]
        stops = {}
        for item in data:
            stop, _ = Stop.objects.update_or_create(
                trip=trip,
                order=item["order"],
                defaults=item,
            )
            stops[stop.name] = stop
        return stops

    def _create_expenses(self, stops, users):
        data = [
            ("Sevilla", "Apartamento Sevilla", "alonso", Decimal("320.00"), date(2026, 6, 10)),
            ("Sevilla", "Cena bienvenida", "mariam", Decimal("96.40"), date(2026, 6, 10)),
            ("Granada", "Entradas visita", "ana", Decimal("72.00"), date(2026, 6, 12)),
            ("Granada", "Transporte urbano", "pablo", Decimal("38.80"), date(2026, 6, 13)),
            ("Málaga", "Comida final", "alonso", Decimal("118.20"), date(2026, 6, 16)),
        ]
        for stop_name, description, username, amount, expense_date in data:
            Expense.objects.update_or_create(
                stop=stops[stop_name],
                description=description,
                defaults={
                    "paid_by": users[username],
                    "amount": amount,
                    "date": expense_date,
                },
            )

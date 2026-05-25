from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Expense, Stop, Traveler, Trip
from .services import get_trip_financial_summary, get_weather_forecast


class PlanAndGoTestCase(TestCase):
    def setUp(self):
        self.alonso = User.objects.create_user(
            username="alonso",
            email="alonso@example.com",
            password="pass12345",
        )
        self.mariam = User.objects.create_user(
            username="mariam",
            email="mariam@example.com",
            password="pass12345",
        )
        self.outsider = User.objects.create_user(username="outsider", password="pass12345")
        self.trip = Trip.objects.create(
            name="Ruta test",
            description="Viaje de pruebas",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 5),
            created_by=self.alonso,
        )
        Traveler.objects.create(trip=self.trip, user=self.alonso)
        Traveler.objects.create(trip=self.trip, user=self.mariam)
        self.stop = Stop.objects.create(
            trip=self.trip,
            name="Sevilla",
            description="Primera parada",
            latitude=Decimal("37.389092"),
            longitude=Decimal("-5.984459"),
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 2),
            order=1,
            notes="",
        )


class ModelTests(PlanAndGoTestCase):
    def test_trip_rejects_invalid_date_range(self):
        trip = Trip(
            name="Fechas invalidas",
            start_date=date(2026, 6, 5),
            end_date=date(2026, 6, 1),
            created_by=self.alonso,
        )

        with self.assertRaises(ValidationError):
            trip.full_clean()

    def test_stop_must_be_inside_trip_dates(self):
        stop = Stop(
            trip=self.trip,
            name="Fuera de rango",
            latitude=Decimal("37.000000"),
            longitude=Decimal("-5.000000"),
            start_date=date(2026, 5, 30),
            end_date=date(2026, 6, 1),
            order=2,
        )

        with self.assertRaises(ValidationError):
            stop.full_clean()

    def test_traveler_is_unique_per_trip(self):
        with self.assertRaises(IntegrityError):
            Traveler.objects.create(trip=self.trip, user=self.alonso)

    def test_expense_payer_must_belong_to_trip(self):
        expense = Expense(
            stop=self.stop,
            paid_by=self.outsider,
            description="Pago externo",
            amount=Decimal("20.00"),
            date=date(2026, 6, 1),
        )

        with self.assertRaises(ValidationError):
            expense.full_clean()

    def test_financial_summary_splits_expenses_between_all_travelers(self):
        Expense.objects.create(
            stop=self.stop,
            paid_by=self.alonso,
            description="Hotel",
            amount=Decimal("100.00"),
            date=date(2026, 6, 1),
        )

        summary = get_trip_financial_summary(self.trip)

        self.assertEqual(summary["total"], Decimal("100.00"))
        self.assertEqual(summary["per_person"], Decimal("50.00"))
        self.assertEqual(summary["settlements"][0]["payer"], self.mariam)
        self.assertEqual(summary["settlements"][0]["receiver"], self.alonso)
        self.assertEqual(summary["settlements"][0]["amount"], Decimal("50.00"))


class ViewPermissionTests(PlanAndGoTestCase):
    def test_anonymous_user_is_redirected_from_trip_list(self):
        response = self.client.get(reverse("plan_and_go:trip_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_non_member_cannot_open_trip_detail(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("plan_and_go:trip_detail", kwargs={"pk": self.trip.pk}))

        self.assertEqual(response.status_code, 403)

    def test_member_can_create_stop(self):
        self.client.force_login(self.mariam)

        response = self.client.post(
            reverse("plan_and_go:stop_create", kwargs={"trip_pk": self.trip.pk}),
            {
                "name": "Granada",
                "description": "Segunda parada",
                "latitude": "37.177336",
                "longitude": "-3.598557",
                "start_date": "2026-06-03",
                "end_date": "2026-06-04",
                "order": "2",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Stop.objects.filter(trip=self.trip, name="Granada").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_creator_can_invite_existing_user_and_email_is_sent(self):
        invited = User.objects.create_user(
            username="ana",
            email="ana@example.com",
            password="pass12345",
        )
        self.client.force_login(self.alonso)

        response = self.client.post(
            reverse("plan_and_go:invite_traveler", kwargs={"pk": self.trip.pk}),
            {"identifier": invited.email},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Traveler.objects.filter(trip=self.trip, user=invited).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.trip.name, mail.outbox[0].subject)


class WeatherServiceTests(PlanAndGoTestCase):
    @patch("plan_and_go.services.requests.get")
    def test_weather_service_returns_daily_forecast(self, mocked_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "timezone": "Europe/Madrid",
            "daily": {
                "time": ["2026-06-01"],
                "weather_code": [0],
                "temperature_2m_max": [29.5],
                "temperature_2m_min": [18.2],
                "precipitation_sum": [0],
            },
        }
        mocked_get.return_value = response

        forecast = get_weather_forecast(self.stop)

        self.assertEqual(forecast["timezone"], "Europe/Madrid")
        self.assertEqual(forecast["days"][0]["label"], "Despejado")

    @patch("plan_and_go.services.requests.get")
    def test_weather_service_returns_none_on_timeout(self, mocked_get):
        mocked_get.side_effect = requests.Timeout

        forecast = get_weather_forecast(self.stop)

        self.assertIsNone(forecast)

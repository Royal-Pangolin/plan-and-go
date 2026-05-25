from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MONEY = Decimal("0.01")


WEATHER_LABELS = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna",
    55: "Llovizna intensa",
    61: "Lluvia ligera",
    63: "Lluvia",
    65: "Lluvia intensa",
    71: "Nieve ligera",
    73: "Nieve",
    75: "Nieve intensa",
    80: "Chubascos ligeros",
    81: "Chubascos",
    82: "Chubascos intensos",
    95: "Tormenta",
    96: "Tormenta con granizo",
    99: "Tormenta fuerte con granizo",
}


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def get_weather_forecast(stop):
    params = {
        "latitude": float(stop.latitude),
        "longitude": float(stop.longitude),
        "start_date": stop.start_date.isoformat(),
        "end_date": stop.end_date.isoformat(),
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=3)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    daily = payload.get("daily") or {}
    days = []
    for index, date in enumerate(daily.get("time", [])):
        code = _value_at(daily.get("weather_code"), index)
        days.append(
            {
                "date": date,
                "label": WEATHER_LABELS.get(code, "Previsión disponible"),
                "temperature_max": _value_at(daily.get("temperature_2m_max"), index),
                "temperature_min": _value_at(daily.get("temperature_2m_min"), index),
                "precipitation": _value_at(daily.get("precipitation_sum"), index),
            }
        )

    if not days:
        return None

    return {
        "timezone": payload.get("timezone"),
        "days": days,
    }


def get_trip_financial_summary(trip):
    participants = list(trip.travelers.order_by("username", "id"))
    expenses = list(
        trip.stops.select_related("trip")
        .prefetch_related("expenses__paid_by")
        .values(
            "expenses__paid_by_id",
            "expenses__amount",
        )
    )
    total = Decimal("0.00")
    paid = defaultdict(lambda: Decimal("0.00"))
    owed = defaultdict(lambda: Decimal("0.00"))

    if not participants:
        return {
            "total": Decimal("0.00"),
            "per_person": Decimal("0.00"),
            "rows": [],
            "settlements": [],
        }

    participant_ids = [user.id for user in participants]
    count = Decimal(len(participants))

    for item in expenses:
        amount = item["expenses__amount"]
        payer_id = item["expenses__paid_by_id"]
        if amount is None or payer_id is None:
            continue
        amount = Decimal(amount)
        total += amount
        paid[payer_id] += amount
        share = amount / count
        for user_id in participant_ids:
            owed[user_id] += share

    rows = []
    balances = {}
    for user in participants:
        balance = paid[user.id] - owed[user.id]
        balances[user.id] = balance
        rows.append(
            {
                "user": user,
                "paid": money(paid[user.id]),
                "owed": money(owed[user.id]),
                "balance": money(balance),
            }
        )

    return {
        "total": money(total),
        "per_person": money(total / count) if total else Decimal("0.00"),
        "rows": rows,
        "settlements": _build_settlements(participants, balances),
    }


def _build_settlements(participants, balances):
    users_by_id = {user.id: user for user in participants}
    debtors = [
        {"user": users_by_id[user_id], "amount": -balance}
        for user_id, balance in balances.items()
        if money(balance) < 0
    ]
    creditors = [
        {"user": users_by_id[user_id], "amount": balance}
        for user_id, balance in balances.items()
        if money(balance) > 0
    ]

    debtors.sort(key=lambda item: item["amount"], reverse=True)
    creditors.sort(key=lambda item: item["amount"], reverse=True)

    settlements = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]
        amount = min(debtor["amount"], creditor["amount"])
        rounded_amount = money(amount)

        if rounded_amount > 0:
            settlements.append(
                {
                    "payer": debtor["user"],
                    "receiver": creditor["user"],
                    "amount": rounded_amount,
                }
            )

        debtor["amount"] -= amount
        creditor["amount"] -= amount

        if money(debtor["amount"]) <= 0:
            debtor_index += 1
        if money(creditor["amount"]) <= 0:
            creditor_index += 1

    return settlements


def _value_at(values, index):
    if not values or index >= len(values):
        return None
    return values[index]

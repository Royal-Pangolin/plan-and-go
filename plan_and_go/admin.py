from django.contrib import admin

from .models import Expense, Stop, Traveler, Trip


class TravelerInline(admin.TabularInline):
    model = Traveler
    extra = 0
    raw_id_fields = ["user"]


class StopInline(admin.TabularInline):
    model = Stop
    extra = 0
    fields = ["order", "name", "start_date", "end_date", "latitude", "longitude"]


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "created_by", "created_at"]
    list_filter = ["start_date", "end_date", "created_by"]
    search_fields = ["name", "description", "created_by__username"]
    raw_id_fields = ["created_by"]
    date_hierarchy = "start_date"
    ordering = ["-start_date"]
    inlines = [TravelerInline, StopInline]


@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = ["trip", "user", "joined_at"]
    list_filter = ["joined_at"]
    search_fields = ["trip__name", "user__username", "user__email"]
    raw_id_fields = ["trip", "user"]


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ["name", "trip", "order", "start_date", "end_date"]
    list_filter = ["trip", "start_date", "end_date"]
    search_fields = ["name", "description", "trip__name"]
    raw_id_fields = ["trip"]
    ordering = ["trip", "order"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["description", "stop", "paid_by", "amount", "date"]
    list_filter = ["date", "paid_by"]
    search_fields = ["description", "stop__name", "paid_by__username"]
    raw_id_fields = ["stop", "paid_by"]
    ordering = ["-date", "-created_at"]

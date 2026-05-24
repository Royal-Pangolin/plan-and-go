from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    # Columnas que se verán en la lista de viajes
    list_display = ["name", "start_date", "end_date", "created_by", "created_at"]

    # Filtros laterales para buscar rápidamente
    list_filter = ["start_date", "end_date", "created_by"]

    # Barra de búsqueda (busca en el nombre del viaje y en su descripción)
    search_fields = ["name", "description"]

    # Widget especial para seleccionar el creador (muy útil si la app tiene muchos usuarios registrados)
    raw_id_fields = ["created_by"]

    # Navegación rápida por fechas en la parte superior (usamos la fecha de inicio del viaje)
    date_hierarchy = "start_date"

    # Ordenación por defecto en el panel (los viajes más recientes o futuros primero)
    ordering = ["-start_date"]

    # Muestra el número de viajes en cada filtro (Novedad Django 5)
    show_facets = admin.ShowFacets.ALWAYS

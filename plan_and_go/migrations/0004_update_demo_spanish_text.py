from django.db import migrations


def update_demo_text(apps, schema_editor):
    Trip = apps.get_model("plan_and_go", "Trip")
    Stop = apps.get_model("plan_and_go", "Stop")

    Trip.objects.filter(name="Andalucia en ruta").update(
        name="Andalucía en ruta",
        description="Ruta de grupo con paradas urbanas, previsiones meteorológicas y gastos compartidos.",
    )
    Trip.objects.filter(name="Andalucía en ruta").update(
        description="Ruta de grupo con paradas urbanas, previsiones meteorológicas y gastos compartidos.",
    )
    Stop.objects.filter(name="Malaga").update(
        name="Málaga",
        description="Cierre del viaje y liquidación final.",
    )
    Stop.objects.filter(name="Málaga").update(
        description="Cierre del viaje y liquidación final.",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("plan_and_go", "0003_alter_expense_created_at_alter_expense_description_and_more"),
    ]

    operations = [
        migrations.RunPython(update_demo_text, migrations.RunPython.noop),
    ]

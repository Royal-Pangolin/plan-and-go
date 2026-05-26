from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Envía un email de prueba usando la configuración SMTP actual."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Email de destino para la prueba.")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        sent = send_mail(
            subject="Prueba de email de Plan&Go",
            message="Si recibes este mensaje, la configuración de email funciona.",
            from_email=None,
            recipient_list=[recipient],
            fail_silently=False,
        )

        if sent:
            self.stdout.write(self.style.SUCCESS(f"Email enviado a {recipient}."))
            return

        self.stdout.write(
            self.style.WARNING(
                "Django no informó errores, pero tampoco confirmó ningún email enviado. "
                f"Backend activo: {settings.EMAIL_BACKEND}"
            )
        )

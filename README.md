# Plan&Go

Plan&Go es una aplicación Django para organizar viajes en grupo: creación de viajes, etapas, participantes, gastos compartidos, balances y previsión meteorológica por etapa.

## Requisitos

- Git
- Python 3.13
- Docker y Docker Compose, recomendado para levantar la app completa con PostgreSQL y Nginx

## Puesta en marcha con Docker

1. Clona el repositorio:

```bash
git clone https://github.com/Royal-Pangolin/plan-and-go.git
cd plan-and-go
```

2. Crea el archivo de entorno:

```bash
cp .env.example .env
```

3. Levanta los servicios:

```bash
docker compose up --build
```

El contenedor `web` aplica migraciones y ejecuta `collectstatic` automáticamente. La aplicación queda disponible en:

```text
http://localhost:8081
```

## Datos demo

Con la app levantada, carga usuarios, viaje, etapas y gastos de prueba:

```bash
docker compose exec web python manage.py seed_demo
```

Credenciales creadas por el seeder:

```text
Usuario: alonso
Password: planandgo123
```

También se crean los usuarios `mariam`, `ana` y `pablo` con la misma contraseña.

El seeder es idempotente: puedes ejecutarlo de nuevo para restaurar los datos demo principales.

## Comandos utiles con Docker

Aplicar migraciones manualmente:

```bash
docker compose exec web python manage.py migrate
```

Crear superusuario:

```bash
docker compose exec web python manage.py createsuperuser
```

Ejecutar tests:

```bash
docker compose exec web python manage.py test
```

Enviar un email de prueba:

```bash
docker compose exec web python manage.py send_test_email destino@example.com
```

Parar servicios:

```bash
docker compose down
```

Parar servicios y borrar volúmenes de base de datos/static/media:

```bash
docker compose down -v
```

## Puesta en marcha local sin Docker

Esta opción usa SQLite si no defines las variables `POSTGRES_*`.

1. Crea y activa el entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Instala dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Aplica migraciones:

```bash
python manage.py migrate
```

4. Carga datos demo:

```bash
python manage.py seed_demo
```

5. Arranca el servidor:

```bash
python manage.py runserver
```

La aplicación queda disponible en:

```text
http://127.0.0.1:8000
```

## Variables de entorno

El archivo `.env.example` contiene las variables necesarias para Docker:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- configuración de email

Si ejecutas localmente sin `.env` y sin `POSTGRES_DB`, Django usa SQLite (`db.sqlite3`).

### Email SMTP

Para enviar invitaciones reales por email, configura estas variables en `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=10
EMAIL_FAIL_SILENTLY=False
DEFAULT_FROM_EMAIL=Plan&Go <your-email@example.com>
```

Para proveedores como Gmail no uses la contraseña normal de la cuenta: usa una contraseña de aplicación. Después de cambiar `.env`, reinicia el servicio `web`:

```bash
docker compose up -d --build web
```

Comprueba el envío con:

```bash
docker compose exec web python manage.py send_test_email destino@example.com
```

## Servicios externos

La previsión meteorológica y el buscador de ciudades usan Open-Meteo:

- Forecast API: previsión por latitud, longitud y fechas.
- Geocoding API: búsqueda de ciudad para rellenar coordenadas.

No requieren API key para el uso actual, pero el servidor o navegador necesitan salida a internet. La previsión puede no aparecer si las fechas están fuera del rango disponible por Open-Meteo.

## Tests

En local:

```bash
python manage.py test
```

Con Docker:

```bash
docker compose exec web python manage.py test
```

## Autores

- Jiménez Flores, Alonso
- Nejeoui Chafiqui, Mariam
- Díaz Sánchez, Ana Valme
- Sánchez Troncoso, Pablo

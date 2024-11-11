#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z authdb 5432; do
  sleep 1
done
echo "PostgreSQL is up and running!"

echo "Waiting for Redis..."
while ! nc -z authredis 6379; do
  sleep 1
done
echo "Redis is up and running!"

echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Creating superuser..."
  
  python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import sys

User = get_user_model()
try:
    User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
    sys.exit()
except User.DoesNotExist:
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
EOF

  echo "Superuser created successfully."
fi

coverage run -m pytest
coverage report

echo "Starting Gunicorn..."
exec gunicorn auth_service.wsgi:application --bind 0.0.0.0:8000
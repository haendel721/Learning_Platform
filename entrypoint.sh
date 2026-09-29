#!/bin/sh
# Arrête le script à la première erreur (évite de lancer gunicorn sur une base cassée)
set -e

# Applique les migrations sur la base PostgreSQL de Render à chaque démarrage
# (idempotent : ne fait rien si tout est déjà appliqué)
python manage.py migrate --noinput

# Rassemble les fichiers statiques (servis par WhiteNoise)
python manage.py collectstatic --noinput

# Lance le serveur applicatif (adapte le nom du module si besoin : config.wsgi)
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
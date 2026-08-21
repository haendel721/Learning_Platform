FROM python:3.12-slim

WORKDIR /app

# Copie uniquement requirements.txt d'abord (pas tout le code) :
# Docker met en cache cette étape tant que requirements.txt ne change pas,
# donc les rebuilds sont beaucoup plus rapides
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
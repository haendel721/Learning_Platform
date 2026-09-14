# ---- Étape 1 : builder ----
# Cette étape installe les dépendances Python et compile
# tout ce qui a besoin d'un compilateur C (comme WeasyPrint/psycopg)
FROM python:3.12-slim AS builder

WORKDIR /app

# Dépendances système nécessaires SEULEMENT pour l'installation
# (compilation), pas pour l'exécution finale
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --user installe les packages dans un dossier local à l'utilisateur,
# plus facile à copier proprement vers l'étape suivante
RUN pip install --no-cache-dir --user -r requirements.txt


# ---- Étape 2 : image finale ----
# Cette étape ne garde que le nécessaire pour FAIRE TOURNER l'app,
# pas pour la construire — image beaucoup plus légère au final
FROM python:3.12-slim

WORKDIR /app

# Dépendances système nécessaires à l'EXÉCUTION seulement
# (WeasyPrint et psycopg ont besoin de ces libs même une fois installés)
RUN apt-get update && apt-get install -y \
    libpq5 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

# Copie uniquement les packages Python déjà installés depuis l'étape builder,
# sans les outils de compilation qui ne servent plus à rien maintenant
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
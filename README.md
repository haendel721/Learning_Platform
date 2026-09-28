# Learning Platform - E-learning SaaS avec IA générative

## 📋 Description

Plateforme e-learning SaaS permettant aux formateurs de créer des cours et de générer automatiquement du contenu pédagogique (quiz, résumés) grâce à l'IA générative. Les étudiants peuvent s'inscrire aux cours, passer des quiz notés automatiquement, et obtenir un certificat vérifiable (PDF + QR code) à la fin.

## 🚀 Fonctionnalités

- Authentification JWT avec rôles (formateur / étudiant)
- Gestion des cours, catégories et leçons
- Génération automatique de quiz via IA (Groq/Gemini avec fallback automatique)
- Inscription aux cours et suivi de progression
- Passage de quiz avec scoring automatique
- Génération de certificats PDF avec QR code de vérification
- Page publique de vérification de certificat
- Tâches asynchrones (emails, génération IA) via Celery + Redis
- Cache et rate limiting sur les endpoints sensibles
- Déploiement conteneurisé (Docker) avec CI/CD (GitHub Actions)

## 🛠️ Stack technique

- **Backend**: Django 5.x + Django REST Framework
- **Base de données**: PostgreSQL
- **Cache/Queue**: Redis + Celery
- **IA**: Groq (openai/gpt-oss-120b) + Gemini (gemini-2.5-flash)
- **PDF**: WeasyPrint
- **Containerisation**: Docker + docker-compose
- **CI/CD**: GitHub Actions

## 🏗️ Architecture

```mermaid
%% Flux global de la plateforme
flowchart LR
    Client[Client web / mobile] -->|HTTP + JWT| API[Django + DRF]
    API -->|lecture / écriture| DB[(PostgreSQL)]
    API -->|cache + rate limiting| Redis[(Redis)]
    API -->|envoie les tâches| Redis
    Redis -->|file de tâches| Worker[Celery Worker]
    Worker -->|génération de quiz| Groq[Groq API]
    Groq -.->|fallback si échec| Gemini[Gemini API]
    Worker -->|génère le certificat| PDF[WeasyPrint PDF + QR code]
    %% Le texte entre guillemets accepte tous les caractères spéciaux
    Worker -->|envoie les emails| Mail["Gmail SMTP"]
    Worker -->|enregistre les résultats| DB
```

## 📦 Installation

### Prérequis

- Python 3.14+
- PostgreSQL 15+
- Redis
- Docker & Docker Compose (pour l'installation conteneurisée)
- Compte API Groq et/ou Google Gemini (clés API)

### Installation locale

1. Cloner le dépôt

```bash
   git clone <url-du-repo>
   cd learning_platform
```

1. Créer et activer l'environnement virtuel

```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
```

1. Installer les dépendances

```bash
   pip install -r requirements.txt
```

1. Configurer les variables d'environnement

```bash
   copy .env.example .env
   # Remplir les valeurs (clés API, DB, etc.)
```

1. Appliquer les migrations

```bash
   python manage.py migrate
```

1. Lancer le serveur

```bash
   python manage.py runserver
```

1. Lancer Celery (dans un terminal séparé, venv activé)

```bash
   celery -A learning_platform worker -l info
```

### Installation avec Docker

1. Configurer les variables d'environnement

```bash
   copy .env.example .env
```

1. Lancer les conteneurs

```bash
   docker-compose up --build
```

1. Appliquer les migrations (dans un autre terminal)

```bash
   docker-compose exec web python manage.py migrate
```

1. L'application est accessible sur `http://localhost:8000`

## 🔑 Variables d'environnement

Crée un fichier `.env` à la racine (voir `.env.example`) avec :

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_URL=postgres://user:password@localhost:5432/learning_platform

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# IA
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

## 🧪 Tests

Le projet compte 29 tests couvrant les modèles, serializers, permissions et cas limites (scoring, enrollments, leçons).

Lancer les tests :

```bash
python manage.py test
```

Avec Docker :

```bash
docker-compose exec web python manage.py test
```

Formatage et qualité de code :

```bash
black .
flake8
```

## 📚 Documentation API

Une fois le serveur lancé, la documentation interactive est disponible sur :

- **Swagger UI** : `http://localhost:8000/api/docs/`
- **Redoc** : `http://localhost:8000/api/redoc/`
- **Schéma OpenAPI (JSON/YAML)** : `http://localhost:8000/api/schema/`

Pour tester les endpoints protégés dans Swagger :

1. Récupérer un token via /api/auth/login/
1. Cliquer sur **Authorize** en haut à droite
1. Saisir `Bearer <ton_token>`
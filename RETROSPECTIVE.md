# Rétrospective MVP (Semaines 1 à 8)

## Résultat

MVP déployé sur Render : authentification JWT, cours et leçons, génération
de quiz par IA (Groq avec bascule automatique sur Gemini), passage de quiz
avec scoring, certificats PDF vérifiables, Docker et CI GitHub Actions.
Couverture de tests : environ 92 %.

## Ce qui a bien marché

- Tous les outils étaient nouveaux pour moi (Celery, Redis, Docker, CI/CD,
  déploiement), et le découpage jour par jour m'a permis de les apprendre
  progressivement.
- Un point d'entrée unique pour l'IA (`AIServiceRouter`) : la bascule
  Groq -> Gemini est testée sans jamais appeler les vraies API.

## Ce qui a été difficile

- Installer `coverage`, `black` et `flake8` en local.
- Pas de Shell sur le plan gratuit de Render : les migrations et la
  création de l'admin passent par `entrypoint.sh` et des variables
  d'environnement.
- Des tests qui dépendaient de Redis (envoi d'email) : lents et fragiles
  tant que la tâche Celery n'est pas remplacée par un mock.

## Bugs trouvés grâce aux tests

- Cache de 7 jours qui gardait l'état "pending" d'un quiz : le cache est
  maintenant vidé à la fin de la génération.
- Quiz passé en "ready" avant la création des questions : les questions
  sont maintenant créées dans une transaction.

## Ce que je change pour la Phase 2

- Écrire les tests en même temps que chaque fonctionnalité.
- Toujours mocker les services externes (IA, Celery, email) dans les tests.
- Prévoir la configuration de déploiement dès le début d'une fonctionnalité.
- Lancer `black` et `flake8` avant chaque commit.
# Adopter des bonnes pratiques GitHub simples et proportionnées

- **Date :** 2026-11-23
- **Statut :** Hypothèse
- **Source :** Demande de Marc, 23 nov. 2026 ; issue #7.

## Contexte
Le dépôt public a déjà GitHub Pages avec déploiement automatique et un cron quotidien qui enregistre la recommandation du jour. Marc a demandé quelles autres pratiques, simples et adaptées à un petit site statique personnel en Python (bibliothèque standard seulement), valaient la peine d'être activées.

## Options
- A. Ne rien ajouter au-delà de Pages et du cron.
- B. Un socle léger : métadonnées du dépôt, Dependabot pour les actions, alertes de sécurité déjà gratuites, permissions minimales des workflows, sans cérémonie (pas de protection de branche, pas de CodeQL, pas de modèles d'issue).
- C. Un appareil plus lourd (CodeQL, protection de `main`, épinglage des actions par SHA, modèles, campagne de labels).

## Pour et contre
- A : rien à entretenir, mais le dépôt reste incomplet (pas d'URL dans « About », wiki et projets inutilisés ouverts, actions non surveillées).
- B : peu de fichiers, automatisable, protège les décisions utiles ; Dependabot ouvrira de rares pull requests, exception étroite à la règle « pas de PR ».
- C : coût d'entretien sans gain réel pour un site personnel sans dépendances pip, et la protection de branche casserait le push direct et le commit du matin.

## Décision
Option B, détaillée dans l'issue #7. En particulier : pas de protection de branche, pas de CodeQL, pas de licence ajoutée sans l'accord de Marc (MIT proposée, en attente), pas de modèle d'issue. Un badge de statut et Dependabot (écosystème `github-actions`, mensuel) sont ajoutés. Les réglages du dépôt (URL, sujets, wiki et projets désactivés, alertes de vulnérabilité, actions limitées aux actions officielles GitHub) sont appliqués. Le secret scanning et la protection au push étaient déjà actifs.

Le commit quotidien de la recommandation, pendant la saison (1er novembre au 31 mars), compte comme une activité du dépôt et relance le délai de 60 jours au terme duquel GitHub peut désactiver le déclenchement planifié. Hors saison, aucun commit automatique n'est fait : un garde-fou n'est pas ajouté maintenant ; on pourra le revoir au printemps 2027 si besoin. Un tag ou une release par saison attend la fin de l'hiver.

## Conséquences
- Fichiers : `.github/dependabot.yml`, permissions par job dans `.github/workflows/pages.yml`, badge dans le `README.md`.
- Les pull requests de Dependabot, limitées aux actions officielles, pourront être fusionnées quand c'est commode, sans changer la règle de saisie (commit direct sur `main`).
- Licence, confirmation des notifications d'échec et tag de fin de saison restent à trancher ou à faire plus tard (issue #7 laissée ouverte).

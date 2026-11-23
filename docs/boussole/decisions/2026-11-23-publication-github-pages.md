# Publier le projet sur GitHub Pages sous le nom buchometre

- **Date :** 2026-11-23
- **Statut :** Acceptée
- **Source :** Demande de Marc et choix du nom, 23 nov. 2026 ; commit `ecfc571` ; issue #1.

## Contexte
Marc voulait consulter les données et leur évolution à distance, surtout sur téléphone, avec un lien direct. Les données (bûches, kWh) ne sont pas sensibles à ses yeux.

## Options
- A. Garder le site sur un seul ordinateur.
- B. Un dépôt public avec GitHub Pages et un déploiement automatique à chaque push.
- C. Un hébergement privé avec authentification.

## Pour et contre
- A : aucune exposition, mais pas d'accès mobile.
- B : gratuit, simple, historique complet ; exige un audit de confidentialité.
- C : plus de configuration pour un gain nul.

## Décision
Option B. Nom **buchometre** (court, sans accent, « ça dit ce que ça fait »), choisi par Marc. Le site généré (`rapports/`) n'est pas versionné : GitHub Actions le reconstruit à chaque push sur `main`. Avant publication : lien vers le chiffrier retiré, aucune adresse ni numéro de client, commits au nom de Marc.

## Conséquences
- Adresse : https://mgagp.github.io/buchometre/ ; tableaux défilants et menu allégé sur téléphone.
- Rendu validé par Marc sur PC et téléphone le 23 nov. 2026.
- Issues de jalons : #1 (fermée), #2 identité visuelle, #3 généralisation légère.

# Un site statique régénéré par script

- **Date :** 2026-11-22
- **Statut :** Acceptée
- **Source :** Propositions de la première itération, retenues le 22 nov. 2026 (page Propositions).

## Contexte
L'analyse 2023-24 produisait beaucoup de tableaux et de graphiques. Il fallait un format consultable, reproductible et sans entretien.

## Options
- A. Enrichir le chiffrier Google existant.
- B. Un tableau de bord hébergé (outil de BI, application web).
- C. Des pages HTML statiques générées par des scripts Python à partir de CSV.

## Pour et contre
- A : familier, mais le chiffrier est une source à ne pas modifier, et les graphiques y sont limités.
- B : interactif, mais lourd à maintenir pour une seule maison.
- C : reproductible, versionnable, aucun serveur ; demande de régénérer après chaque saisie.

## Décision
Option C : site statique, Python bibliothèque standard seulement, saisie simplifiée dans `data/saisie_2026-2027.csv`.

## Conséquences
- Aucun chiffre n'est tapé à la main dans une page : tout vient de `data/`.
- Rend possible la publication automatique (voir `2026-11-23-publication-github-pages`).

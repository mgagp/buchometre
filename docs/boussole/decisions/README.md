# Décisions

Une décision par fichier, nommé `AAAA-MM-JJ-sujet.md` (date de la décision, sujet court sans accents).
Statuts : **Acceptée** (confirmée par Marc), **Hypothèse** (appliquée par un assistant, sans confirmation
explicite), **Proposée** (en attente de Marc), **Remplacée par …** (on garde le fichier pour l'histoire).

| Date | Décision | Statut |
|---|---|---|
| 2026-11-21 | [Estimer les kWh évités par une régression (≈ 4,5 kWh par bûche)](2026-11-21-modele-kwh-par-regression.md) | Acceptée |
| 2026-11-22 | [Ne pas chauffer tous les jours : cibler les moments rentables](2026-11-22-cibler-moments-rentables.md) | Acceptée |
| 2026-11-22 | [Inventaire mesuré de la pile : 876 bûches](2026-11-22-inventaire-876-buches.md) | Acceptée |
| 2026-11-22 | [Météo de référence : Vaudreuil-Dorion](2026-11-22-meteo-vaudreuil-dorion.md) | Acceptée |
| 2026-11-22 | [Pas de corde d'appoint cet hiver](2026-11-22-pas-de-corde-appoint.md) | Acceptée |
| 2026-11-22 | [Prix du bois de référence : 425 $ tout compris, +25 $ par corde](2026-11-22-prix-du-bois-reference.md) | Acceptée |
| 2026-11-22 | [Règle de budget avec réserve pour les événements](2026-11-22-regle-de-budget-avec-reserve.md) | Acceptée |
| 2026-11-22 | [Règles de chauffe assouplies avec le nouveau stock](2026-11-22-regles-assouplies.md) | Acceptée |
| 2026-11-22 | [Une recommandation chaque matin, par notification plutôt que par courriel](2026-11-22-routine-du-matin.md) | Acceptée |
| 2026-11-22 | [Un site statique régénéré par script](2026-11-22-site-statique-par-script.md) | Acceptée |
| 2026-11-22 | [Premier stock estimé à environ 348 bûches](2026-11-22-stock-estime-348.md) | Remplacée par `2026-11-22-inventaire-876-buches` |
| 2026-11-22 | [Tarif Flex D ; option de crédit hivernal écartée](2026-11-22-tarif-flex-d.md) | Acceptée |
| 2026-11-23 | [Une boussole : intention, principes et décisions dans le dépôt](2026-11-23-boussole-du-projet.md) | Acceptée |
| 2026-11-23 | [Adopter des principes de travail allégés](2026-11-23-principes-de-travail-alleges.md) | Acceptée |
| 2026-11-23 | [Adopter des bonnes pratiques GitHub simples et proportionnées](2026-11-23-pratiques-github-proportionnees.md) | Hypothèse |
| 2026-11-23 | [Historique des recommandations par commit quotidien](2026-11-23-historique-recommandations-commit-quotidien.md) | Acceptée |
| 2026-11-23 | [Plan recalculé sur la météo réelle, projection jusqu'au 31 mars](2026-11-23-plan-sur-meteo-reelle.md) | Hypothèse |
| 2026-11-23 | [Publier le projet sur GitHub Pages sous le nom buchometre](2026-11-23-publication-github-pages.md) | Acceptée |
| 2026-11-23 | [Relooking après la restructuration, limité au thème](2026-11-23-relooking-apres-restructuration.md) | Acceptée |
| 2026-11-23 | [Recommandation canonique dans le dépôt](2026-11-23-recommandation-canonique.md) | Acceptée |
| 2026-11-23 | [Restructurer le site en mode saison](2026-11-23-restructuration-mode-saison.md) | Acceptée |
| 2026-11-23 | [Un commit par saisie, sans pull request](2026-11-23-un-commit-par-saisie.md) | Acceptée |

## Modèle

```markdown
# Titre de la décision

- **Date :** AAAA-MM-JJ
- **Statut :** Proposée | Hypothèse | Acceptée | Remplacée par `AAAA-MM-JJ-sujet`
- **Source :** échange avec Marc, commit, issue ou page du site

## Contexte
Le problème, en deux ou trois phrases.

## Options
- A. …
- B. …

## Pour et contre
- A : …
- B : …

## Décision
L'option retenue et pourquoi, en une ou deux phrases.

## Conséquences
- Ce que ça change, ce qui reste à vérifier.
```

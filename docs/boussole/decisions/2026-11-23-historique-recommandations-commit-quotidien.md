# Historique des recommandations par commit quotidien

- **Date :** 2026-11-23
- **Statut :** Acceptée (décision de Marc) ; détails d'exécution en « Hypothèse »
- **Source :** Réponses de Marc du 23 nov. 2026 (restructuration) et étape 2 ([issue #6](https://github.com/mgagp/buchometre/issues/6)).

## Contexte
Pour juger le protocole en fin de saison, il faut comparer ce qui était recommandé chaque matin avec ce qui a été fait.
La reconstruction du matin ne laissait aucune trace : la recommandation d'hier était perdue.

## Options
- A. Ne rien garder ; recalculer après coup (faux : la prévision du matin n'existe plus).
- B. Garder la recommandation dans un fichier versionné, un commit automatique par jour.
- C. La garder hors du dépôt (artefact ou cache de GitHub Actions) : expire, et invisible sur le site.

## Pour et contre
- A : rien à faire, mais on ne peut pas évaluer le protocole.
- B : historique permanent et lisible ; environ 130 petits commits par saison, faits par un robot.
- C : pas de commits, mais fragile et hors de la mémoire du dépôt.

## Décision
Option B. Le workflow du matin (cron et lancement manuel) ajoute la ligne du jour à `data/recommandations_2026-2027.csv`
(date, recommandation, bûches, moment, raison, règle, source météo, T prévue, événement, stock, réserve, heure), puis
commite ce seul fichier sous l'identité `github-actions[bot]` avec `GITHUB_TOKEN` (permission `contents: write`).

Hypothèses (choix d'exécution) :
- **La première recommandation du jour fait foi** : une reconstruction plus tard (saisie, code) ne la réécrit pas, et
  aucun commit n'est fait si la ligne existe déjà. Les constructions déclenchées par un push n'écrivent rien.
- Pas de boucle : un push fait avec `GITHUB_TOKEN` ne relance aucun workflow ; le site est déployé dans la même exécution.
- Une saisie poussée pendant la construction du matin attend au lieu de l'annuler (`cancel-in-progress: false`) ;
  en cas de course, le commit est rebasé puis poussé (trois essais), sinon un avertissement et le site est publié quand même.

## Conséquences
- Avant de pousser une saisie : `git pull --rebase` (le robot a pu commiter le matin).
- Le Journal et l'accueil montrent « recommandé, puis fait » ; le calendrier marque les jours où un feu était recommandé.

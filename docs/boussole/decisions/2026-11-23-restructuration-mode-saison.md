# Restructurer le site en mode saison

- **Date :** 2026-11-23
- **Statut :** Acceptée
- **Source :** Proposition d'architecture et réponses de Marc aux cinq questions, 23 nov. 2026 ; livrée par les commits `71e0e72` à `d2f993f` ([issue #4](https://github.com/mgagp/buchometre/issues/4), fermée).

## Contexte
Le site était un rapport d'analyse 2023-24 : l'accueil montrait l'hiver passé, le menu comptait une quinzaine d'entrées et le suivi de la saison était au quatrième niveau. Le projet devient un tableau de bord quotidien.

## Options
- A. Garder la structure et ajouter un lien « Saison ».
- B. Inverser la pyramide : la saison en cours d'abord, la stratégie ensuite, l'historique en archives.

## Pour et contre
- A : aucun travail, mais navigation confuse, surtout sur téléphone.
- B : un vrai tableau de bord ; demande de déplacer des pages et d'ajouter des redirections.

## Décision
Option B, menu de cinq entrées : Saison (accueil), Journal, Stratégie, Archives, Méthode. Marc a tranché : saison du **1er nov. au 31 mars** ; **régénération automatique chaque matin**, sans commit ; **tout 2023-24 en archives**, avec redirections ; **historique des recommandations conservé** (un commit par jour, à l'étape 2) ; **jours manquants signalés à partir du 1er déc.**

## Conséquences
Livré le 23 nov. 2026 :
- les 5 entrées de menu, avec des redirections depuis les anciennes adresses ;
- `data/saisons.json`, qui décrit chaque saison et permet de basculer en 2027-28 sans toucher au code ;
- trois couches séparées : `outils/calculs/` (aucun HTML), `outils/rendu/` (aucune couleur), `theme/` (apparence) ;
- une reconstruction chaque matin à 11 h 30 UTC (6 h 30 à Toronto en hiver ; devancée le 2026-11-23 à 10 h 45 UTC, 5 h 45, pour précéder la routine de 7 h même avec un retard de GitHub et en heure avancée), sans commit, avec repli sur les données versionnées ;
- une validation de la saisie qui échoue en mode fermé : une erreur bloque la publication.

Reste pour l'étape 2 : le calendrier complet, l'historique des recommandations (un commit par jour) et le plan recalculé sur la météo réelle.

# Météo observée canonique : Environnement Canada, Ste-Anne-de-Bellevue 1

- **Date :** 2026-11-23
- **Statut :** Acceptée (option C de l'issue, choisie par Marc)
- **Source :** [issue #9](https://github.com/mgagp/buchometre/issues/9) ; comparaison avant/après :
  [recalibration-meteo-ec-2026-11.md](../../recalibration-meteo-ec-2026-11.md).

## Contexte
L'historique du site affichait pour le 22 nov. 6,1 / 13,7 / 8,7 °C (min / max / moy.). Environnement Canada a mesuré
0,2 / 14,9 / 7,5 °C à Ste-Anne-de-Bellevue. La météo « passée » venait d'Open-Meteo. C'était un modèle (ECMWF IFS) et
non une mesure, ni la réanalyse ERA5 annoncée. Ce même modèle servait à la régression, aux normales et aux décisions.

## Options
- A. Garder Open-Meteo et corriger seulement l'étiquette.
- B. EC pour l'historique affiché seulement ; le modèle et la simulation restent sur Open-Meteo.
- C. EC partout : affichage, régression, normales et simulation, recalibrées une fois.

## Pour et contre
- A : aucun travail, mais l'historique reste faux d'environ 6 °C certaines nuits.
- B : un affichage juste, mais deux météos, donc deux vérités entre l'affichage et les décisions.
- C : une seule météo, mesurée. Les chiffres du modèle bougent une fois (comparaison publiée).

## Décision
Option C.
- **Source canonique :** API GeoMet `climate-daily` d'Environnement Canada, station Ste-Anne-de-Bellevue 1 (702FHL8).
  Repli : Montréal-Trudeau (7025251), puis Open-Meteo, toujours étiqueté « estimation par modèle ».
  Le fichier Datamart « hier » reste facultatif (secours ou contre-vérification).
- **Moyenne du jour :** (max + min) / 2, la définition d'EC. La prévision d'EC suit la même formule : le minimum vient
  de la nuit qui précède le jour, sinon de la nuit suivante. Cette formule remplace l'hypothèse de calcul notée dans
  `2026-11-23-recommandation-canonique`.
- **Recalibration :** une seule fois, sur EC (Ste-Anne, avec Trudeau pour les trous). Elle couvre la régression, les
  normales, les creux, la période critique et la simulation. Historique versionné : `sources/meteo_ec_2023-2026.csv`.
- **Chaque matin** (cron à 10 h 45 UTC), `--maj` retélécharge les 30 derniers jours, et tout trou depuis le dernier jour
  versionné, dans `data/meteo_observee_AAAA-AAAA.csv` (`date,station,min,max,moyenne,source`). Les révisions d'EC sont
  acceptées. Le fichier part dans le même commit quotidien que la recommandation, pendant la saison seulement.
  Le fichier est petit (environ 365 lignes par an) : on ne l'élague pas.

## Conséquences
- Le site affiche la source de chaque jour passé : le calendrier, la ligne « Hier, observé » de l'accueil et le tableau
  « Météo observée » du journal.
- Principaux changements : 4,50 → 4,87 kWh évités par bûche (plage 3,9 à 6,2). La période critique va du 27 nov. au
  19 mars (au lieu du 27 mars). La fin de saison projetée passe de 97 à 109 bûches. La décision du 23 nov. ne change pas.
- Remplace la partie « archives » de `2026-11-22-meteo-vaudreuil-dorion`. Les prévisions restent celles d'EC pour
  Vaudreuil-Dorion, avec Open-Meteo en secours.
- La recommandation publiée indique la source de la veille (`jours[0].source`, par exemple
  « Ste-Anne-de-Bellevue 1, EC »). Sa structure ne change pas.
- À surveiller : si Ste-Anne manque souvent un jour, le repli Trudeau (plus chaud en ville) apparaîtra dans
  l'historique, étiqueté comme tel.

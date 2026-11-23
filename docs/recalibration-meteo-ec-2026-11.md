# Recalibration sur la météo observée d'Environnement Canada (23 nov. 2026)

Décision : [météo observée canonique, Environnement Canada](boussole/decisions/2026-11-23-meteo-observee-ec.md)
([issue #9](https://github.com/mgagp/buchometre/issues/9)).

**Avant :** archives Open-Meteo, point 45,40 N / −74,03 O. C'était le modèle ECMWF IFS, et non la réanalyse ERA5
annoncée ; c'est un modèle et non une mesure.
**Après :** Environnement Canada, données climatiques quotidiennes, station Ste-Anne-de-Bellevue 1 (702FHL8), à environ
8 km. Repli sur Montréal-Trudeau (7025251), puis sur Open-Meteo, étiqueté « estimation par modèle ».
La moyenne du jour est calculée comme (max + min) / 2, la définition d'EC.

Tout a été recalculé une seule fois sur la nouvelle série, sans toucher aux règles : régression, normales (médiane des
31 jours), creux froids, période critique et simulation sur les trois hivers. De 2023-07-01 à 2026-06-30, on a
1 079 jours de Ste-Anne et 17 de Trudeau. Sur l'hiver 2023-24, EC est plus chaud qu'Open-Meteo de 0,46 °C en moyenne
(1,15 °C d'écart absolu par jour).

## Modèle kWh (102 jours mesurés, 2023-24)

| Paramètre | Avant (Open-Meteo) | Après (EC) |
|---|---:|---:|
| Constante (kWh/jour) | 50,04 ± 7,78 | 46,16 ± 7,51 |
| kWh par degré-jour | 1,94 ± 0,46 | 2,29 ± 0,47 |
| kWh par bûche | −4,50 ± 0,46 | −4,87 ± 0,48 |
| R² | 0,529 | 0,554 |
| Erreur type (RMSE, kWh/jour) | 15,2 | 14,8 |
| Jours mesurés | 102 | 102 |
| Plage retenue, kWh évités par bûche | 3,6 à 5,7 | 3,9 à 6,2 |

Une bûche évite un peu plus de kWh qu'avant : 4,9 kWh au lieu de 4,5, à l'intérieur de l'ancienne plage. La chaleur
d'une bûche se lit plus nettement quand la température de référence est mesurée. L'ajustement est légèrement meilleur.

## Normales, creux et période critique

- Période critique : 2026-11-27 → 2027-03-27 (121 j) avant ; 2026-11-27 → 2027-03-19 (113 j) après.

La fin de la période critique avance de 8 jours, car la normale d'EC est plus douce en mars.

| Hiver (météo) | Creux avant / après | Jours de cœur avant / après | Bûches brûlées (règle) avant / après | Reste avant / après | Valeur ($) avant / après |
|---|---:|---:|---:|---:|---:|
| 2023-2024 | 7 / 7 | 26 / 30 | 644 / 652 | 232 / 224 | 326 / 358 |
| 2024-2025 | 11 / 8 | 31 / 28 | 830 / 789 | 46 / 87 | 534 / 568 |
| 2025-2026 | 8 / 8 | 26 / 27 | 874 / 871 | 2 / 5 | 518 / 569 |

| Hiver (météo) | Jours simulés | Décision différente (bûches du jour) | Jours de feu avant / après |
|---|---:|---:|---:|
| 2023-2024 | 145 | 31 | 62 / 63 |
| 2024-2025 | 145 | 23 | 85 / 80 |
| 2025-2026 | 145 | 17 | 85 / 84 |

Les valeurs en dollars augmentent surtout parce qu'une bûche évite plus de kWh. Les jours où la décision change sont
des jours limites : la moyenne d'EC fait passer un jour d'un côté ou de l'autre de −5 °C (cœur de creux) ou de 0 °C
(à partir de janvier).

## Saison 2026-2027 : projection et réserve

- Fin de saison projetée (stock restant au 31 mars, météo 2024-2025 / 2024-2025) : **97 → 109 bûches** ; bûches projetées sur la saison : 779 → 767 ; fourchette des trois hivers : 644 à 874 → 652 à 871.
- Réserve pour les événements (aujourd'hui) : 115 → 115 bûches ; marge : 761 → 761.

## Recommandation du 23 nov. 2026

| Jour | Avant : T moy (min / max), source → décision | Après |
|---|---|---|
| hier (2026-11-22) | 8,7 °C (6,1 / 13,7), observée | 7,5 °C (0,2 / 14,9), Ste-Anne-de-Bellevue 1, EC |
| aujourd'hui (2026-11-23) | 5,0 °C (−3,0 / 13,0), Environnement Canada → pas de feu | 5,0 °C (−3,0 / 13,0), Environnement Canada → pas de feu |
| demain (2026-11-24) | −2,5 °C (−3,0 / 1,0), Environnement Canada → pas de feu | −1,0 °C (−3,0 / 1,0), Environnement Canada → pas de feu |
| après-demain (2026-11-25) | −3,8 °C (−9,0 / 2,0), Environnement Canada → pas de feu | −3,5 °C (−9,0 / 2,0), Environnement Canada → pas de feu |

Le verdict ne change pas : on est avant la période critique, donc pas de feu jusqu'au 26 nov. Hier affiche maintenant
la mesure d'EC à Ste-Anne (0,2 / 14,9 / 7,5 °C), alors qu'Open-Meteo donnait 6,1 / 13,7 / 8,7 °C. Les moyennes prévues
de demain et d'après-demain changent pour une autre raison : la moyenne prévue d'EC prend maintenant le minimum de la
nuit qui précède le jour (repli : la nuit suivante), soit (max + min) / 2. Avant, elle prenait la moyenne des deux nuits.

## Non recalibré (volontairement)

- La projection 2023-24 du chiffrier (928 bûches, donc 232 bûches/corde) reste un paramètre fixe. Avec EC, la
  projection donnerait 930 bûches, un écart négligeable.
- Les règles (−5 °C, 0 °C, réserve de 5 bûches par événement, frein à 50 bûches) ne changent pas.

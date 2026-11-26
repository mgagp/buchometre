# Jour d'événement = journée complète, réserve de 9 bûches, un seul feu continu

- **Date :** 2026-11-26
- **Statut :** Acceptée (quatre questions tranchées une à une par Marc le 26 nov.) ; le plancher de 11 bûches, le
  rythme des recharges (≈ toutes les 2 h) et la part de 55 % restent des points de départ (« Hypothèse »)
- **Source :** échange avec Marc du 26 nov. 2026, après une vérification de l'alignement du modèle et de la simulation
  sur ses journées de feu de 2023-24 (102 jours mesurés).

## Contexte
Marc chauffe en « journée complète » : un feu allumé le matin et gardé vivant toute la journée. En 2023-24, un jour de
feu comptait en médiane 9 bûches (moyenne 8,8), 11 à 14 par grand froid. Les règles 3 et 4 (jours froids, jusqu'à
12 bûches) collaient à cette pratique, mais pas la règle 1 : un jour d'événement Flex D ne prévoyait que 4 à 5 bûches,
pour la seule fenêtre, et le plan de feu coupait la journée en deux feux (matin, puis après-midi), ce qui supposait
deux allumages. La réserve (5 bûches par événement attendu, ≈ 115 au départ) était dimensionnée pour ces petits feux.

## Options
- A. Garder les règles telles quelles (petit feu ciblé sur la fenêtre).
- B. Aligner les règles sur la pratique de Marc : journée complète les jours d'événement, réserve à la hauteur,
  un seul feu continu ; et une part plus prudente de la chaleur livrée dans la fenêtre du matin.

## Pour et contre
- A : moins de bois par événement ; mais ne décrit pas ce que Marc fait vraiment, et sous-estime la dépense.
- B : la simulation dépense ce que Marc brûlera réellement (≈ 39 bûches de plus par saison en moyenne) ; la marge
  de fin de saison diminue, et avec la météo de 2025-26 le tas serait vide vers le 18 mars.

## Décision
Option B, en quatre points confirmés par Marc :
1. **Règle 1** : un jour d'événement est une journée de chauffe complète. Bûches = le plus grand de : besoin des
   fenêtres, plafond des règles 3 et 4 (0,45 × degrés-jours, au plus 12) et un plancher de 11 ; au plus 15.
2. **Réserve** : 9 bûches par événement encore attendu (≈ 207 au 1er décembre, au lieu de ≈ 115).
3. **Plan de feu** : un seul feu, gardé vivant toute la journée par des recharges régulières (en 2023-24, Marc ne
   le laissait jamais tomber aux braises entre le matin et l'après-midi). Allumer ≈ 1 h 30 avant le moment visé,
   jamais avant 6 h : tout jour de feu s'allume à 6 h, même quand seul l'événement de 16 h est annoncé et que le
   matin est doux (précision de Marc du 26 nov., 11 h) ; dernière charge vers 19 h, ou vers 21 h 30 si la nuit est ≤ −10 °C. Les bûches du jour sont réparties sur les recharges.
4. **Part de la chaleur d'une bûche livrée dans la fenêtre** : 55 % pour un événement du matin (feu allumé à 6 h,
   pleine chaleur vers 7 h 30), 70 % pour l'après-midi (inchangé). Plage inconnue (hiver simulé sans données
   d'Hydro-Québec) : 55 %, par prudence.

## Conséquences
- Simulation (stock 876, trois météos) : dépense moyenne ≈ 810 bûches au lieu de ≈ 771, marge moyenne au 31 mars
  ≈ 66 au lieu de ≈ 105. Avec la météo de 2025-26, le stock est épuisé le 18 mars (dernier événement couvert) ;
  tous les événements restent couverts dans les trois météos. Valeur évitée moyenne ≈ +20 $ par saison, surtout
  parce que plus de bois est brûlé (ce bois ne reste pas pour l'hiver suivant).
- La réserve plus haute ne change presque rien à la simulation : elle n'a jamais refusé de feu les jours froids avant mars.
- Remplace les quantités de la règle 1 et de la réserve de `2026-11-22-regle-de-budget-avec-reserve`, et le partage
  en deux feux de `2026-11-23-min-max-moment-du-feu`.
- À vérifier avec les saisies de l'hiver : bûches réellement brûlées un jour d'événement, rythme des recharges,
  et la part de 55 % le matin
  (il faudrait les kWh horaires pour la mesurer).

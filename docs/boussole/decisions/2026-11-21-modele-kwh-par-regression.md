# Estimer les kWh évités par une régression (≈ 4,5 kWh par bûche)

- **Date :** 2026-11-21
- **Statut :** Acceptée (confirmée par Marc le 2026-11-23)
- **Source :** Première analyse de l'hiver 2023-24, commit `79e97d8` ; page Méthode.

## Contexte
Le chiffrier 2023-24 estimait à la main, chaque jour de feu, les kWh qu'on aurait consommés sans feu. Il fallait une mesure plus objective du gain d'une bûche, à température égale.

## Options
- A. Garder l'estimation manuelle du chiffrier (≈ 4,1 kWh par bûche).
- B. Comparer aux seuls jours sans feu.
- C. Régression sur les 102 jours mesurés : kWh = a + b × degrés-jours + c × bûches, météo publique.

## Pour et contre
- A : simple, mais subjectif et non reproductible.
- B : les 28 jours sans feu sont presque tous doux ; impossible d'extrapoler à −14 °C.
- C : utilise tous les jours, donne une incertitude ; dépend d'une météo de réanalyse et ignore la masse thermique (la chaleur rendue le lendemain).

## Décision
Option C. Retenu : **4,50 kWh évités par bûche** (erreur-type 0,46 ; plage plausible 3,6 à 5,7). Le test d'une interaction bûches × froid n'est pas significatif : **pas de gain supplémentaire par grand froid**, plutôt l'inverse.

## Conséquences
- Toute valeur en dollars du site part de ce coefficient.
- Viser les jours froids ne se justifie pas par un meilleur rendement, mais par la préparation aux événements de pointe (voir `2026-11-22-cibler-moments-rentables`).
- Les lignes « E » (extrapolées) du chiffrier sont exclues des calculs.
- À réestimer avec les données 2026-27 (jours témoins, kWh horaires des jours d'événement).

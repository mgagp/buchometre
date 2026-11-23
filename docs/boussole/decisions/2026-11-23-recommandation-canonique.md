# Recommandation canonique dans le dépôt

- **Date :** 2026-11-23
- **Statut :** Acceptée (portée de l'étape 2 fixée par Marc) ; détails de calcul ci-dessous en « Hypothèse »
- **Source :** Étape 2 « Le temps qui avance » ([issue #6](https://github.com/mgagp/buchometre/issues/6)).

## Contexte
La recommandation du matin était calculée à deux endroits : une approximation sur l'accueil du site (seuil de
température, sans creux) et un calcul à part dans la routine du matin. Deux calculs finissent par diverger.

## Options
- A. Garder deux calculs et les tenir alignés à la main.
- B. Un seul module dans le dépôt, publié en JSON ; la routine du matin ne fait que le lire.

## Pour et contre
- A : aucun travail, mais deux vérités possibles un matin d'événement.
- B : une seule règle, testée par la simulation elle-même ; la routine dépend du site publié (repli prévu si le fichier n'est pas du jour).

## Décision
Option B. `outils/calculs/recommandation.py` contient la règle de budget (`decider`, utilisée aussi par la simulation de
`protocole.py`), la détection des creux froids (`creux`, la même pour l'historique et la prévision) et le verdict du jour.
Ordre : (1) événement Flex D annoncé, allumer 30 à 60 min avant ; (5) plus de 50 bûches sous le plan, événements seulement ;
(3) jour cœur d'un creux, T moy ≤ −5 °C, période critique, jusqu'à 12 bûches si le stock reste au-dessus de la réserve ;
(4) dès le 1er janvier, T moy ≤ 0 °C, même condition ; sinon pas de feu. Prévision : Environnement Canada pour
Vaudreuil-Dorion, Open-Meteo en secours ; la source est affichée. Résultat publié dans `data/recommandation.json`.

Hypothèses (choix techniques, à confirmer à l'usage) :
- T moyenne d'un jour selon Environnement Canada = (maximum + moyenne des minimums des nuits avant et après) / 2.
  *Remplacée le même jour* : (max + min de la nuit précédente, sinon suivante) / 2, voir `2026-11-23-meteo-observee-ec`.
- Jour cœur = même définition que l'analyse historique (médiane des 31 jours autour, ici réel puis prévision) ;
  en bout de prévision, la fenêtre est tronquée.
- Sans prévision du jour : verdict « indéterminé » (mode ouvert), affiché ; un événement annoncé reste recommandé.

## Conséquences
- La simulation et la recommandation ne peuvent plus diverger (vérifié : sorties de la simulation identiques avant et après).
- La routine du matin devient une lectrice de `data/recommandation.json`.
- Le jour témoin (règle 6) n'est pas proposé automatiquement ; il reste au choix de Marc.

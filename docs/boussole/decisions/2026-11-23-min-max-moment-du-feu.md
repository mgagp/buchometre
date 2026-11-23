# Température du jour en min / max, heure du min et plan de feu

- **Date :** 2026-11-23
- **Statut :** Acceptée (options A1, B1 et C1 ajustée, choisies par Marc) ; heures et seuils en « Hypothèse » (points de départ)
- **Source :** [issue #10](https://github.com/mgagp/buchometre/issues/10) : analyse chiffrée et échanges avec Marc du 23 nov. (15 h 13 à 15 h 18) ;
  amendement du 23 nov., 15 h 49 (feu du matin à 6 h).

## Contexte
Le site affichait la température moyenne du jour. Pour Marc, ce qui compte, c'est le min, le max et surtout le moment du min :
un feu au mauvais moment fait « cuire » la maison. La recommandation disait seulement « dès le matin, puis entretenir
jusqu'au soir », ou « 30 à 60 min avant » pour un événement.

## Options
- Affichage : A1, min / max avec l'heure du min et la moyenne en petit ; A2, A1 plus une courbe horaire ; A3, min / max sans la moyenne.
- Indicateur de décision : B1, la moyenne (max + min) / 2 ; B2, les degrés-heures horaires ; B3, le min.
- Moment : C1, deux feux alignés sur le froid et sur Flex D ; C2, une heure calculée à partir de l'heure du min ; C3, le statu quo.

## Pour et contre
- Sur 102 jours mesurés (2023-24), aucun indicateur ne prédit nettement mieux les kWh. L'erreur hors échantillon (LOO) est
  de 15,06 pour la moyenne, 14,99 pour les degrés-heures, 15,22 pour le max et 15,59 pour le min. Le min seul est le moins
  bon : B1 garde la règle simple et cohérente avec les normales.
- Le creux de la nuit tombe entre 4 h et 8 h une nuit sur deux (52 %), en soirée une nuit sur cinq (22 %). La fenêtre de
  6 h à 10 h est la plus froide de la journée. Le moment compte donc pour le confort, et il coïncide avec Flex D.
- C2 est trop précis pour l'incertitude : Open-Meteo place l'heure du min à ±2 h 79 % du temps, et la prévision horaire
  d'EC ne couvre que 24 h.

## Décision
- **A1.** Pour chaque jour : « min / max °C · min vers HH h », avec la moyenne en petit. L'heure ne s'affiche que si une
  prévision horaire couvre la nuit du minimum : EC (24 h), sinon Open-Meteo marqué « (modèle) ». Pour les jours passés,
  min et max observés par EC, et heure du min tirée de climate-hourly (nouvelle colonne `heure_min` de
  `data/meteo_observee_*.csv`).
- **B1.** On garde la moyenne (max + min) / 2 pour décider du feu et du nombre de bûches.
- **C1 ajustée** avec les données de Marc ; les événements Flex D priment.
  - Un feu met environ 1 h 30 à atteindre sa température : on allume 1 h 30 avant le moment visé, événements compris
    (vers 4 h 30 pour 6 h et vers 14 h 30 pour 16 h ; avant : 30 à 60 min).
  - Règles 3 et 4 : deux feux, à peu près la moitié des bûches chacun, vers 4 h 30 et vers 14 h 30.
  - Max prévu ≥ −1 °C : chaque feu est plafonné à environ 4 h, puis on laisse baisser.
  - On réduit la charge vers 19 h (sommeil, étage), sauf si le min prévu de la nuit est ≤ −10 °C : dernière charge vers 21 h 30.
  - Creux prévu en soirée : le feu de l'après-midi reçoit les deux tiers des bûches.
  - Paramètres : `PLAN` dans `outils/calculs/recommandation.py`, le seul endroit où ils sont définis.

## Conséquences
- `data/recommandation.json` reçoit de nouveaux champs : `t_min`, `t_max`, `heure_min`, `heure_min_source`, `plan_feu`, et
  dans `jours[]` : `heure_min`, `heure_min_source`, `plan_feu`. Les champs existants restent ; `moment` décrit maintenant le plan.
- La simulation, le plan de stock et la décision ne changent pas : ils sont vérifiés identiques.
- À ajuster avec les retours de confort : 1 h 30, −1 °C, 4 h, 19 h, −10 °C, et le partage moitié-moitié.
- Le feu du matin se décide la veille : la recommandation de 5 h 45 arrive juste avant, mais la routine de 7 h arrive après. Le plan de demain est donc publié dès aujourd'hui.
- Limite : l'effet du moment sur les kWh n'est pas mesuré ; il faudrait les kWh horaires.

## Amendement du 2026-11-23 (15 h 49) : feu du matin à 6 h
Marc : « je veux bien mettre mon cadran à 5 h 30 et commencer un feu à 6 h le matin, mais 4 h 30, ça n'arrivera pas ».
- Nouveau paramètre `PLAN["allumage_tot"]` = 6 h : aucun feu ne s'allume plus tôt, même si la règle des 1 h 30 le demanderait.
- Jours de feu (règles 3 et 4) : le feu du matin s'allume à 6 h. Dernière charge, puis baisse, vers 10 h ; c'est aussi le
  plafond d'environ 4 h des jours doux. Le feu de l'après-midi reste vers 14 h 30.
- Événement de 6 h à 10 h : on allume aussi à 6 h, et la pleine chaleur arrive vers 7 h 30. Événement de 16 h : toujours vers 14 h 30.
- Conséquence : environ la première heure et demie de l'événement du matin est moins couverte par le bois. Le nombre de
  bûches et la part de chaleur livrée dans la fenêtre (hypothèse de la simulation) ne changent pas ; ce n'est pas mesuré.

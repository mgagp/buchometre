# bois-chauffage : règles de travail

Projet local, jamais publié. Il sert à faire parler les mesures de chauffage au bois de Marc
(hiver 2023-2024 : bûches par jour, kWh Hydro-Québec, température) : électricité évitée par le bois,
économie en dollars et rendement face au prix du bois.

## Structure (calquée sur suivi-pbr)
- `sources/` : copies en lecture seule (chiffrier Google « Bois de chauffage », chiffrier « Hydro »,
  météo Open-Meteo). Jamais modifiées.
- `data/` : CSV et JSON produits par `outils/preparer_donnees.py` (brut fidèle + nettoyé, drapeau
  mesure/extrapole, anomalies, météo, factures, modèle).
- `outils/` : scripts Python, bibliothèque standard seulement. `svg.py` dessine les graphiques
  (SVG intégré, aucun réseau requis).
- `rapports/` : site HTML statique produit par `outils/generer_site.py`. Ouvrir `rapports/index.html`.

## Régénérer
    python outils/preparer_donnees.py
    python outils/generer_site.py

## Principes
1. Les sources sont intouchables ; le chiffrier Google n'est jamais modifié par un agent.
2. Aucun chiffre saisi à la main dans une page : tout vient de `data/`.
3. Les lignes « E » du chiffrier (extrapolées) sont conservées, signalées, et exclues des calculs.
4. Les écarts sont signalés (page Qualité), jamais corrigés en silence.
5. On distingue toujours : mesuré / calculé / hypothèse.

## Protocole hiver 2026-2027 (ajout du 2026-11-22)
Pages `rapports/protocole*.html` : positionnement (tarif Flex D, valeur d'une bûche), étude météo
(période critique, creux froids, événements de pointe), simulation 2026-2027 (sommaire, mensuel, jour par jour)
et saisie avec suivi réel vs projection. Analyse : `outils/protocole.py` ; pages : `outils/generer_protocole.py`.

### Saisir une journée
Ouvrir `data/saisie_2026-2027.csv` (Excel, LibreOffice ou éditeur texte) et ajouter une ligne par jour,
même sans feu :

    date,buches,kwh,evenement_hq,jour_temoin,remarque
    2026-12-08,9,61,oui,non,feu allumé 5 h 30 pour l'événement du matin

- `date` : AAAA-MM-JJ ; `buches` : nombre ; `kwh` : consommation du jour (Espace client Hydro-Québec)
- `evenement_hq` : oui/non ; `jour_temoin` : oui si jour froid volontairement sans feu ; `remarque` : libre
- Enregistrer en CSV (séparateur virgule, UTF-8).

### Régénérer
    py outils\preparer_donnees.py --maj    (télécharge la météo Open-Meteo et les événements HQ, puis recalcule)
    py outils\generer_site.py              (réécrit rapports\, puis F5 dans le navigateur)
Sans connexion internet, omettre `--maj` : les sources déjà présentes sont utilisées.

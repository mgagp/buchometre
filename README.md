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

# <img src="theme/favicon.svg" alt="" width="32" height="32"> buchometre

[![Publier le site](https://github.com/mgagp/buchometre/actions/workflows/pages.yml/badge.svg)](https://github.com/mgagp/buchometre/actions/workflows/pages.yml)

Le bûchomètre : combien d'électricité chaque bûche fait économiser, et quand il vaut la peine de faire un feu.

**Site : https://mgagp.github.io/buchometre/** (consultable sur téléphone)

Mesures de chauffage au bois d'une maison de Vaudreuil-Dorion (Québec) : bûches par jour, consommation
Hydro-Québec, température. À l'accueil, le tableau de bord de la saison en cours (recommandation du jour avec min / max, heure du min et plan de feu, stock,
réel contre plan, événements de pointe Flex D, calendrier) ; puis le journal des saisies, la stratégie (règles,
plan simulé, étude météo, inventaire), les archives (hiver 2023-2024) et la méthode.

## Fonctionnement
- La saisie quotidienne se fait dans `data/saisie_2026-2027.csv` ; les saisons sont déclarées dans `data/saisons.json`.
- Trois couches : `outils/calculs/` (chiffres), `outils/rendu/` (HTML), `theme/` (apparence).
- GitHub Actions reconstruit et publie `rapports/` sur GitHub Pages à chaque push sur `main` et chaque matin
  (10 h 45 UTC, soit 5 h 45 à Toronto en hiver) avec la prévision d'Environnement Canada (Open-Meteo en secours)
  et les événements du jour. La recommandation du matin est conservée dans `data/recommandations_2026-2027.csv`,
  la météo observée (Environnement Canada, station Ste-Anne-de-Bellevue 1) dans `data/meteo_observee_2026-2027.csv`
  (un seul commit automatique par jour) et publiée dans [`data/recommandation.json`](https://mgagp.github.io/buchometre/data/recommandation.json).
- Python 3, bibliothèque standard seulement. Pour générer localement :

      python outils/preparer_donnees.py    # --maj pour rafraîchir météo, prévision et événements
      python outils/generer_site.py        # puis ouvrir rapports/index.html
      python outils/verifier_site.py       # liens et thème

Détails (structure, format de saisie, règles, modèle) : [AGENTS.md](AGENTS.md).
Licence : [MIT](LICENSE).

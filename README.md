# buchometre

Le bûchomètre : combien d'électricité chaque bûche fait économiser, et quand il vaut la peine de faire un feu.

**Site : https://mgagp.github.io/buchometre/** (consultable sur téléphone)

Mesures de chauffage au bois d'une maison de Vaudreuil-Dorion (Québec) : bûches par jour, consommation
Hydro-Québec, température. Le site présente l'hiver 2023-2024 (sommaire, mois, jours, données brutes, qualité,
méthode), l'inventaire de la pile et le protocole de l'hiver 2026-2027 au tarif Flex D (étude météo, simulation,
saisie et suivi).

## Fonctionnement
- La saisie quotidienne se fait dans `data/saisie_2026-2027.csv`.
- À chaque push sur `main`, GitHub Actions exécute `outils/preparer_donnees.py` puis `outils/generer_site.py`
  et publie `rapports/` sur GitHub Pages.
- Python 3, bibliothèque standard seulement. Pour générer localement :

      python outils/preparer_donnees.py
      python outils/generer_site.py        # puis ouvrir rapports/index.html

Détails (structure, format de saisie, règles, modèle) : [AGENTS.md](AGENTS.md).

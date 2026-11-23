# theme/ : l'apparence du Bûchomètre

Tout ce qui est visuel vit ici : `site.css` (variables de couleur, typographie, motifs), les polices
(`polices/`), les images (`favicon.svg`, `motifs/`). `outils/generer_site.py` copie ce dossier dans
`rapports/assets/` (sauf ce README).

**Identité** (jalon 2, issue #2, décision du 23 nov. 2026) : camp de bûcherons cartoon — noyer, chemise
à carreaux rouge et noir, grain de bois, poêle. Polices SIL Open Font License, hébergées ici, sans CDN :
Calistoga (marque, titres, verdict) et Nunito Sans (texte et chiffres). Le logo (`favicon.svg`) reprend le
poêle, la bûche et la flamme du premier pictogramme, avec un badge noyer et un anneau doré ; le gabarit
l'affiche dans l'en-tête (`header.site .logo`).

**Contrat** : le Python n'écrit aucune couleur. Il émet des classes stables et, pour les graphiques SVG,
des références `var(--g-<clé>)`. Un relooking ne modifie que ce dossier (et, au besoin, le balisage de l'en-tête
dans `outils/rendu/gabarit.py`). La saisie quotidienne ne touche jamais ce dossier.

## Variables
- Interface : `--fond`, `--surface`, `--encre`, `--encre-douce`, `--ligne`, `--accent`, `--entete`, `--police`,
  `--police-titre`, `--rayon`, `--sur-vif`, états `--ok/--ko/--prov/--info-*`.
- Calendrier : `--t-chaud`, `--t-doux`, `--t-frais`, `--t-froid`, `--t-tresfroid`, `--t-glacial`.
- Graphiques : `--g-<clé>` pour chaque clé de `outils/rendu/graphes.py` (`CLES`) : `reel`, `buche`, `plan`, `reserve`, `evt`, `temp`…
- Motifs : `--carreaux`, `--grain` (fichiers dans `motifs/`).

## Classes stables
- Gabarit : `header.site`, `.marque`, `.logo`, `.contexte`, `nav.menu`, `.onglet(.actif)`, `nav.sousnav`, `main.contenu`, `footer.pied`, `body.tableau-de-bord`.
- Tableau de bord : `.bloc`, `.bloc-titre`, `.bloc-lien`, `.grille-blocs`, `.bloc-jour`, `.verdict(-feu|-non|-na)`, `.raison`, `.vignettes`, `.vignette(.actif|.feu|.coeur)`, `.evt-jour`,
  `.chiffre`, `.jauge`, `.jauge-reserve`, `.jauge-valeur`, `.jauge-repere`, `.temps`, `.temps-zone.zone-critique`, `.temps-ecoule`, `.temps-marque`,
  `.temps-auj`, `.temps-axe`, `.minis`, `.mini`, `.mini-barre`, `.mini-reel`, `.mini-plan`, `.compteurs`, `.compteur(.c-couvert|.c-manque)`, `.vide`, `.liens-bas`.
- Calendrier : `table.calendrier`, cases `.t-*` (température), `.prev`, `.auj`, `.st-saisi|.st-manquant|.st-futur|.st-avant`, `.evt-annonce|.evt-couvert|.evt-manque|.evt-nonsaisi`, `.reco-feu` (feu recommandé ce matin-là),
  `.pastille`, `.losange`, `.croix`, `.legende`, `.leg`.
- Analyse : `.cartes`, `.carte(.ok|.ko|.neutre|.prov)`, `.alerte`, `.info`, `.petit`, `.badge`, `.tab`, `.defile`, `.graphe`, `.ax`, `.grille`, `.axe0`, `.ligne-auj`, `.pile-*`.

Seules des géométries (largeur, position en %) passent par `style=` dans le HTML généré ; `outils/verifier_site.py`
échoue si une couleur codée en dur apparaît dans une page.

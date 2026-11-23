# buchometre : directives pour les agents

Site public : https://mgagp.github.io/buchometre/ · dépôt : https://github.com/mgagp/buchometre

## Commencer ici : la boussole
Avant toute modification autre qu'une saisie, lire [docs/boussole/](docs/boussole/README.md) :
- [INTENTION.md](docs/boussole/INTENTION.md) : pourquoi le projet existe, ses valeurs, son périmètre, qui décide ;
- [PRINCIPES.md](docs/boussole/PRINCIPES.md) : comment trancher quand aucune règle ne s'applique ;
- [decisions/](docs/boussole/decisions/README.md) : les choix datés, avec leurs raisons et leur statut.

Pour une simple saisie, la section « Ajouter une saisie » ci-dessous suffit.

**Ajouter une décision** quand un choix change une règle de chauffe, un comportement du site, une contrainte
ou une façon de travailler : copier le modèle de `docs/boussole/decisions/README.md` dans
`docs/boussole/decisions/AAAA-MM-JJ-sujet.md`, ajouter une ligne à l'index, puis faire un commit dédié
(« Boussole : … »). Une décision prise sans l'accord explicite de Marc a le statut « Hypothèse ». On ne réécrit
pas une ancienne décision : on la marque « Remplacée par … ». Ce fichier reste une table de pointeurs : on n'y
recopie pas le contenu de la boussole.

## But
Faire parler les mesures de chauffage au bois d'une maison de Vaudreuil-Dorion (Québec) : bûches brûlées,
kWh Hydro-Québec, température. On en tire l'électricité évitée par le bois, sa valeur en dollars et un
protocole pour l'hiver 2026-2027 : chauffer aux moments les plus rentables (événements de pointe Flex D d'abord,
puis jours les plus froids), avec un stock de bois limité.

## Le site (5 entrées)
- **Saison** (`index.html`) : tableau de bord de la saison courante (recommandation du jour, stock contre réserve,
  avancement, réel contre plan, événements Flex D, calendrier, courbe de stock, recommandé et fait).
- **Journal** (`journal.html`) : historique « recommandé, puis fait », journées saisies, jours à saisir, réel contre plan, mode d'emploi.
- **Stratégie** (`strategie/`) : règles et tarif (`index`), plan de saison simulé (`plan`, ancres `#mensuel`, `#jours`),
  étude météo (`meteo`), inventaire de la pile (`inventaire`).
- **Archives** (`archives/`) : saisons passées ; l'hiver 2023-24 (chiffrier) dans `archives/2023-2024/`.
- **Méthode** (`methode.html`) : modèle, incertitudes, historique des décisions, fonctionnement du site.
- Les anciennes adresses (`protocole*.html`, `jours.html`, `mois-*.html`, `decisions.html`…) redirigent vers les nouvelles
  (`ROUTES` dans `outils/rendu/gabarit.py`). Publiés aussi : `data/recommandation.json` (la recommandation du jour,
  lue par la routine du matin) et `data/saison_courante.json` (tout l'état du tableau de bord).

## Structure : trois couches séparées
- `sources/` : copies en lecture seule (chiffrier exporté, météo et prévision Open-Meteo, prévision d'Environnement
  Canada pour Vaudreuil-Dorion, événements de pointe HQ,
  grille tarifaire). Ne pas modifier à la main ; `--maj` les rafraîchit. `sources/maj_statut.json` n'est pas versionné.
- `data/` : **saisie manuelle** `data/saisie_2026-2027.csv`, inventaire `data/inventaire_pile_2026-11.csv`,
  **`data/saisons.json`** (saisons, dates, saison courante), **`data/recommandations_2026-2027.csv`** (historique :
  une ligne par matin, écrite et commitée par le workflow, ne pas modifier à la main) et les CSV/JSON dérivés.
- `outils/calculs/` (données → chiffres, **aucun HTML**) : `preparer_donnees.py` (2023-24, modèle, téléchargements),
  `protocole.py` (météo, creux, simulation), `inventaire.py`, `saison.py` (état de la saison à une date),
  `recommandation.py` (**source canonique** : règle de budget, creux froids, verdict du jour ; la simulation l'utilise aussi),
  `prevision.py` (Environnement Canada, Open-Meteo en secours), `valider_saisie.py`, `saisons.py`.
- `outils/rendu/` (chiffres → HTML, **aucune couleur**) : `gabarit.py` (en-tête, menu, liens, redirections),
  `composants.py` (bloc, jauge, barre de temps, calendrier…), `graphes.py` (SVG, couleurs par variables du thème),
  `pages/` (un module par section : `saison`, `journal`, `strategie`, `methode`, `archives_2023`).
- `theme/` (**apparence seulement**) : `site.css` (variables, typographie), polices OFL, motifs, favicon ; copié dans `rapports/assets/`.
  L'identité vit dans ce dossier (et, au besoin, le logo dans `outils/rendu/gabarit.py`). Classes stables : `theme/README.md`.
- Points d'entrée : `outils/preparer_donnees.py`, `outils/generer_site.py`, `outils/verifier_site.py`,
  `outils/enregistrer_recommandation.py` (ligne du jour dans l'historique ; appelé par le workflow du matin).
- `rapports/` : site généré, **non versionné** (sauf `rapports/img/`). GitHub Actions le reconstruit et le publie à chaque
  push sur `main`, chaque matin à 10 h 45 UTC (5 h 45 à Toronto en hiver, 6 h 45 en été) et à la main
  (`.github/workflows/pages.yml`). En CI, `--maj` rafraîchit météo, prévisions et événements pour la construction
  (sans les commiter) ; si un téléchargement échoue, les fichiers versionnés sont utilisés et l'accueil le dit.
  Le cron et le lancement manuel commitent en plus la recommandation du jour (`github-actions[bot]`, `GITHUB_TOKEN`,
  au plus un commit par jour, aucun si la ligne existe) : faire `git pull` avant de pousser une saisie.
- Essai à une autre date : `BUCHOMETRE_DATE=2026-12-15 python outils/generer_site.py` (dans une copie, avec de fausses données).

## Ajouter une saisie
Une ligne par jour dans `data/saisie_2026-2027.csv`, même sans feu, UTF-8, virgules :

    date,buches,kwh,evenement_hq,jour_temoin,stock_compte,remarque
    2026-12-08,5,61,oui,non,,feu allumé 5 h 30 pour l'événement du matin
    2026-12-01,0,72,non,non,330,tas recompté

- `date` AAAA-MM-JJ ; `buches` nombre ; `kwh` consommation du jour (Espace client Hydro-Québec), **peut rester vide**
  et être complété plus tard (mettre à jour la ligne, ne pas la dupliquer) ; `evenement_hq` oui/non ;
  `jour_temoin` oui si jour froid volontairement sans feu ; `stock_compte` facultatif (recomptage réel) ; `remarque` libre.
- Une valeur inconnue reste vide : ne jamais inventer un chiffre. Les jours sans ligne sont signalés à partir du 1er déc.
- `preparer_donnees.py` valide la saisie d'abord : une **erreur** (date illisible ou en double, date future, nombre
  invalide, oui/non invalide) arrête tout et bloque la publication ; une valeur inhabituelle est seulement signalée.

## Régénérer, vérifier, publier
    python outils/preparer_donnees.py --maj   # --maj : météo, prévision, événements HQ (facultatif)
    python outils/generer_site.py             # génère rapports/
    python outils/verifier_site.py            # liens internes, ancres, aucune couleur codée en dur
    git pull --rebase                         # récupérer le commit automatique du matin
    git add data/saisie_2026-2027.csv && git commit -m "Saisie du 2026-12-08 au 2026-12-10"
    git push                                  # Actions reconstruit et publie (≈ 1 min)

## Changer de saison (ex. 2027-2028)
Ajouter une entrée `type: suivi` dans `data/saisons.json` (dates, `debut_suivi`, `flex_d`, fichiers), créer
`data/saisie_2027-2028.csv` (en-tête seulement), mettre `courante` à `2027-2028`. La saison précédente apparaît dans
Archives avec son tableau de bord figé. À revoir à ce moment : inventaire de départ et paramètres du protocole
(`outils/calculs/protocole.py`, encore propre à 2026-27).

## Règles
1. **Un commit par saisie**, même si elle couvre plusieurs jours. Pas de pull request, push direct sur `main`.
   Issues seulement pour les jalons ou une vraie question.
2. Ne jamais modifier les chiffriers Google de Marc : ils sont en lecture seule.
3. Aucun chiffre saisi à la main dans une page : tout vient de `data/`.
4. Les lignes « E » (extrapolées) du chiffrier 2023-24 sont signalées et exclues des calculs.
5. Les écarts sont signalés (page Qualité), jamais corrigés en silence. Toujours distinguer mesuré / calculé / hypothèse.
6. Dépôt public : aucune adresse, numéro de client ou de compteur, courriel, lien privé ou chemin local.
7. Le style (identité visuelle) reste dans `theme/` : aucune couleur dans le Python, aucune donnée dans le thème.
8. Avant de pousser : `outils/verifier_site.py` doit passer (il tourne aussi en CI).

## Modèle en bref
- Régression sur 102 jours mesurés (2023-24) : kWh ≈ 50 + 1,94 × degrés-jours (base 18 °C) − 4,50 × bûches,
  soit ≈ 4,5 kWh évités par bûche (3,6 à 5,7).
- Tarif **Flex D** (1er avril 2026), hiver du 1er déc. au 31 mars : 4,886 ¢/kWh jusqu'à 40 kWh × jours, puis
  9,103 ¢ ; **46,463 ¢/kWh pendant un événement de pointe** (6 h-10 h ou 16 h-20 h, avis la veille avant 15 h).
  Hors hiver : tarif D (7,065 / 11,142 ¢).
- Stock de départ 2026-27 : inventaire mesuré de la pile, ≈ 876 bûches (≈ 4,1 cordes de face, bûches de 16 po,
  une seule rangée : confirmé par Marc).
- Règles de chauffe : événements toujours (4-5 bûches) ; réserve de 5 bûches par événement attendu ; jours ≤ −5 °C
  jusqu'à 12 bûches ; surplus libéré dès le 1er janvier ; 50 bûches sous le plan → événements seulement.
  Une seule implémentation : `outils/calculs/recommandation.py`. Le plan = la règle appliquée à la météo réelle
  depuis l'inventaire ; la projection = la règle sur la prévision, puis la dépense moyenne des 3 hivers simulés.
- Limite connue : la prime d'événement réelle n'est pas mesurée (il faudrait les kWh horaires).

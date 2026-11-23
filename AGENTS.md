# buchometre : directives pour les agents

Site public : https://mgagp.github.io/buchometre/ · dépôt : https://github.com/mgagp/buchometre

## But
Faire parler les mesures de chauffage au bois d'une maison de Vaudreuil-Dorion (Québec) : bûches brûlées,
kWh Hydro-Québec, température. On en tire l'électricité évitée par le bois, sa valeur en dollars et un
protocole pour l'hiver 2026-2027 : chauffer aux moments les plus rentables (événements de pointe Flex D d'abord,
puis jours les plus froids), avec un stock de bois limité.

## Structure
- `sources/` : copies en lecture seule (chiffrier d'origine exporté en CSV, météo Open-Meteo, événements de
  pointe Hydro-Québec, grille tarifaire). Ne pas modifier à la main.
- `data/` : CSV et JSON produits par `outils/preparer_donnees.py`, **plus la saisie manuelle**
  `data/saisie_2026-2027.csv` et l'inventaire `data/inventaire_pile_2026-11.csv`.
- `outils/` : scripts Python, bibliothèque standard seulement (`svg.py` dessine les graphiques, hors ligne).
- `rapports/` : site HTML généré par `outils/generer_site.py`. **Non versionné** (sauf `rapports/img/`) :
  GitHub Actions le reconstruit et le publie à chaque push sur `main` (`.github/workflows/pages.yml`).

## Ajouter une saisie
Une ligne par jour dans `data/saisie_2026-2027.csv`, même sans feu, dates en ordre croissant, UTF-8, virgules :

    date,buches,kwh,evenement_hq,jour_temoin,stock_compte,remarque
    2026-12-08,5,61,oui,non,,feu allumé 5 h 30 pour l'événement du matin
    2026-12-01,0,72,non,non,330,tas recompté

- `date` AAAA-MM-JJ ; `buches` nombre ; `kwh` consommation du jour (Espace client Hydro-Québec) ;
  `evenement_hq` oui/non ; `jour_temoin` oui si jour froid volontairement sans feu ;
  `stock_compte` facultatif (recomptage réel de la pile) ; `remarque` libre.
- Une valeur inconnue reste vide : ne jamais inventer un chiffre.

## Régénérer, vérifier, publier
    python outils/preparer_donnees.py --maj   # --maj : télécharge météo et événements HQ (facultatif)
    python outils/generer_site.py             # vérifie que tout se génère sans erreur
    git add data sources && git commit -m "Saisie du 2026-12-08 au 2026-12-10"
    git push                                  # Actions reconstruit et publie (≈ 1 min)

La CI n'exécute pas `--maj` : pour rafraîchir météo et événements HQ, lancer `--maj` localement et
committer `sources/` et `data/` avec la saisie.

## Règles
1. **Un commit par saisie**, même si elle couvre plusieurs jours. Pas de pull request, push direct sur `main`.
   Issues seulement pour les jalons ou une vraie question.
2. Ne jamais modifier les chiffriers Google de Marc : ils sont en lecture seule.
3. Aucun chiffre saisi à la main dans une page : tout vient de `data/`.
4. Les lignes « E » (extrapolées) du chiffrier 2023-24 sont signalées et exclues des calculs.
5. Les écarts sont signalés (page Qualité), jamais corrigés en silence. Toujours distinguer mesuré / calculé / hypothèse.
6. Dépôt public : aucune adresse, numéro de client ou de compteur, courriel, lien privé ou chemin local.
7. Le style (identité visuelle) doit rester séparé de la génération des données.

## Modèle en bref
- Régression sur 102 jours mesurés (2023-24) : kWh ≈ 50 + 1,94 × degrés-jours (base 18 °C) − 4,50 × bûches,
  soit ≈ 4,5 kWh évités par bûche (3,6 à 5,7).
- Tarif **Flex D** (1er avril 2026), hiver du 1er déc. au 31 mars : 4,886 ¢/kWh jusqu'à 40 kWh × jours, puis
  9,103 ¢ ; **46,463 ¢/kWh pendant un événement de pointe** (6 h-10 h ou 16 h-20 h, avis la veille avant 15 h).
  Hors hiver : tarif D (7,065 / 11,142 ¢).
- Stock de départ 2026-27 : inventaire mesuré de la pile, ≈ 876 bûches (≈ 4,1 cordes de face, bûches de 16 po).
- Règles de chauffe : événements toujours (4-5 bûches) ; réserve de 5 bûches par événement attendu ; jours ≤ −5 °C
  jusqu'à 12 bûches ; surplus libéré dès le 1er janvier ; 50 bûches sous le plan → événements seulement.

# Principes de travail

Ce sont des repères pour trancher quand aucune règle précise ne s'applique, pas une procédure à appliquer
mécaniquement. Le but et les valeurs sont dans [INTENTION.md](INTENTION.md) ; les règles pratiques (format de
saisie, commandes) sont dans `AGENTS.md`. Ce fichier ne les répète pas.

## Faire simple
1. **Rigueur proportionnée.** On choisit le processus le plus léger qui protège encore la décision.
   *Exemple :* une saisie se fait par un commit direct sur `main`, sans pull request ni issue ; une issue ne sert
   qu'à un jalon ou à une vraie question.
2. **80/20.** On vise environ 80 % de la valeur pour 20 % de la complexité.
   *Exemple :* le modèle kWh par bûche est une régression linéaire sur trois variables, pas un modèle thermique
   de la maison ; ses limites sont affichées sur la page Méthode.
3. **Complexité essentielle seulement.** Une couche ou une abstraction qui n'améliore pas le résultat n'a pas sa
   place. *Exemple :* le site est produit par des scripts Python de la bibliothèque standard ; pas de cadriciel
   JavaScript ni de npm pour une vingtaine de pages.
4. **Un seul endroit par concept.** On renvoie à la source de vérité au lieu de recopier un chiffre ou une règle.
   *Exemple :* le stock de départ vit dans `data/inventaire_pile_2026-11.csv` et les règles de chauffe dans
   `data/protocole.json` ; les pages et `AGENTS.md` les lisent ou y renvoient. Dans la boussole, l'intention est
   dans `INTENTION.md`, chaque décision dans son fichier, et rien n'est dupliqué ailleurs.
5. **Les cas simples restent simples.** La sophistication attend d'avoir prouvé son utilité.
   *Exemple :* la saisie reste un CSV d'une ligne par jour ; les colonnes déduites (événement, jour témoin)
   viendront seulement si elles évitent un vrai effort à Marc.
6. **Dire ce qui se passe quand ça casse**, en une ligne, aux vraies frontières.
   *Exemple :* si le téléchargement de la météo ou des événements échoue en CI, on continue avec les données
   versionnées et la page affiche « prévision indisponible » (échec ouvert). Si la validation de la saisie
   trouve une erreur, la publication s'arrête et le site garde sa version précédente (échec fermé) : rien de faux
   n'est publié.

## Garder la mémoire dans le dépôt
7. **Le dépôt est la mémoire.** Une décision qui change un comportement, une règle ou une façon de travailler est
   écrite dans `docs/boussole/decisions/`, avec sa raison. Une décision restée dans une conversation n'est pas
   enregistrée. *Exemple :* l'assouplissement des règles de chauffe du 22 novembre 2026 a son propre fichier.
8. **Un démarrage à froid court.** `AGENTS.md` est lu à chaque session et sert de table de pointeurs ; on ne lit
   le reste qu'au besoin. *Exemple :* pour une saisie, `AGENTS.md` suffit ; pour un changement de règle, on lit
   `INTENTION.md` et les décisions concernées.

## Posture
9. **Des choix assumés.** On recommande une option et on dit pourquoi, au lieu d'aligner des possibilités.
   *Exemple :* « pas de corde d'appoint cette année », chiffré, plutôt qu'un « ça dépend ».
10. **Des affirmations honnêtes.** On dit ce que le site mesure, ce qu'il estime et ce qu'il ne sait pas ; pas de
    survente. *Exemple :* le gain d'une bûche est présenté comme 4,9 kWh, plage de 3,9 à 6,2, et le stock comme
    876 bûches, fourchette de 876 à 947.
11. **L'information là où l'on regarde déjà.** On juge l'expérience d'ensemble, surtout sur téléphone.
    *Exemple :* la recommandation du jour et le stock sont en haut de l'accueil, au lieu d'être cachés dans une
    page de protocole.

## Pratiques
12. **Marc décide des changements de direction.** Les saisies, les correctifs et les mises à jour de données vont
    directement sur `main` ; un changement de but, de règle de chauffe ou d'identité attend son accord.
    *Exemple :* le menu à cinq entrées a été appliqué seulement après les cinq réponses de Marc du 23 nov. 2026.
13. **« Fini » se vérifie à l'écran.** Avant de dire qu'une page est terminée, on la parcourt rapidement sur
    téléphone et sur ordinateur, captures à l'appui. *Exemple :* la publication du 23 nov. 2026 a été validée
    par Marc sur PC et sur téléphone avant de lancer le relooking.

# Intention du projet

*État au 23 novembre 2026, après l'étape 2 (le temps qui avance). Modifier seulement quand Marc change d'avis, et le noter par une décision.*

## Pourquoi le Bûchomètre existe
Marc chauffe une maison de Vaudreuil-Dorion (Québec) au bois et à l'électricité. Depuis 2026, il est au tarif
**Flex D** d'Hydro-Québec : l'électricité coûte environ 9 ¢/kWh en hiver, mais environ 46 ¢/kWh pendant les
**événements de pointe** (6 h-10 h ou 16 h-20 h, annoncés la veille). Son stock de bois est **fini et déjà payé**
(environ 876 bûches pour l'hiver 2026-27).

Le projet répond donc à une question simple : **où placer chaque bûche pour éviter le plus d'électricité ?**
D'abord pendant les événements de pointe, ensuite pendant les creux de froid, sans jamais manquer de bois un jour
d'événement. On vise le **maximum raisonnable**, pas l'optimum dogmatique : une règle simple et suivie vaut mieux
qu'une règle parfaite qu'on abandonne en janvier.

Le projet sert aussi à **mesurer** : combien de kWh une bûche fait réellement économiser, et si suivre le protocole
a payé en fin de saison.

## À qui il sert
- **Marc**, d'abord : un coup d'œil sur son téléphone le matin pour savoir s'il fait un feu, et combien de bûches.
- **Un collaborateur humain ou un agent** qui reprend le travail : il doit pouvoir agir à partir de cette boussole,
  d'`AGENTS.md` et des données, sans refaire la discussion.
- **Un lecteur curieux** : le site est public et doit rester compréhensible sans contexte.

## Valeurs
1. **Pragmatisme.** Des outils simples, proportionnés à une vingtaine de pages. La façon de travailler qui en
   découle est dans [PRINCIPES.md](PRINCIPES.md).
2. **Effort quotidien minimal.** Marc écrit « hier 6 bûches, 71 kWh », en langage naturel, même plusieurs jours
   d'un coup. Tout le reste (calculs, graphiques, publication) est automatique.
3. **Données honnêtes.** Un chiffre inconnu reste vide ; on n'invente jamais un jour manquant. Les écarts sont
   signalés, jamais corrigés en silence.
4. **Incertitudes dites.** On distingue toujours mesuré, calculé et hypothèse, et on donne des fourchettes.
5. **Séparation du style et des données.** Une saisie ne touche que les données ; un relooking ne touche que le
   thème. L'un ne doit jamais casser l'autre.
6. **Plaisir visuel assumé.** Le site doit être beau et avoir une identité québécoise forte : camp en bois rond,
   art populaire, couleurs saturées, un peu cartoon. Mais l'identité reste au service de la lecture des données.

## Dans le périmètre
- Le journal quotidien de la saison (bûches, kWh, événements, stock) et le tableau de bord de la saison en cours.
- Le protocole de chauffe (règles, réserve pour les événements, simulation) et son suivi réel contre le plan.
- Le modèle kWh par bûche, l'inventaire de la pile, la météo et les événements Hydro-Québec publics.
- Les archives des saisons passées (2023-24, puis les suivantes).
- L'identité visuelle du site.

## Hors périmètre
- Le pilotage automatique d'appareils (thermostat, domotique) ou toute action sur le compte Hydro-Québec.
- Les données personnelles : adresse, numéros de client ou de compteur, factures nominatives.
- Une application générique pour d'autres maisons. Une généralisation **légère** (changer de saison sans
  toucher au code) est voulue ; un produit ne l'est pas.
- La modification des chiffriers Google de Marc : ce sont des sources en lecture seule.

## Principes de collaboration
- **Marc décide** des changements de direction. Un assistant propose, chiffre les options avec leur pour et leur
  contre, puis applique le choix. Une décision qu'il prend seul reste une « hypothèse » tant que Marc ne l'a pas
  confirmée (voir [PRINCIPES.md](PRINCIPES.md), principe 12).
- **Un commit par saisie**, même si elle couvre plusieurs jours, poussé directement sur `main`.
- **Pas de pull request.** Les issues servent aux jalons et aux vraies questions, pas au quotidien.
- **Les chiffriers Google de Marc ne sont jamais modifiés.**
- **Rien de privé dans le dépôt public**, et aucun chiffre saisi à la main dans une page : tout vient de `data/`.
- **Les décisions importantes vont dans `docs/boussole/decisions/`**, avec un commit dédié.

## Trajectoire
| Étape | Période | État |
|---|---|---|
| Analyse historique de l'hiver 2023-24 (chiffrier, modèle kWh par bûche) | 21-22 nov. 2026 | Faite |
| Protocole 2026-27 au tarif Flex D (météo, règles, simulation, saisie) | 22 nov. 2026 | Fait |
| Inventaire mesuré de la pile (876 bûches) et règles assouplies | 22 nov. 2026 | Fait |
| Publication publique sur GitHub Pages (jalon 1) | 23 nov. 2026 | Faite |
| Restructuration en mode saison : accueil tableau de bord, 5 menus, archives, régénération chaque matin | 23 nov. 2026 | Faite (issue #4) |
| Le temps qui avance : recommandation canonique (Environnement Canada, creux froids), historique par commit quotidien, plan sur la météo réelle | 23 nov. 2026 | Faite (issue #6) |
| Identité visuelle québécoise (jalon 2), limitée au thème | après la restructuration | À faire |
| Généralisation légère : une saison de plus sans toucher au code (jalon 3) | avant l'hiver 2027-28 | À faire |

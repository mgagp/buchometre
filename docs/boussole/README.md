# La boussole du Bûchomètre

La boussole explique **pourquoi** le projet existe, **ce qu'il vise** et **comment il a évolué**.
Le code et les données disent *quoi* ; la boussole dit *pourquoi*. Elle sert à Marc, à un collaborateur
humain ou à un agent qui doit agir seul sans refaire toute la discussion.

## Comment la lire
1. [INTENTION.md](INTENTION.md) : le but, les valeurs, le périmètre et les principes de collaboration.
   À lire en premier, en entier ; c'est court.
2. [PRINCIPES.md](PRINCIPES.md) : comment on travaille (simplicité, une source par concept, honnêteté,
   qui décide). À consulter quand aucune règle précise ne s'applique.
3. [decisions/](decisions/README.md) : une décision par fichier, datée, avec les options, le pour et le contre.
   L'index donne la liste et le statut de chacune.

`AGENTS.md`, à la racine, reste la porte d'entrée : il pointe ici et ne recopie rien.

En cas de doute, l'intention l'emporte sur une décision, et une décision plus récente l'emporte sur une plus
ancienne. Si une action semble contredire la boussole, on pose la question à Marc avant d'agir.

## Comment la faire évoluer
- **Nouvelle décision** : copier le modèle de [decisions/README.md](decisions/README.md) dans
  `decisions/AAAA-MM-JJ-sujet.md` (date de la décision, sujet court en minuscules, sans accents), puis ajouter
  une ligne à l'index.
- **Décision changée** : on ne réécrit pas l'histoire. On crée une nouvelle décision, et l'ancienne passe au
  statut « Remplacée par … » avec un lien.
- **Intention changée** : modifier `INTENTION.md` seulement quand Marc a changé d'avis sur le but ou les valeurs,
  et le noter par une décision.
- **Statut « Hypothèse »** : une décision proposée ou appliquée par un assistant, sans confirmation explicite de
  Marc. Elle passe à « Acceptée » quand Marc la confirme.
- **Commit** : un commit dédié par mise à jour de la boussole (ex. « Boussole : décision 2026-12-05-… »),
  séparé des saisies quotidiennes.

## Confidentialité
Le dépôt est public : aucune adresse, aucun numéro de compte ou de client, aucun lien privé, aucun chemin local.
Les montants liés au bois et à l'électricité sont acceptables.

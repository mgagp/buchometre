# Un commit par saisie, sans pull request

- **Date :** 2026-11-23
- **Statut :** Acceptée
- **Source :** Demande de Marc, 23 nov. 2026 ; `AGENTS.md`.

## Contexte
Marc ne saisit pas toujours au jour le jour : il peut envoyer trois jours d'un coup. Il fallait éviter de perdre de l'information sans alourdir le flux.

## Options
- A. Un commit par jour saisi.
- B. Un commit par saisie, quel que soit le nombre de jours.
- C. Des pull requests et des issues pour chaque mise à jour.

## Pour et contre
- A : trois commits identiques en substance, sans valeur ajoutée.
- B : chaque saisie est sauvegardée dès qu'elle arrive ; historique lisible.
- C : cérémonie disproportionnée pour un projet d'une personne.

## Décision
Option B, poussé directement sur `main`. Les issues servent aux jalons ou à une vraie question.

## Conséquences
- Chaque push redéploie le site en une minute environ.
- Un jour manquant reste vide ; il n'est jamais inventé.

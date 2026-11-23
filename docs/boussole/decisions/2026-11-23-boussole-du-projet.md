# Une boussole : intention, principes et décisions dans le dépôt

- **Date :** 2026-11-23
- **Statut :** Acceptée (confirmée par Marc le 2026-11-23)
- **Source :** Demande de Marc, 23 nov. 2026 ; issue « Boussole : intention, valeurs et décisions du projet ».

## Contexte
Les intentions, les arbitrages et leurs raisons vivaient dans les conversations. Marc veut qu'un humain ou un agent puisse agir de façon autonome à partir de l'intention, et suivre son évolution.

## Options
- A. Une page « Décisions » sur le site.
- B. Un seul long document.
- C. `docs/boussole/` : un fichier d'intention, un fichier de principes et une décision par fichier, avec un index.

## Pour et contre
- A : mélange décisions, tâches et propositions ; dépend du générateur.
- B : simple au début, illisible après une saison.
- C : découvrable depuis `AGENTS.md`, une décision se lit seule, l'historique reste dans git.

## Décision
Option C, ajoutée par un commit dédié.

## Conséquences
- `AGENTS.md` pointe d'abord vers la boussole.
- Toute décision future qui change une règle, un comportement ou une façon de travailler y est ajoutée.
- La page Décisions du site pourra un jour se générer à partir de ce dossier.

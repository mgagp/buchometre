# Relooking après la restructuration, limité au thème

- **Date :** 2026-11-23
- **Statut :** Acceptée
- **Source :** Échange avec Marc du 23 nov. 2026 ; issue #2.

## Contexte
Marc veut une identité visuelle forte et québécoise (camp en bois rond, art populaire, couleurs saturées), sans que le style complique la saisie quotidienne.

## Options
- A. Relooker tout de suite, sur la structure actuelle.
- B. Restructurer d'abord, puis habiller, en isolant le style dans un dossier de thème.

## Pour et contre
- A : plus rapide à voir, mais figerait une navigation qui ne sert plus le nouvel usage.
- B : un peu plus long ; le relooking ne touche ensuite que le thème, et une saisie que le CSV.

## Décision
Option B. Le style vit dans un dossier `theme/` ; aucune couleur ni `style=` dans le Python.

## Conséquences
- Un relooking et une saisie se vérifient par un `git diff --stat` : chacun reste dans sa zone.
- Depuis la restructuration, `outils/verifier_site.py` refuse en CI tout bloc `<style>` ou toute couleur codée en dur dans les pages générées.

#!/usr/bin/env python3
"""Point d'entrée de la couche calculs.

Usage : python outils/preparer_donnees.py [--maj]
  --maj : télécharge météo (archive + prévision) et événements Hydro-Québec avant de calculer.
          Un téléchargement qui échoue n'arrête rien : on garde les fichiers versionnés de sources/.
Valide d'abord la saisie (une erreur arrête tout, code de sortie 1), puis écrit data/ (CSV/JSON dérivés).
Bibliothèque standard seulement.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculs import preparer_donnees, valider_saisie

if __name__ == "__main__":
    erreurs, avert = valider_saisie.valider()
    for a in avert:
        print("Saisie, à vérifier :", a)
    if erreurs:
        for e in erreurs:
            print("Saisie, ERREUR :", e)
        print("Saisie invalide : corriger data/ avant de régénérer (rien n'a été écrit).")
        sys.exit(1)
    if "--maj" in sys.argv:
        preparer_donnees.mettre_a_jour_sources()
    preparer_donnees.main()
    from calculs import protocole
    o = protocole.analyser()
    print(f"Protocole : {o['n_saisie']} jour(s) saisi(s) ; météo jusqu'au {o['meteo_derniere_date']}")

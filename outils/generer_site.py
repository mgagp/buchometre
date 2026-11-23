#!/usr/bin/env python3
"""Génère le site statique du Bûchomètre dans rapports/ (point d'entrée de la couche rendu).

Usage : python outils/preparer_donnees.py [--maj] && python outils/generer_site.py
Lit data/ (et la prévision dans sources/) ; aucun chiffre saisi à la main. Bibliothèque standard seulement.
  outils/calculs/  données → chiffres (aucun HTML)
  outils/rendu/    chiffres → HTML (aucune couleur) ; gabarit, composants, graphiques, pages/
  theme/           apparence (CSS, variables de couleur) : copié dans rapports/assets/
"""
import os, sys, json, shutil, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chemins import OUT, DATA
from calculs import saison as calc_saison, saisons
from rendu import gabarit
from rendu.pages import archives_2023, strategie, saison as p_saison, journal, methode


def nettoyer():
    """Vide rapports/ sauf rapports/img/ (versionné)."""
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f == "img":
            continue
        p = os.path.join(OUT, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def main():
    nettoyer()
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    for f in sorted(os.listdir(DATA)):  # data/ publié tel quel (liens « data/… »)
        if f.endswith((".csv", ".json")):
            shutil.copy2(os.path.join(DATA, f), os.path.join(OUT, "data", f))
    gabarit.copier_theme()
    quand = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    sortie = archives_2023.main(quand)
    _, a_faire = methode.separer_decisions(sortie.get("decisions.html", ""))
    strategie.main(quand, a_faire)
    cour = saisons.courante()
    e = calc_saison.etat(cour)
    p_saison.rendre(e, "index.html", quand)
    journal.rendre(e, quand)
    methode.rendre(sortie, quand)
    arch = saisons.archivees()
    for s in arch:  # saisons de suivi terminées : tableau de bord figé
        if s["type"] == "suivi":
            p_saison.rendre(calc_saison.etat(s), f"archives/{s['id']}/index.html", quand)
    methode.archives(arch, quand)
    with open(os.path.join(OUT, "data", "saison_courante.json"), "w", encoding="utf-8") as f:
        json.dump(calc_saison.en_json(e), f, ensure_ascii=False, indent=1, default=str)
    red = gabarit.redirections()
    print(f"Site généré : {len(gabarit._ecrites)} pages, {len(red)} redirections ; saison {cour['id']}, jour {e['jour']}/{e['jours_total']}, "
          f"recommandation du jour : {e['reco'][1].get('raison')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Conserve la recommandation du jour dans data/recommandations_AAAA-AAAA.csv (une ligne par jour).

Appelé par le workflow du matin (cron et lancement manuel), après « preparer_donnees.py --maj » et avant la
génération du site ; le workflow commite ensuite ce seul fichier (un commit par jour, rien si la ligne existe déjà).
La première recommandation du jour fait foi : une reconstruction plus tard dans la journée (saisie, code) ne la
réécrit pas. --forcer remplace la ligne du jour (à éviter : l'historique doit montrer ce qui a été dit le matin).
Usage : python outils/enregistrer_recommandation.py [--forcer]
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chemins import DATA
from calculs import saison as calc_saison, saisons


def main(forcer=False):
    s = saisons.courante()
    e = calc_saison.etat(s)
    if e["terminee"] or e["aujourd_hui"] < calc_saison.dt.date.fromisoformat(s["debut"]):
        print("Hors saison : aucune recommandation enregistrée.")
        return
    p = os.path.join(DATA, calc_saison.fichier_reco(s))
    lignes = []
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as f:
            lignes = list(csv.DictReader(f))
    l = calc_saison.ligne_reco(e)
    deja = [x for x in lignes if x["date"] == l["date"]]
    if deja and not forcer:
        print(f"Recommandation du {l['date']} déjà enregistrée ({deja[0]['recommandation']}) : rien à faire.")
        return
    lignes = sorted([x for x in lignes if x["date"] != l["date"]] + [l], key=lambda x: x["date"])
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=calc_saison.COLS_RECO)
        w.writeheader()
        w.writerows(lignes)
    print(f"Recommandation du {l['date']} enregistrée : {l['recommandation']}"
          + (f", {l['buches']} bûches" if l["recommandation"] == "feu" else "") + f" (source : {l['source_meteo']}).")


if __name__ == "__main__":
    main("--forcer" in sys.argv)

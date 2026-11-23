"""Validation de la saisie de la saison courante (data/saisie_AAAA-AAAA.csv).

Erreurs : la publication est bloquée (le site reste à la version précédente).
Avertissements : affichés dans le Journal, la publication continue.
"""
import csv, os, datetime as dt
from chemins import DATA
from calculs.saisons import courante, aujourdhui

COLS = ["date", "buches", "kwh", "evenement_hq", "jour_temoin", "stock_compte", "remarque"]
OUINON = ("", "oui", "non", "o", "n", "1", "0", "x")


def valider(aujourd_hui=None):
    s = courante(); p = os.path.join(DATA, s["saisie"])
    erreurs, avert = [], []
    if not os.path.exists(p):
        return erreurs, avert
    aujourd_hui = aujourd_hui or aujourdhui()
    deb, fin = dt.date.fromisoformat(s["debut"]), dt.date.fromisoformat(s["fin"])
    with open(p, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        manque = [c for c in COLS if c not in (r.fieldnames or [])]
        if manque:
            return [f"colonnes manquantes : {', '.join(manque)}"], avert
        vus = set()
        for i, l in enumerate(r, start=2):
            ds = (l["date"] or "").strip()
            if not ds:
                continue
            ou = f"ligne {i} ({ds})"
            try:
                d = dt.date.fromisoformat(ds)
            except ValueError:
                erreurs.append(f"{ou} : date illisible (format AAAA-MM-JJ)"); continue
            if d in vus:
                erreurs.append(f"{ou} : date en double")
            vus.add(d)
            if d > aujourd_hui:
                erreurs.append(f"{ou} : date dans le futur")
            if not (deb <= d <= fin):
                avert.append(f"{ou} : hors de la saison ({s['debut']} → {s['fin']})")
            b = (l["buches"] or "").strip()
            try:
                bv = float(b) if b else 0.0
                if bv < 0:
                    erreurs.append(f"{ou} : nombre de bûches négatif")
                elif bv > 20:
                    avert.append(f"{ou} : {b} bûches, inhabituel (maximum observé : 15)")
            except ValueError:
                erreurs.append(f"{ou} : bûches « {b} » n'est pas un nombre")
            k = (l["kwh"] or "").strip()
            if k:
                try:
                    kv = float(k)
                    if not (15 <= kv <= 250):
                        avert.append(f"{ou} : {k} kWh, hors de la plage habituelle (15 à 250)")
                except ValueError:
                    erreurs.append(f"{ou} : kWh « {k} » n'est pas un nombre")
            for c in ("evenement_hq", "jour_temoin"):
                if (l[c] or "").strip().lower() not in OUINON:
                    erreurs.append(f"{ou} : {c} doit être oui ou non")
            sc = (l["stock_compte"] or "").strip()
            if sc:
                try:
                    if float(sc) < 0:
                        erreurs.append(f"{ou} : stock compté négatif")
                except ValueError:
                    erreurs.append(f"{ou} : stock compté « {sc} » n'est pas un nombre")
    return erreurs, avert


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    e, a = valider()
    print("\n".join(["ERREUR : " + x for x in e] + ["à vérifier : " + x for x in a]) or "Saisie valide.")

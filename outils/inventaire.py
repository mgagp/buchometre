#!/usr/bin/env python3
"""Inventaire de la pile de bois (mesures de Marc, 2026-11-22).

Lit data/inventaire_pile_2026-11.csv ; calcule surfaces de face, bûches (densité de face), cordes, fourchettes.
Bibliothèque standard seulement. Utilisé par protocole.py (stock initial) et generer_protocole.py (page inventaire).
"""
import csv, os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(RACINE, "data", "inventaire_pile_2026-11.csv")

P = {
    "date": "2026-11-22",
    "densite": 6.7,                 # bûches par pi² de face : « premier échantillon de référence » (origine non précisée) — HYPOTHÈSE À CONFIRMER
    "densite_bas": 6.0,             # sensibilité
    "densite_haut": 7.4,
    "buches_par_corde": 232,        # ratio du projet : 928 bûches projetées 2023-24 ÷ 4 cordes (fragile)
    "corde_face_pi2": 32.0,         # corde de face québécoise : 4 pi × 8 pi de face, bûches de 16 po
    "corde_pleine_pi3": 128.0,      # 4 × 4 × 8 pi
    "longueur_buche_po": 16,        # CONFIRMÉE par Marc le 2026-11-22
    "rangees": 1,                   # présumé : une seule rangée vue de face — À CONFIRMER
    "fourchette_retenue": (876, 947),  # sensibilité à la densité 6,7 → 7,25 b/pi² (232 b/corde)
}


def calculer():
    sec = []
    for r in csv.DictReader(open(FICHIER, encoding="utf-8")):
        l, h, n = float(r["largeur_po"]) / 12, float(r["hauteur_po"]) / 12, int(r["nombre"])
        su = l * h if r["forme"] == "rectangle" else l * h / 2
        s = su * n
        sec.append({**r, "largeur_pi": l, "hauteur_pi": h, "nombre": n, "surface_unitaire": su, "surface": s,
                    "buches": round(s * P["densite"]) * P["rangees"],
                    "buches_bas": round(s * P["densite_bas"]) * P["rangees"], "buches_haut": round(s * P["densite_haut"]) * P["rangees"]})
    surf = sum(s["surface"] for s in sec)
    tot = sum(s["buches"] for s in sec)  # somme des sections arrondies (comme dans la session) : 876
    d232 = P["buches_par_corde"] / P["corde_face_pi2"]
    return {
        "param": P, "sections": sec, "surface": surf, "buches": tot, "buches_exact": surf * P["densite"] * P["rangees"],
        "buches_bas": sum(s["buches_bas"] for s in sec), "buches_haut": sum(s["buches_haut"] for s in sec),
        "moins15": round(tot * 0.85), "plus15": round(tot * 1.15),
        "cordes_face": surf / P["corde_face_pi2"], "cordes_232": tot / P["buches_par_corde"],
        "buches_par_corde_implicite": P["densite"] * P["corde_face_pi2"],
        "densite_232": d232, "buches_selon_232": round(surf * d232 * P["rangees"]),
        "po2_par_buche": 144 / P["densite"], "cote_po": (144 / P["densite"]) ** 0.5,
        "volume_pi3": surf * P["longueur_buche_po"] / 12 * P["rangees"],
        "triangle_45_h": 3.0, "triangle_45_buches": round(2 * 6 * 3 / 2 * P["densite"]),
        "intermediaire_surface": sum(s["surface"] for s in sec[:2]), "intermediaire_buches": sum(s["buches"] for s in sec[:2]),
    }


if __name__ == "__main__":
    import json
    print(json.dumps({k: v for k, v in calculer().items() if k != "sections"}, indent=1, ensure_ascii=False, default=str))

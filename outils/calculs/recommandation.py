"""Recommandation du jour : faire un feu ou non, et combien de bûches (couche calculs, aucun HTML).

Applique la règle de budget du protocole (data/protocole.json → hypotheses) à la prévision météo et aux
événements Flex D annoncés par Hydro-Québec. Version 1 (étape 1) : approximation « jour cœur » = moyenne prévue ≤ seuil
dans la période critique (sans détection des creux sur la prévision). Étape 2 : version commune avec la routine du matin.
"""
import math, datetime as dt

MOIS = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def besoin_fenetre(dj, H, cdj):
    return 4 * H["facteur_pointe_horaire"] * cdj * dj / 24


def plafond(dj, H):
    return min(H["buches_max_jour"], round(H["buches_par_dj"] * dj), H["regle_max_coeur"])


def recommander(d, t, nevt, plages, stock, reserve, ecart_plan, P, saison):
    """Verdict pour un jour. Renvoie {feu: bool, buches: int, raison: str, regle: str}."""
    H = P["hypotheses"]; kb = P["kwh_par_buche"]; cdj = P["coef"][1]
    crit0, crit1 = dt.date.fromisoformat(P["critique"]["debut"]), dt.date.fromisoformat(P["critique"]["fin"])
    fx0, fx1 = (dt.date.fromisoformat(x) for x in saison["flex_d"])
    if t is None:
        return {"feu": None, "buches": 0, "raison": "prévision indisponible", "regle": ""}
    dj = max(18 - t, 0)
    # Règle 1 : événement annoncé → toujours
    if nevt and fx0 <= d <= fx1:
        par_evt = max(4, math.ceil(besoin_fenetre(dj, H, cdj) / (kb * H["part_buche_dans_fenetre"])))
        n = min(par_evt * nevt, int(stock))
        quand = " et ".join(plages) or "fenêtre annoncée"
        return {"feu": True, "buches": n, "regle": "1",
                "raison": f"événement Flex D annoncé ({quand}) : allumer 30 à 60 min avant, environ {par_evt} bûches par événement"}
    # Règle 5 : freinage si le stock passe plus de 50 bûches sous le plan
    frein = ecart_plan is not None and ecart_plan < -50
    if t <= H["regle_seuil_coeur"] and crit0 <= d <= crit1:
        v = plafond(dj, H)
        if frein:
            return {"feu": False, "buches": 0, "regle": "5", "raison": f"froid ({fmt(t)} °C), mais le stock est plus de 50 bûches sous le plan : événements seulement"}
        if stock - v >= reserve:
            return {"feu": True, "buches": v, "regle": "3", "raison": f"jour froid : moyenne prévue {fmt(t)} °C ≤ {fmt(H['regle_seuil_coeur'])} °C (jusqu'à {v} bûches)"}
        return {"feu": False, "buches": 0, "regle": "2", "raison": "froid, mais le feu entamerait la réserve pour les événements"}
    lib = dt.date(d.year, int(H["regle_liberation"][:2]), int(H["regle_liberation"][3:]))
    if d.month <= 3 and d >= lib and t <= 0 and not frein:
        v = plafond(dj, H)
        if v and stock - v >= reserve:
            return {"feu": True, "buches": v, "regle": "4", "raison": f"surplus libéré depuis le 1er janvier : moyenne prévue {fmt(t)} °C ≤ 0 °C (jusqu'à {v} bûches)"}
    raison = f"moyenne prévue {fmt(t)} °C, au-dessus du seuil de {fmt(H['regle_seuil_coeur'])} °C"
    if d < fx0:
        raison += f" ; la saison des événements Flex D commence le {fx0.day}{'er' if fx0.day == 1 else ''} {MOIS[fx0.month]}"
    elif not (crit0 <= d <= crit1):
        raison = f"hors période critique ; moyenne prévue {fmt(t)} °C"
    return {"feu": False, "buches": 0, "regle": "", "raison": raison}


def fmt(x):
    s = f"{x:.1f}".replace(".", ",").replace("-", "−")
    return s[:-2] if s.endswith(",0") else s

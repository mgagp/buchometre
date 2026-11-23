"""Règle de budget et recommandation du jour : la source canonique (couche calculs, aucun HTML).

Un seul endroit pour la règle :
  - decider()     : règles 1 à 5 du protocole pour un jour ; utilisée par la simulation (protocole.py), par le plan
                    recalculé sur la météo réelle et par la recommandation du jour (saison.py) ;
  - creux()       : détection des creux froids (anomalie de la moyenne sur 3 jours sous la médiane mobile de 31 jours),
                    la même pour l'analyse historique et pour la prévision ;
  - recommander() : le verdict lisible du jour (feu ou non, bûches, moment, raison) ;
  - plan_feu()    : les heures d'allumage, de dernière charge et de baisse (décision de Marc du 2026-11-23, issue #10) ;
                    il ne change ni la décision ni le nombre de bûches.
Les paramètres viennent de data/protocole.json → hypotheses (écrites par protocole.py).
"""
import math, datetime as dt

MOIS = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def fmt(x):
    s = f"{x:.1f}".replace(".", ",").replace("-", "−")
    return s[:-2] if s.endswith(",0") else s


def dfr(d):
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS[d.month]}"


def regles(H):
    """Paramètres en vigueur (règles assouplies du 2026-11-22)."""
    return {"seuil": H["regle_seuil_coeur"], "max": H["regle_max_coeur"], "liberation": H["regle_liberation"]}


def besoin_fenetre(dj, H, cdj):
    """kWh électriques de chauffage dans une fenêtre d'événement de 4 h."""
    return 4 * H["facteur_pointe_horaire"] * cdj * dj / 24


def buches_evt(dj, H, kb, cdj):
    """Bûches pour couvrir un événement (chaleur livrée à 70 % dans la fenêtre si le feu est allumé juste avant)."""
    return math.ceil(besoin_fenetre(dj, H, cdj) / (kb * H["part_buche_dans_fenetre"]))


def plafond(dj, H, maxi):
    return min(H["buches_max_jour"], round(H["buches_par_dj"] * dj), maxi)


def apres_liberation(d, lib):
    """Règle 4 : du 1er janvier (« 01-01 ») au 31 mars."""
    return d.strftime("%m-%d") >= lib and d.month <= 3


def decider(nevt, dj, t, coeur, dans_crit, apres_lib, stock, reserve, H, kb, cdj, rp=None, frein=False):
    """Règle de budget pour un jour → (bûches, règle appliquée).
    1 : événement annoncé → toujours ; 5 : plus de 50 bûches sous le plan → événements seulement ;
    3 : jour cœur d'un creux froid, T moy ≤ seuil, période critique → feu (≤ max) si le stock reste au-dessus de la réserve ;
    4 : surplus libéré dès le 1er janvier, T moy ≤ 0 °C, même condition de réserve ; 2 : feu refusé pour protéger la réserve."""
    rp = rp or regles(H)
    if nevt:
        return min(nevt * buches_evt(dj, H, kb, cdj), stock), "1"
    if frein:
        return 0, "5"
    if coeur and t <= rp["seuil"] and dans_crit:
        v = plafond(dj, H, rp["max"])
        return (v, "3") if stock - v >= reserve else (0, "2")
    if apres_lib and t <= 0:
        v = plafond(dj, H, rp["max"])
        return (v, "4") if stock - v >= reserve else (0, "2")
    return 0, ""


def creux(js, H):
    """js : jours consécutifs {t, anom, base}. Renvoie la liste des creux (listes de jours, ≥ 2 jours) :
    anomalie ≤ seuil_creux, un jour de répit toléré (anomalie ≤ 0). Marque chaque jour : j["coeur"] (T ≤ base + seuil_coeur)."""
    runs, run, trou = [], [], 0

    def fermer(r):
        if len(r) >= 2:
            for j in r:
                j["coeur"] = j["t"] <= j["base"] + H["seuil_coeur"]
            runs.append(r)
    for j in js:
        if j["anom"] <= H["seuil_creux"]:
            run.append(j); trou = 0
        elif run and trou == 0 and j["anom"] <= 0:
            trou = 1; run.append(j)
        else:
            if run and run[-1]["anom"] > H["seuil_creux"]:
                run.pop()
            fermer(run); run = []; trou = 0
    fermer(run)
    return runs


# Plan de feu (issue #10) : points de départ, à ajuster avec les retours de confort de Marc.
PLAN = {
    "chauffe_min": 90,        # un feu met ≈ 1 h 30 à atteindre sa température optimale : allumer 1 h 30 avant le moment visé
    "matin": "06:00",         # creux du petit matin et fenêtre Flex D de 6 h (moment visé)
    "allumage_tot": "06:00",  # heure d'allumage au plus tôt, réaliste pour Marc (cadran à 5 h 30) : prime sur la règle des 1 h 30
    "apres_midi": "16:00",    # fenêtre Flex D de 16 h et froid du soir → allumer vers 14 h 30
    "fin_matin": "10:00",     # fin de la fenêtre du matin : on laisse baisser ensuite
    "seuil_doux": -1.0,       # max prévu ≥ −1 °C : chaque feu plafonné à ≈ 4 h, puis on laisse baisser
    "plafond_h": 4,
    "reduire": "19:00",       # réduire la charge vers 19 h (sommeil, étage) …
    "nuit_froide": -10.0,     # … sauf si le min prévu de la nuit est ≤ −10 °C : dernière charge vers 21 h 30
    "charge_nuit": "21:30",
    "buches_nuit": 2,
}


def _hm(t):
    return t.strftime("%H:%M")


def _moins(hm, minutes):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) - dt.timedelta(minutes=minutes))


def _plus(hm, heures):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) + dt.timedelta(hours=heures))


def _plus_min(hm, minutes):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) + dt.timedelta(minutes=minutes))


def plan_feu(n, regle, plages, jour):
    """Heures du feu pour un jour où la règle en brûle n (le total ne change pas).
    jour : {tmax, tmin_nuit (min prévu de la nuit qui suit), creux_soir (le creux de cette nuit tombe avant minuit)}.
    → {feux: [{feu, allumer, derniere_charge, baisser, buches, vise}], doux, nuit_froide, creux_soir} ou None."""
    if not n:
        return None
    P = PLAN; j = jour or {}
    tmax, tnuit = j.get("tmax"), j.get("tmin_nuit")
    doux = tmax is not None and tmax >= P["seuil_doux"]
    froide = tnuit is not None and tnuit <= P["nuit_froide"]
    soir = bool(j.get("creux_soir"))
    feux = []
    if regle == "1" and plages:
        par = [n // len(plages) + (1 if i < n % len(plages) else 0) for i in range(len(plages))]
        for p, b in zip(plages, par):
            deb, fin = p.split("-")
            allumer = max(_moins(deb, P["chauffe_min"]), P["allumage_tot"])
            plein = _plus_min(allumer, P["chauffe_min"])
            dern = _moins(fin, 60)
            if doux:
                dern = min(dern, _plus(allumer, P["plafond_h"]))
            if deb >= "12:00" and not froide:
                dern = min(dern, P["reduire"])
            feux.append({"feu": f"événement {_h(deb)}-{_h(fin)}", "allumer": allumer, "derniere_charge": dern, "baisser": dern,
                         "buches": b, "vise": f"fenêtre Flex D {_h(deb)}-{_h(fin)}" + (f" ; pleine chaleur vers {_h(plein)}" if plein > deb else "")})
    else:
        n1 = round(n / 3) if soir else n // 2
        n2 = n - n1
        # nuit ≤ −10 °C : pas de réduction à 19 h, dernière charge vers 21 h 30 ; si la journée est douce (feu plafonné
        # à ≈ 4 h), cette charge de nuit est une petite relance à part
        nuit = min(P["buches_nuit"], n2 // 2) if froide and doux and n2 >= 4 else 0
        a1 = max(_moins(P["matin"], P["chauffe_min"]), P["allumage_tot"])
        a2 = max(_moins(P["apres_midi"], P["chauffe_min"]), P["allumage_tot"])
        d1 = min(_plus(a1, P["plafond_h"]), P["fin_matin"]) if doux else P["fin_matin"]
        d2 = min(_plus(a2, P["plafond_h"]), P["reduire"]) if doux else (P["charge_nuit"] if froide else P["reduire"])
        if n1:
            feux.append({"feu": "matin", "allumer": a1, "derniere_charge": d1, "baisser": d1, "buches": n1,
                         "vise": "creux du petit matin et fenêtre de 6 h"})
        feux.append({"feu": "après-midi et soir", "allumer": a2, "derniere_charge": d2, "baisser": d2,
                     "buches": n2 - nuit, "vise": "fenêtre de 16 h et froid du soir" + (" (creux prévu en soirée : priorité)" if soir else "")
                     + (f" ; nuit prévue à {fmt(tnuit)} °C : pas de réduction à 19 h" if froide and not doux else "")})
        if nuit:
            feux.append({"feu": "nuit froide", "allumer": P["charge_nuit"], "derniere_charge": P["charge_nuit"], "baisser": P["charge_nuit"],
                         "buches": nuit, "vise": f"nuit prévue à {fmt(tnuit)} °C"})
    return {"feux": feux, "doux": doux, "nuit_froide": froide, "creux_soir": soir}


def texte_plan(pl):
    """Plan → phrase courte (champ « moment »)."""
    if not pl:
        return ""
    out = []
    for f in pl["feux"]:
        if f["feu"] == "nuit froide":
            out.append(f"dernière charge vers {_h(f['allumer'])} (≈ {f['buches']} bûches, {f['vise']})")
            continue
        x = f"allumer vers {_h(f['allumer'])}" + (f" ({f['vise']})" if f["feu"].startswith("événement") else "")
        x += f", ≈ {f['buches']} bûches, dernière charge vers {_h(f['derniere_charge'])}"
        if f["feu"] == "après-midi et soir":
            relance = any(g["feu"] == "nuit froide" for g in pl["feux"])
            x += ("" if relance else ", puis réduire pour la nuit") if f["baisser"] <= PLAN["reduire"] else f" (nuit froide : pas de réduction à {_h(PLAN['reduire'])})"
        out.append(x)
    t = " ; puis ".join(out)
    if pl["doux"]:
        t += f" (max prévu ≥ {fmt(PLAN['seuil_doux'])} °C : ≈ {PLAN['plafond_h']} h de feu au plus, puis laisser baisser)"
    return t


def _h(hm):
    """« 06:00 » → « 6 h » ; « 05:30 » → « 5 h 30 »."""
    h, m = int(hm[:2]), int(hm[3:5])
    return f"{h} h" + (f" {m:02d}" if m else "")


def plage_fr(plage):
    """« 06:00-10:00 » → « 6 h-10 h »."""
    a, b = plage.split("-")
    return f"{_h(a)}-{_h(b)}"


def moment_evt(plage):
    """« 16:00-20:00 » → « vers 14 h 30 (événement 16 h-20 h) » : allumer 1 h 30 avant le début, pas avant
    PLAN["allumage_tot"] (« 06:00-10:00 » → « vers 6 h »)."""
    deb, fin = plage.split("-")
    return f"vers {_h(max(_moins(deb, PLAN['chauffe_min']), PLAN['allumage_tot']))} (événement {_h(deb)}-{_h(fin)})"


def recommander(d, jour, plages, stock, reserve, ecart_plan, P, saison, frein=False):
    """Verdict pour un jour.
    jour : {t, coeur, creux} (prévision et détection des creux), plus {tmax, tmin_nuit, creux_soir} pour le plan de feu,
           ou None si la prévision manque ;
    plages : événements Flex D annoncés ce jour (« 06:00-10:00 ») ; stock, reserve en bûches.
    Renvoie {feu: True|False|None, buches, regle, moment, plan, raison, evenement}."""
    H = P["hypotheses"]; kb = P["kwh_par_buche"]; cdj = P["coef"][1]; rp = regles(H)
    crit0, crit1 = (dt.date.fromisoformat(P["critique"][k]) for k in ("debut", "fin"))
    fx0, _ = (dt.date.fromisoformat(x) for x in saison["flex_d"])
    evt = " et ".join(plage_fr(p) for p in plages)
    t = jour["t"] if jour else None
    # Règle 1 en premier, même sans prévision (on prend alors la réserve par événement : 5 bûches)
    if plages:
        dj = max(18 - t, 0) if t is not None else None
        par = buches_evt(dj, H, kb, cdj) if dj is not None else H["regle_buches_evt"]
        n = min(par * len(plages), int(stock))
        pl = plan_feu(n, "1", plages, jour)
        return {"feu": True, "buches": n, "regle": "1", "moment": texte_plan(pl), "plan": pl, "evenement": evt,
                "raison": f"événement Flex D annoncé ({evt}) : environ {par} bûches par événement, allumées environ 1 h 30 avant (pas avant {_h(PLAN['allumage_tot'])})"
                          + ("" if t is not None else " (prévision indisponible : quantité par défaut)")}
    if t is None:
        return {"feu": None, "buches": 0, "regle": "", "moment": "", "plan": None, "evenement": "",
                "raison": "prévision indisponible (mode ouvert) : la règle n'est pas appliquée ; décider au jugé, un événement annoncé par Hydro-Québec reste prioritaire"}
    dj = max(18 - t, 0)
    dans_crit = crit0 <= d <= crit1
    n, regle = decider(0, dj, t, jour.get("coeur"), dans_crit, apres_liberation(d, rp["liberation"]), stock, reserve, H, kb, cdj, rp, frein)
    tt = f"{fmt(t)} °C"
    if regle == "3":
        r = f"jour cœur d'un creux froid : {tt} prévus, sous le seuil de {fmt(rp['seuil'])} °C (jusqu'à {n} bûches)"
    elif regle == "4":
        r = f"surplus libéré depuis le {dfr(dt.date(d.year, 1, 1))} : {tt} prévus, sous 0 °C (jusqu'à {n} bûches)"
    elif regle == "5":
        r = f"le stock est plus de 50 bûches sous le plan ({'+' if ecart_plan >= 0 else ''}{fmt(round(ecart_plan))}) : événements seulement jusqu'à revenir sur la courbe"
    elif regle == "2":
        r = f"jour froid ({tt}), mais un feu entamerait la réserve de {round(reserve)} bûches gardée pour les événements"
    elif not dans_crit and d < crit0:
        r = f"{tt} prévus ; avant la période critique ({dfr(crit0)} au {dfr(crit1)})"
    elif not dans_crit:
        r = f"{tt} prévus ; hors période critique, et au-dessus de 0 °C"
    elif jour.get("coeur"):
        r = f"jour cœur d'un creux froid, mais {tt} reste au-dessus du seuil de {fmt(rp['seuil'])} °C"
    elif jour.get("creux"):
        r = f"creux froid en cours, mais pas son cœur ({tt} prévus)"
    elif t <= rp["seuil"]:
        r = f"{tt} prévus, mais pas plus froid que la normale du moment : pas un jour cœur"
    else:
        r = f"{tt} prévus, au-dessus du seuil de {fmt(rp['seuil'])} °C"
    if regle in ("", "2", "5") and d < fx0:
        r += f" ; les événements Flex D commencent le {dfr(fx0)}"
    pl = plan_feu(n, regle, [], jour)
    return {"feu": n > 0, "buches": n, "regle": regle, "moment": texte_plan(pl), "plan": pl, "evenement": "", "raison": r}

"""Règle de budget et recommandation du jour : la source canonique (couche calculs, aucun HTML).

Un seul endroit pour la règle :
  - decider()     : règles 1 à 5 du protocole pour un jour ; utilisée par la simulation (protocole.py), par le plan
                    recalculé sur la météo réelle et par la recommandation du jour (saison.py) ;
  - creux()       : détection des creux froids (anomalie de la moyenne sur 3 jours sous la médiane mobile de 31 jours),
                    la même pour l'analyse historique et pour la prévision ;
  - recommander() : le verdict lisible du jour (feu ou non, bûches, moment, raison).
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


def _h(hm):
    """« 06:00 » → « 6 h » ; « 05:30 » → « 5 h 30 »."""
    h, m = int(hm[:2]), int(hm[3:5])
    return f"{h} h" + (f" {m:02d}" if m else "")


def plage_fr(plage):
    """« 06:00-10:00 » → « 6 h-10 h »."""
    a, b = plage.split("-")
    return f"{_h(a)}-{_h(b)}"


def moment_evt(plage):
    """« 06:00-10:00 » → « entre 5 h et 5 h 30 (événement 6 h-10 h) » : allumer 30 à 60 min avant le début."""
    deb, fin = plage.split("-")
    t0 = dt.datetime(2000, 1, 1, int(deb[:2]), int(deb[3:5]))
    a, b = (t0 - dt.timedelta(minutes=60)).strftime("%H:%M"), (t0 - dt.timedelta(minutes=30)).strftime("%H:%M")
    return f"entre {_h(a)} et {_h(b)} (événement {_h(deb)}-{_h(fin)})"


def recommander(d, jour, plages, stock, reserve, ecart_plan, P, saison, frein=False):
    """Verdict pour un jour.
    jour : {t, coeur, creux} (prévision et détection des creux) ou None si la prévision manque ;
    plages : événements Flex D annoncés ce jour (« 06:00-10:00 ») ; stock, reserve en bûches.
    Renvoie {feu: True|False|None, buches, regle, moment, raison, evenement}."""
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
        moment = " ; ".join(moment_evt(p) for p in plages)
        return {"feu": True, "buches": n, "regle": "1", "moment": f"allumer {moment}", "evenement": evt,
                "raison": f"événement Flex D annoncé ({evt}) : environ {par} bûches par événement, allumées 30 à 60 min avant"
                          + ("" if t is not None else " (prévision indisponible : quantité par défaut)")}
    if t is None:
        return {"feu": None, "buches": 0, "regle": "", "moment": "", "evenement": "",
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
    moment = "dès le matin, puis entretenir jusqu'au soir" if n else ""
    return {"feu": n > 0, "buches": n, "regle": regle, "moment": moment, "evenement": "", "raison": r}

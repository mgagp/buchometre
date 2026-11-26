"""Règle de budget et recommandation du jour : la source canonique (couche calculs, aucun HTML).

Un seul endroit pour la règle :
  - decider()     : règles 1 à 5 du protocole pour un jour ; utilisée par la simulation (protocole.py), par le plan
                    recalculé sur la météo réelle et par la recommandation du jour (saison.py) ;
  - creux()       : détection des creux froids (anomalie de la moyenne sur 3 jours sous la médiane mobile de 31 jours),
                    la même pour l'analyse historique et pour la prévision ;
  - recommander() : le verdict lisible du jour (feu ou non, bûches, moment, raison) ;
  - plan_feu()    : un seul feu continu : allumage, recharges et dernière charge (décisions de Marc du 2026-11-23,
                    issue #10, et du 2026-11-26) ;
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


def part_fenetre(plage, H):
    """Part de la chaleur d'une bûche livrée dans la fenêtre (décision de Marc du 2026-11-26) :
    événement de l'après-midi (16 h-20 h, feu allumé à 6 h et déjà à pleine chaleur) → part_buche_dans_fenetre (0,7) ;
    événement du matin (6 h-10 h, allumé à 6 h, pleine chaleur vers 7 h 30) → part_buche_dans_fenetre_matin (0,55).
    Plage inconnue (hiver simulé sans données HQ) : la valeur du matin, prudente (la plupart des événements Flex D
    tombent le matin)."""
    if plage and plage[:5] >= "12:00":
        return H["part_buche_dans_fenetre"]
    return H["part_buche_dans_fenetre_matin"]


def liste_plages(evts):
    """Événements d'un jour : un nombre (plages inconnues) ou une liste de plages « 06:00-10:00 »."""
    if isinstance(evts, (list, tuple)):
        return list(evts)
    return [None] * int(evts or 0)


def buches_evt(dj, H, kb, cdj, plage=None):
    """Bûches pour couvrir la fenêtre d'un seul événement (besoin de la fenêtre / chaleur livrée dans la fenêtre)."""
    return math.ceil(besoin_fenetre(dj, H, cdj) / (kb * part_fenetre(plage, H)))


def buches_jour_evt(evts, dj, H, kb, cdj):
    """Règle 1 (décision de Marc du 2026-11-26) : un jour d'événement est une journée de chauffe complète.
    Bûches = le plus grand de : besoin des fenêtres, plafond des règles 3 et 4 (0,45 × DJ, au plus regle_max_coeur)
    et plancher d'une journée complète (regle_plancher_evt) ; au plus buches_max_jour."""
    pl = liste_plages(evts)
    if not pl:
        return 0
    besoin = sum(buches_evt(dj, H, kb, cdj, p) for p in pl)
    return min(max(besoin, plafond(dj, H, H["regle_max_coeur"]), H["regle_plancher_evt"]), H["buches_max_jour"])


def kwh_dans_fenetres(kwh, evts, dj, H, cdj):
    """kWh évités pendant les fenêtres d'événement : chaque fenêtre reçoit sa part du feu du jour
    (× part_fenetre), plafonnée par son besoin."""
    pl = liste_plages(evts)
    if not pl:
        return 0.0
    b = besoin_fenetre(dj, H, cdj)
    return sum(min(b, kwh / len(pl) * part_fenetre(p, H)) for p in pl)


def plafond(dj, H, maxi):
    return min(H["buches_max_jour"], round(H["buches_par_dj"] * dj), maxi)


def apres_liberation(d, lib):
    """Règle 4 : du 1er janvier (« 01-01 ») au 31 mars."""
    return d.strftime("%m-%d") >= lib and d.month <= 3


def decider(nevt, dj, t, coeur, dans_crit, apres_lib, stock, reserve, H, kb, cdj, rp=None, frein=False):
    """Règle de budget pour un jour → (bûches, règle appliquée). nevt : nombre d'événements ou liste de leurs plages.
    1 : événement annoncé → toujours, journée de chauffe complète (buches_jour_evt) ; 5 : plus de 50 bûches sous le plan → événements seulement ;
    3 : jour cœur d'un creux froid, T moy ≤ seuil, période critique → feu (≤ max) si le stock reste au-dessus de la réserve ;
    4 : surplus libéré dès le 1er janvier, T moy ≤ 0 °C, même condition de réserve ; 2 : feu refusé pour protéger la réserve."""
    rp = rp or regles(H)
    if nevt:
        return min(buches_jour_evt(nevt, dj, H, kb, cdj), stock), "1"
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


# Plan de feu (issue #10 ; un seul feu continu depuis la décision de Marc du 2026-11-26) : points de départ,
# à ajuster avec les retours de confort de Marc.
PLAN = {
    "chauffe_min": 90,        # un feu met ≈ 1 h 30 à atteindre sa température optimale : allumer 1 h 30 avant le moment visé
    "matin": "06:00",         # creux du petit matin et fenêtre Flex D de 6 h (moment visé)
    "allumage_tot": "06:00",  # heure d'allumage au plus tôt, réaliste pour Marc (cadran à 5 h 30) : prime sur la règle des 1 h 30
    "seuil_doux": -1.0,       # max prévu ≥ −1 °C : signalé (champ « doux »), sans effet sur les heures
    "recharge_min": 120,      # un seul feu gardé vivant : recharger ≈ toutes les 2 h, jamais jusqu'aux braises
    "reduire": "19:00",       # dernière charge, puis réduire vers 19 h (sommeil, étage) …
    "nuit_froide": -10.0,     # … sauf si le min prévu de la nuit est ≤ −10 °C : dernière charge vers 21 h 30
    "charge_nuit": "21:30",
}


def _hm(t):
    return t.strftime("%H:%M")


def _moins(hm, minutes):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) - dt.timedelta(minutes=minutes))


def _plus(hm, heures):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) + dt.timedelta(hours=heures))


def _plus_min(hm, minutes):
    return _hm(dt.datetime(2000, 1, 1, int(hm[:2]), int(hm[3:5])) + dt.timedelta(minutes=minutes))


def _minutes(hm):
    return int(hm[:2]) * 60 + int(hm[3:5])


def _de_minutes(m):
    m = int(round(m / 15.0) * 15)
    return f"{m // 60:02d}:{m % 60:02d}"


def plan_feu(n, regle, plages, jour):
    """Heures du feu pour un jour où la règle en brûle n (le total ne change pas).
    Un seul feu continu, gardé vivant toute la journée par des recharges régulières (décision de Marc du 2026-11-26 :
    en 2023-24, le feu restait vivant toute la journée, jamais jusqu'aux braises entre deux fenêtres).
    Tout jour de feu s'allume à 6 h (PLAN["allumage_tot"]), même un jour où seul l'événement de 16 h est annoncé
    (décision de Marc du 2026-11-26 : un jour d'événement est une journée de chauffe complète).
    Dernière charge vers 19 h, ou vers 21 h 30 si la nuit qui suit est ≤ −10 °C ; les bûches sont réparties sur les recharges.
    jour : {tmax, tmin_nuit (min prévu de la nuit qui suit), creux_soir (le creux de cette nuit tombe avant minuit)}.
    → {feux: [{feu, allumer, derniere_charge, baisser, buches, vise, charges: [{heure, buches}]}], doux, nuit_froide, creux_soir}
    ou None. « feux » garde la forme d'une liste (un seul élément) pour les lecteurs de data/recommandation.json."""
    if not n:
        return None
    P = PLAN; j = jour or {}
    tmax, tnuit = j.get("tmax"), j.get("tmin_nuit")
    doux = tmax is not None and tmax >= P["seuil_doux"]
    froide = tnuit is not None and tnuit <= P["nuit_froide"]
    soir = bool(j.get("creux_soir"))
    plages = sorted(plages or [])
    matin = max(_moins(P["matin"], P["chauffe_min"]), P["allumage_tot"])
    allumer = matin
    if plages:
        vise = "journée complète ; fenêtre" + ("s" if len(plages) > 1 else "") + " Flex D " + " et ".join(plage_fr(p) for p in plages)
        if plages[0][:5] < "12:00":
            vise += f", pleine chaleur vers {_h(_plus_min(allumer, P['chauffe_min']))}"
    else:
        vise = "journée complète : creux du petit matin, puis froid du soir" + (", creux prévu en soirée" if soir else "")
    dern = P["charge_nuit"] if froide else P["reduire"]
    if plages:
        dern = max(dern, _moins(plages[-1].split("-")[1], 60))  # entretenir jusqu'à la fin de la dernière fenêtre
    if froide:
        vise += f" ; nuit prévue à {fmt(tnuit)} °C : pas de réduction à {_h(P['reduire'])}"
    t0, t1 = _minutes(allumer), _minutes(dern)
    m = max(1, min(n, math.ceil((t1 - t0) / P["recharge_min"]) + 1))
    heures = [_de_minutes(t0 + (t1 - t0) * i / (m - 1)) if m > 1 else allumer for i in range(m)]
    par = [n // m + (1 if i < n % m else 0) for i in range(m)]
    charges = [{"heure": h, "buches": b} for h, b in zip(heures, par)]
    feux = [{"feu": "feu continu", "allumer": allumer, "derniere_charge": heures[-1], "baisser": heures[-1], "buches": n,
             "vise": vise, "charges": charges}]
    return {"feux": feux, "doux": doux, "nuit_froide": froide, "creux_soir": soir}


def texte_plan(pl):
    """Plan → phrase courte (champ « moment »)."""
    if not pl:
        return ""
    f = pl["feux"][0]; ch = f["charges"]
    x = f"un seul feu gardé vivant : allumer vers {_h(f['allumer'])} ({f['vise']})"
    if len(ch) > 1:
        q = sorted({c["buches"] for c in ch[1:]})
        qt = f"{q[0]}" if len(q) == 1 else f"{q[0]} à {q[-1]}"
        x += f", ≈ {ch[0]['buches']} bûches à l'allumage, puis {qt} bûche{'s' if q[-1] > 1 else ''} toutes les ≈ {PLAN['recharge_min'] // 60} h"
        x += f" ; dernière charge vers {_h(f['derniere_charge'])}"
    x += f" (≈ {f['buches']} bûches en tout)"
    x += ", puis réduire pour la nuit" if f["derniere_charge"] <= PLAN["reduire"] else ""
    return x


def _h(hm):
    """« 06:00 » → « 6 h » ; « 05:30 » → « 5 h 30 »."""
    h, m = int(hm[:2]), int(hm[3:5])
    return f"{h} h" + (f" {m:02d}" if m else "")


def plage_fr(plage):
    """« 06:00-10:00 » → « 6 h-10 h »."""
    a, b = plage.split("-")
    return f"{_h(a)}-{_h(b)}"


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
    # Règle 1 en premier, même sans prévision (on prend alors le plancher d'une journée complète)
    if plages:
        dj = max(18 - t, 0) if t is not None else None
        n0 = buches_jour_evt(plages, dj, H, kb, cdj) if dj is not None else H["regle_plancher_evt"]
        n = min(n0, int(stock))
        pl = plan_feu(n, "1", plages, jour)
        fen = ((" ; la fenêtre seule en demande " if len(plages) == 1 else " ; les fenêtres seules en demandent ")
               + str(sum(buches_evt(dj, H, kb, cdj, p) for p in plages))) if dj is not None else ""
        return {"feu": True, "buches": n, "regle": "1", "moment": texte_plan(pl), "plan": pl, "evenement": evt,
                "raison": f"événement Flex D annoncé ({evt}) : journée de chauffe complète, environ {n} bûches{fen} ; "
                          f"un seul feu gardé vivant, allumé environ 1 h 30 avant (pas avant {_h(PLAN['allumage_tot'])})"
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

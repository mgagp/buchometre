#!/usr/bin/env python3
"""Analyse du protocole hiver 2026-2027 (appelé par preparer_donnees.py, ou seul).

Lit la météo observée (calculs/meteo.py), sources/hq_evenements_pointe.csv, data/modele.json,
data/saisie_2026-2027.csv ; écrit data/protocole.json, data/protocole_meteo_jours.csv, data/protocole_creux.csv,
data/protocole_simulation.csv, data/saisie_2026-2027_enrichie.csv.
Bibliothèque standard seulement.
"""
import csv, json, os, sys, math, statistics as st, datetime as dt
from chemins import RACINE
from calculs import inventaire
from calculs.saisons import courante
from calculs import recommandation as RG
SAISON = courante()
INV = inventaire.calculer()

S = lambda *p: os.path.join(RACINE, "sources", *p)
D = lambda *p: os.path.join(RACINE, "data", *p)
EST = dt.timezone(dt.timedelta(hours=-5))

# ---------------- hypothèses (toutes affichées dans les pages) ----------------
H = {
    "prix_bois_2023": 425.0,            # tout inclus (Marc, 2026-11-22)
    "cordes": 4,                        # « 4 cordes habituelles » : le chiffrier ne le précise pas (hypothèse)
    "hausse_par_corde": 25.0,           # Marc : +25 $ par corde depuis l'achat
    "buches_saison": 928,               # projection 2023-24 (méthode)
    "taxes": 0.14975,
    "tarif_D_2026": {"p1": 0.07065, "p2": 0.11142, "acces": 0.46154},
    "flex_D_2026": {"p1_hiver": 0.04886, "p2_hiver": 0.09103, "pointe": 0.46463, "acces": 0.46154,
                    "max_heures": 120, "duree_evt": 4, "max_evt_jour": 2},
    "credit_hivernal_2026": 0.58490,    # $/kWh effacé (option fermée aux nouveaux abonnés depuis le 2026-03-31)
    "part_buche_dans_fenetre": 0.70,    # part de la chaleur d'une bûche livrée dans la fenêtre de 4 h si allumée juste avant (hypothèse)
    "facteur_pointe_horaire": 1.25,     # besoin de chauffage aux heures 6-10 h / 16-20 h vs moyenne du jour (hypothèse)
    "buches_par_dj": 0.45,              # plafond « raisonnable » de bûches/jour = 0,45 × degrés-jours (≈ 9 à 20 DJ, 13 à 30 DJ)
    "buches_max_jour": 15,              # maximum observé en 2023-24
    "seuil_creux": -2.0,                # anomalie (°C) sous la médiane mobile 31 j pour former un creux
    "seuil_coeur": -3.0,                # jour « cœur » : T moy ≤ médiane mobile − 3 °C
    "seuil_evt_predit": -12.0,          # hiver sans données HQ : jour d'événement probable si T moy ≤ −12 °C
    # --- stock 2026-2027 : inventaire mesuré de la pile (révision du 2026-11-22, voir outils/inventaire.py) ---
    "stock_source": "inventaire de la pile du 2026-11-22 (mesures de Marc × 6,7 bûches/pi²)",
    "stock_ancien": 348,                # 1re estimation (2026-11-22 12 h 51) : ≈ 1,5 corde × 232 — remplacée
    "cordes_restantes_ancien": 1.5,
    "buches_par_corde": 232,            # dérivé : 928 bûches projetées / 4 cordes (2023-24) — fragile
    "prix_corde_remplacement": 131.25,  # 425 $ / 4 + 25 $
    "regle_buches_evt": 5,              # bûches réservées par événement attendu
    "regle_seuil_coeur": -5.0,          # révisé 2026-11-22 (stock 876) : feu un jour cœur si T moy prévue ≤ −5 °C (avant : −8 °C)
    "regle_max_coeur": 12,              # révisé : au plus 12 bûches un jour sans événement (avant : 10 ; plafond d'absorption 0,45 × DJ)
    "regle_liberation": "01-01",        # révisé : dès le 1er janv. (avant : 1er févr.) le surplus au-dessus de la réserve va à tout jour ≤ 0 °C
    "regle_ancienne": {"seuil": -8.0, "max": 10, "liberation": "02-01"},
    "evts_attendus": 23,                # moyenne Flex D 2024-25 (26) et 2025-26 (19)
}
HIVERS = {"2023-2024": 2023, "2024-2025": 2024, "2025-2026": 2025, "2026-2027": 2026}


def jdate(s):
    return dt.date.fromisoformat(s)


def charger_meteo():
    """Météo observée canonique (calculs/meteo.py : EC Ste-Anne-de-Bellevue 1, repli Trudeau, puis modèle) : date → {t, tmin, tmax}."""
    from calculs import meteo
    return {d: {"t": v["t"], "tmin": v["tmin"], "tmax": v["tmax"]} for d, v in meteo.observee().items()}


def charger_evenements():
    ev = {}
    p = S("hq_evenements_pointe.csv")
    if not os.path.exists(p):
        return ev
    for r in csv.DictReader(open(p, encoding="utf-8-sig"), delimiter=";"):
        if r["offre"] != "TPC-DPC":  # TPC-DPC = tarif Flex D (données ouvertes HQ)
            continue
        deb = dt.datetime.fromisoformat(r["datedebut"]).astimezone(EST)
        fin = dt.datetime.fromisoformat(r["datefin"]).astimezone(EST)
        ev.setdefault(deb.date(), []).append({"plage": r["plagehoraire"], "debut": deb.strftime("%H:%M"), "fin": fin.strftime("%H:%M"),
                                             "heures": round((fin - deb).total_seconds() / 3600, 1)})
    return ev


def hiver_de(d):
    y = d.year if d.month >= 7 else d.year - 1
    return f"{y}-{y + 1}"


def mediane_mobile(vals, k=15):
    out = []
    for i in range(len(vals)):
        fen = [v for v in vals[max(0, i - k):i + k + 1] if v is not None]
        out.append(st.median(fen) if fen else None)
    return out


def moyenne_mobile(vals, k=1):
    out = []
    for i in range(len(vals)):
        fen = [v for v in vals[max(0, i - k):i + k + 1] if v is not None]
        out.append(sum(fen) / len(fen) if fen else None)
    return out


def analyser(ecrire=True):
    MOD = json.load(open(D("modele.json"), encoding="utf-8"))
    c0, cdj, cb = MOD["modeles"]["principal"]["coef"]
    kb = -cb
    M = charger_meteo(); EV = charger_evenements()
    tx = 1 + H["taxes"]
    F = H["flex_D_2026"]; TD = H["tarif_D_2026"]

    # ---------- coûts du bois ----------
    prix_corde_2023 = H["prix_bois_2023"] / H["cordes"]
    prix_ref = (prix_corde_2023 + H["hausse_par_corde"]) * H["cordes"]
    buches_par_corde = H["buches_saison"] / H["cordes"]
    cout_buche = prix_ref / H["buches_saison"]
    val = {"tarif_D": kb * TD["p2"] * tx, "flex_hors_evt": kb * F["p2_hiver"] * tx, "flex_evt": kb * F["pointe"] * tx,
           "tarif_D_2023": kb * 0.10041 * tx}
    seuils = {k: prix_ref / v for k, v in val.items()}

    # ---------- jours météo par hiver (1er oct. → 30 avr.) ----------
    jours = []
    for nom, y in HIVERS.items():
        d0, d1 = dt.date(y, 10, 1), dt.date(y + 1, 4, 30)
        ds = [d0 + dt.timedelta(i) for i in range((d1 - d0).days + 1) if (d0 + dt.timedelta(i)) in M]
        if not ds:
            continue
        t = [M[d]["t"] for d in ds]
        s3 = moyenne_mobile(t, 1); base = mediane_mobile(t, 15)
        for i, d in enumerate(ds):
            jours.append({"hiver": nom, "date": d, "t": t[i], "tmin": M[d]["tmin"], "tmax": M[d]["tmax"], "s3": s3[i], "base": base[i],
                          "anom": s3[i] - base[i], "dj": max(18 - t[i], 0), "evt": len(EV.get(d, [])),
                          "evt_h": sum(e["heures"] for e in EV.get(d, []))})

    # ---------- climatologie et période critique ----------
    def jour_saison(d):
        return (d - dt.date(d.year if d.month >= 7 else d.year - 1, 10, 1)).days
    clim = {}
    complets = ["2023-2024", "2024-2025", "2025-2026"]
    for j in jours:
        if j["hiver"] in complets:
            clim.setdefault(jour_saison(j["date"]), []).append(j["t"])
    idx = sorted(clim)
    cm = [sum(clim[i]) / len(clim[i]) for i in idx]
    cl = moyenne_mobile(cm, 7)  # lissage 15 jours
    sous0 = [i for i, v in zip(idx, cl) if v <= 0]
    crit_deb, crit_fin = min(sous0), max(sous0)
    ref = dt.date(2026, 10, 1)
    to_date = lambda i: ref + dt.timedelta(i)
    crit = {"debut": to_date(crit_deb).isoformat(), "fin": to_date(crit_fin).isoformat(), "jours": crit_fin - crit_deb + 1}
    # part des DJ et des événements dans la période critique vs fenêtre de Marc (15 nov.-15 mars)
    def dans(j, a, b):
        i = jour_saison(j["date"]); return a <= i <= b
    marc = (jour_saison(dt.date(2026, 11, 15)), jour_saison(dt.date(2027, 3, 15)))
    tot_dj = sum(j["dj"] for j in jours if j["hiver"] in complets)
    evj = [j for j in jours if j["hiver"] in ("2024-2025", "2025-2026")]
    crit["part_dj"] = sum(j["dj"] for j in jours if j["hiver"] in complets and dans(j, crit_deb, crit_fin)) / tot_dj
    crit["part_evt"] = sum(j["evt"] for j in evj if dans(j, crit_deb, crit_fin)) / max(1, sum(j["evt"] for j in evj))
    crit["marc_part_dj"] = sum(j["dj"] for j in jours if j["hiver"] in complets and dans(j, *marc)) / tot_dj
    crit["marc_part_evt"] = sum(j["evt"] for j in evj if dans(j, *marc)) / max(1, sum(j["evt"] for j in evj))
    clim_serie = [{"date": to_date(i).isoformat(), "t_moy3": round(v, 2), "t_lisse": round(l, 2)} for i, v, l in zip(idx, cm, cl)]

    # ---------- creux (systèmes froids) ----------
    creux = []
    for nom in HIVERS:
        js = [j for j in jours if j["hiver"] == nom and dans(j, crit_deb - 14, crit_fin + 14)]
        for run in RG.creux(js, H):  # même détection que pour la prévision (calculs/recommandation.py)
            cid = f"{nom[:4]}-{len([c for c in creux if c['hiver'] == nom]) + 1:02d}"
            coeur = [j for j in run if j["coeur"]]
            for j in run:
                j["creux"] = cid
            jm = min(run, key=lambda j: j["t"])
            creux.append({"id": cid, "hiver": nom, "debut": run[0]["date"].isoformat(), "fin": run[-1]["date"].isoformat(),
                          "jours": len(run), "jours_coeur": len(coeur), "t_min_jour": round(jm["t"], 1), "date_min": jm["date"].isoformat(),
                          "t_moy": round(sum(j["t"] for j in run) / len(run), 1), "dj": round(sum(j["dj"] for j in run), 1),
                          "evt": sum(j["evt"] for j in run), "dans_critique": any(dans(j, crit_deb, crit_fin) for j in run)})
    stats_creux = {}
    for nom in HIVERS:
        cs = [c for c in creux if c["hiver"] == nom and c["dans_critique"]]
        if not cs:
            continue
        mins = [jdate(c["date_min"]) for c in cs]
        ecarts = [(b - a).days for a, b in zip(mins, mins[1:])]
        stats_creux[nom] = {"n": len(cs), "jours_med": st.median(c["jours"] for c in cs), "coeur_med": st.median(c["jours_coeur"] for c in cs),
                            "jours_tot": sum(c["jours"] for c in cs), "coeur_tot": sum(c["jours_coeur"] for c in cs),
                            "cycle_med": st.median(ecarts) if ecarts else None,
                            "evt_dans_creux": sum(c["evt"] for c in cs),
                            "evt_tot": sum(j["evt"] for j in jours if j["hiver"] == nom),
                            "complet": nom in complets}

    # ---------- probabilité d'événement selon la température ----------
    bins = [(-99, -15), (-15, -12), (-12, -9), (-9, -6), (-6, -3), (-3, 99)]
    proba = []
    hiver_hq = [j for j in jours if j["hiver"] in ("2024-2025", "2025-2026") and (j["date"].month in (12, 1, 2, 3))]
    for a, b in bins:
        js = [j for j in hiver_hq if a < j["t"] <= b]
        e = sum(1 for j in js if j["evt"])
        proba.append({"de": a, "a": b, "jours": len(js), "jours_evt": e, "p": e / len(js) if js else 0})

    # ---------- simulation ----------
    def besoin_fenetre(dj):
        return 4 * H["facteur_pointe_horaire"] * cdj * dj / 24  # kWh électriques de chauffage dans une fenêtre de 4 h

    def plafond(dj):
        return min(H["buches_max_jour"], round(H["buches_par_dj"] * dj))

    sims, resume = [], {}
    for nom in complets:
        y = HIVERS[nom]
        js = [j for j in jours if j["hiver"] == nom and dt.date(y, 11, 7) <= j["date"] <= dt.date(y + 1, 3, 31)]
        reel = nom != "2023-2024"
        for j in js:
            if reel:
                j["nevt"] = j["evt"] if dt.date(y, 12, 1) <= j["date"] <= dt.date(y + 1, 3, 31) else 0
            else:
                j["nevt"] = 1 if (j["t"] <= H["seuil_evt_predit"] and j["date"].month in (12, 1, 2, 3)) else 0
        sdj = sum(j["dj"] for j in js)
        B = H["buches_saison"]
        strat = {}
        # Q : quotidien (comme 2023-24) : bûches proportionnelles aux degrés-jours, chaque jour
        q = {j["date"]: B * j["dj"] / sdj for j in js}
        # C : ciblé
        c = {j["date"]: 0.0 for j in js}
        reste = B
        evts = sorted([j for j in js if j["nevt"]], key=lambda j: -j["dj"])
        for j in evts:
            need = math.ceil(j["nevt"] * besoin_fenetre(j["dj"]) / (kb * H["part_buche_dans_fenetre"]))
            n = min(max(need, plafond(j["dj"])), reste); c[j["date"]] = n; reste -= n
        cands = sorted([j for j in js if not j["nevt"] and j.get("creux") and dans(j, crit_deb, crit_fin)], key=lambda j: (-int(j.get("coeur", False)), -j["dj"]))
        for j in cands:
            n = min(plafond(j["dj"]), reste); c[j["date"]] = n; reste -= n
        autres = sorted([j for j in js if not c[j["date"]] and j["t"] <= 0], key=lambda j: -j["dj"])
        for j in autres:
            n = min(plafond(j["dj"]), reste); c[j["date"]] = n; reste -= n
        for nomS, plan in (("quotidien", q), ("cible", c)):
            tot = {"buches": 0, "kwh": 0, "base": 0, "prime": 0, "prime_kwh": 0, "tarifD": 0, "jours_feu": 0, "evt_couverts": 0, "evt": 0}
            for j in js:
                b = plan[j["date"]]
                kwh = kb * b
                besoin = j["nevt"] * besoin_fenetre(j["dj"])
                if nomS == "cible":
                    dans_f = min(besoin, kwh * H["part_buche_dans_fenetre"])
                else:
                    dans_f = min(besoin, kwh * 4 * j["nevt"] / 24)
                base = kwh * F["p2_hiver"] * tx
                prime = dans_f * (F["pointe"] - F["p2_hiver"]) * tx
                tot["buches"] += b; tot["kwh"] += kwh; tot["base"] += base; tot["prime"] += prime; tot["prime_kwh"] += dans_f
                tot["tarifD"] += kwh * TD["p2"] * tx; tot["jours_feu"] += b > 0.5; tot["evt"] += j["nevt"]
                tot["evt_couverts"] += (j["nevt"] if besoin and dans_f >= 0.95 * besoin else 0)
                sims.append({"hiver_meteo": nom, "strategie": nomS, "date_meteo": j["date"].isoformat(),
                             "date_2026_2027": (j["date"].replace(year=j["date"].year + (2026 - y))).isoformat() if not (j["date"].month == 2 and j["date"].day == 29) else "",
                             "t_moy": j["t"], "dj18": round(j["dj"], 1), "creux": j.get("creux", ""), "coeur": int(j.get("coeur", False)),
                             "evenements": j["nevt"], "evt_reels": int(reel), "buches": round(b, 2), "kwh_evites": round(kwh, 1),
                             "kwh_evites_pointe": round(dans_f, 2), "kwh_sans_feu": round(c0 + cdj * j["dj"], 1),
                             "kwh_avec_feu": round(c0 + cdj * j["dj"] - kwh, 1), "valeur_base": round(base, 2), "valeur_pointe": round(prime, 2)})
            tot["valeur"] = tot["base"] + tot["prime"]
            tot["reste"] = B - tot["buches"]
            strat[nomS] = {k: round(v, 2) for k, v in tot.items()}
        resume[nom] = {"dj_saison": round(sdj), "strategies": strat, "evts_reels": reel}

    # ---------- stock limité 2026-2027 ----------
    stock0 = INV["buches"]
    # part cumulée des événements après chaque jour de saison (2024-25 et 2025-26)
    evs = sorted(jour_saison(j["date"]) for j in jours if j["hiver"] in ("2024-2025", "2025-2026") for _ in range(j["evt"]))
    def part_apres(i):
        return sum(1 for x in evs if x > i) / len(evs)
    mois_evt = {}
    for j in jours:
        if j["hiver"] in ("2024-2025", "2025-2026") and j["evt"]:
            mois_evt[j["date"].month] = mois_evt.get(j["date"].month, 0) + j["evt"] / 2
    def n_evt_jour(j):
        return sum(math.ceil(besoin_fenetre(j["dj"]) / (kb * H["part_buche_dans_fenetre"])) for _ in range(j["nevt"]))
    def evaluer(js, plan):
        tot = {"buches": 0, "base": 0, "prime": 0, "prime_kwh": 0, "jours_feu": 0, "jours_evt": 0, "evt": 0, "evt_couverts": 0, "par_mois": {}}
        for j in js:
            b = plan.get(j["date"], 0); kwh = kb * b
            besoin = j["nevt"] * besoin_fenetre(j["dj"])
            dans_f = min(besoin, kwh * H["part_buche_dans_fenetre"])
            tot["buches"] += b; tot["base"] += kwh * F["p2_hiver"] * tx; tot["prime"] += dans_f * (F["pointe"] - F["p2_hiver"]) * tx
            tot["prime_kwh"] += dans_f; tot["jours_feu"] += b > 0; tot["evt"] += j["nevt"]; tot["jours_evt"] += (j["nevt"] > 0 and b > 0)
            tot["evt_couverts"] += j["nevt"] if (besoin and dans_f >= 0.95 * besoin) else 0
            k = j["date"].strftime("%m"); tot["par_mois"][k] = tot["par_mois"].get(k, 0) + b
        tot["valeur"] = tot["base"] + tot["prime"]
        return tot
    def regle(js, stock, rp=None):
        rp = rp or {"seuil": H["regle_seuil_coeur"], "max": H["regle_max_coeur"], "liberation": H["regle_liberation"]}
        plan, st_, courbe = {}, stock, []
        for j in js:
            reserve = H["regle_buches_evt"] * H["evts_attendus"] * part_apres(jour_saison(j["date"]))
            # règle de budget canonique (calculs/recommandation.py)
            n, _ = RG.decider(j["nevt"], j["dj"], j["t"], j.get("coeur"), dans(j, crit_deb, crit_fin),
                              RG.apres_liberation(j["date"], rp["liberation"]), st_, reserve, H, kb, cdj, rp)
            plan[j["date"]] = n; st_ -= n
            courbe.append((j["date"].isoformat(), round(st_), round(reserve)))
        return plan, courbe
    def optimal(js, stock):
        plan, st_ = {}, stock
        for j in sorted([j for j in js if j["nevt"]], key=lambda j: -j["dj"]):
            n = min(n_evt_jour(j), st_); plan[j["date"]] = n; st_ -= n
        for j in sorted([j for j in js if not j["nevt"] and j["t"] <= 0], key=lambda j: (-int(bool(j.get("coeur"))), -j["dj"])):
            if st_ <= 0:
                break
            n = min(plafond(j["dj"]), H["regle_max_coeur"], st_); plan[j["date"]] = n; st_ -= n
        return plan
    def quotidien(js, stock):
        sdj = sum(j["dj"] for j in js)
        return {j["date"]: stock * j["dj"] / sdj for j in js}
    stock_res, courbes_stock, sims_stock = {}, {}, []
    for nom in complets:
        y = HIVERS[nom]
        js = [j for j in jours if j["hiver"] == nom and dt.date(y, 11, 7) <= j["date"] <= dt.date(y + 1, 3, 31)]
        r = {}
        for lab, B in (("stock", stock0), ("stock_plus_corde", stock0 + H["buches_par_corde"]), ("stock_bas", INV["buches_bas"]), ("stock_haut", INV["buches_haut"]),
                       ("stock_ancien", H["stock_ancien"])):
            pr, cr = regle(js, B)
            for nomS, plan in (("regle", pr), ("optimal", optimal(js, B)), ("quotidien", quotidien(js, B))):
                t = evaluer(js, plan); t["reste"] = B - t["buches"]; t["stock_initial"] = B
                r[f"{nomS}_{lab}"] = {k: (round(v, 2) if not isinstance(v, dict) else {kk: round(vv) for kk, vv in v.items()}) for k, v in t.items()}
            if lab == "stock":
                courbes_stock[nom] = cr
                stk = B
                for j in js:
                    b = pr.get(j["date"], 0); stk -= b
                    kwh = kb * b; besoin = j["nevt"] * besoin_fenetre(j["dj"]); dans_f = min(besoin, kwh * H["part_buche_dans_fenetre"])
                    if j["date"].month == 2 and j["date"].day == 29:
                        continue
                    sims_stock.append({"hiver_meteo": nom, "date_2026_2027": j["date"].replace(year=j["date"].year + (2026 - y)).isoformat(),
                                       "t_moy": j["t"], "dj18": round(j["dj"], 1), "creux": j.get("creux", ""), "coeur": int(bool(j.get("coeur"))),
                                       "evenements": j["nevt"], "buches": b, "stock_restant": stk, "reserve_evt": dict((d, rv) for d, _, rv in cr)[j["date"].isoformat()],
                                       "kwh_evites": round(kwh, 1), "kwh_evites_pointe": round(dans_f, 2), "kwh_sans_feu": round(c0 + cdj * j["dj"], 1),
                                       "kwh_avec_feu": round(c0 + cdj * j["dj"] - kwh, 1), "valeur_base": round(kwh * F["p2_hiver"] * tx, 2),
                                       "valeur_pointe": round(dans_f * (F["pointe"] - F["p2_hiver"]) * tx, 2)})
        # comparaison : ancienne règle (−8 °C, 10 bûches, 1er févr.) avec l'ancien stock (348) et avec l'inventaire
        for lab, B in (("ancien_ancienne_regle", H["stock_ancien"]), ("stock_ancienne_regle", stock0)):
            pr, _ = regle(js, B, H["regle_ancienne"])
            t = evaluer(js, pr); t["reste"] = B - t["buches"]; t["stock_initial"] = B
            r[lab] = {k: (round(v, 2) if not isinstance(v, dict) else {kk: round(vv) for kk, vv in v.items()}) for k, v in t.items()}
        stock_res[nom] = r
    stock = {"buches": stock0, "cordes": stock0 / H["buches_par_corde"], "valeur_remplacement": stock0 / H["buches_par_corde"] * H["prix_corde_remplacement"],
             "inventaire": {k: v for k, v in INV.items() if k != "sections"}, "resultats": stock_res,
             "courbes": courbes_stock, "evts_par_mois_moyen": mois_evt,
             "buches_par_evt_typ": [n_evt_jour({"nevt": 1, "dj": dj}) for dj in (24, 28, 32, 36)]}

    # courbe « part des bûches → part du gain » (stratégie ciblée)
    courbes = {}
    for nom in complets:
        rows = [s for s in sims if s["hiver_meteo"] == nom and s["strategie"] == "cible" and s["buches"] > 0]
        par = []
        for s in rows:
            v = (s["valeur_base"] + s["valeur_pointe"]) / s["buches"]
            par.append((v, s["buches"]))
        par.sort(key=lambda x: -x[0])
        tb = sum(b for _, b in par); tv = sum(v * b for v, b in par); cb_, cv = 0, 0; pts = [(0, 0)]
        for v, b in par:
            cb_ += b; cv += v * b; pts.append((cb_ / tb, cv / tv))
        courbes[nom] = pts

    # ---------- saisie 2026-2027 ----------
    saisie = []
    p = D(SAISON["saisie"])
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            if not (r.get("date") or "").strip():
                continue
            d = jdate(r["date"].strip())
            m = M.get(d)
            b = float(r.get("buches") or 0)
            kwh = float(r["kwh"]) if (r.get("kwh") or "").strip() else None
            t = m["t"] if m else None
            djv = max(18 - t, 0) if t is not None else None
            att = (c0 + cdj * djv - kb * b) if djv is not None else None
            evh = (r.get("evenement_hq") or "").strip().lower() in ("oui", "o", "1", "x", "yes")
            evo = len(EV.get(d, []))
            sc = (r.get("stock_compte") or "").strip()
            saisie.append({"date": d.isoformat(), "buches": b, "stock_compte": sc, "kwh": kwh, "evenement_hq_saisi": int(evh), "evenements_hq_donnees": evo,
                           "jour_temoin": int((r.get("jour_temoin") or "").strip().lower() in ("oui", "o", "1", "x", "yes")),
                           "remarque": r.get("remarque", ""), "t_moy": t, "dj18": round(djv, 1) if djv is not None else "",
                           "kwh_attendu_modele": round(att, 1) if att is not None else "", "kwh_sans_feu_modele": round(c0 + cdj * djv, 1) if djv is not None else "",
                           "kwh_evites_modele": round(kb * b, 1), "valeur_base": round(kb * b * F["p2_hiver"] * tx, 2),
                           "ecart_kwh": round(kwh - att, 1) if (kwh is not None and att is not None) else ""})
    else:
        with open(p, "w", newline="", encoding="utf-8") as fo:
            csv.writer(fo).writerow(["date", "buches", "kwh", "evenement_hq", "jour_temoin", "stock_compte", "remarque"])
    # stock restant réel : stock initial − bûches cumulées ; « stock_compte » (recomptage) remplace le calcul ce jour-là
    saisie.sort(key=lambda r: r["date"])
    stk = INV["buches"]  # stock de départ = inventaire mesuré (paramètre daté), pas une ligne de saisie
    for r in saisie:
        if r["stock_compte"]:
            stk = float(r["stock_compte"])
        else:
            stk -= r["buches"]
        r["stock_restant"] = round(stk)

    # ---------- test : le rendement par bûche dépend-il du froid ? (interaction bûches × DJ, données 2023-24) ----------
    from calculs.preparer_donnees import mco
    jn = [r for r in csv.DictReader(open(D("journal_nettoye.csv"), encoding="utf-8")) if r["statut"] == "mesure"]
    inter = mco([[1, float(r["dj18"]), float(r["nb_buches"]), float(r["nb_buches"]) * float(r["dj18"])] for r in jn], [float(r["kwh_reel"]) for r in jn])
    inter["kwh_par_buche_selon_dj"] = {str(x): -(inter["coef"][2] + inter["coef"][3] * x) for x in (10, 15, 20, 25, 30, 35)}

    out = {"hypotheses": H, "interaction": inter, "kwh_par_buche": kb, "coef": [c0, cdj, cb], "prix_corde_2023": prix_corde_2023, "prix_ref": prix_ref,
           "buches_par_corde": buches_par_corde, "cout_buche": cout_buche, "valeur_buche": val, "seuils": seuils,
           "critique": crit, "climatologie": clim_serie, "stats_creux": stats_creux, "proba_evt": proba, "resume_sim": resume,
           "courbes": courbes, "stock": stock, "meteo_derniere_date": max(M).isoformat(),
           "evts_par_hiver": {h: {"jours": sum(1 for j in jours if j["hiver"] == h and j["evt"]), "evenements": sum(j["evt"] for j in jours if j["hiver"] == h),
                                  "heures": sum(j["evt_h"] for j in jours if j["hiver"] == h)} for h in ("2024-2025", "2025-2026", "2026-2027")},
           "n_saisie": len(saisie)}
    if ecrire:
        json.dump(out, open(D("protocole.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        with open(D("protocole_meteo_jours.csv"), "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo); w.writerow(["hiver", "date", "t_moy", "t_min", "t_max", "t_lisse_3j", "mediane_31j", "anomalie", "dj18", "creux", "coeur", "evenements_flexd", "heures_evt"])
            for j in jours:
                w.writerow([j["hiver"], j["date"], j["t"], j["tmin"], j["tmax"], round(j["s3"], 2), round(j["base"], 2), round(j["anom"], 2), round(j["dj"], 1),
                            j.get("creux", ""), int(j.get("coeur", False)), j["evt"], j["evt_h"]])
        with open(D("protocole_creux.csv"), "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, list(creux[0].keys())); w.writeheader(); w.writerows(creux)
        with open(D("protocole_simulation_stock.csv"), "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, list(sims_stock[0].keys())); w.writeheader(); w.writerows(sims_stock)
        with open(D("protocole_simulation.csv"), "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, list(sims[0].keys())); w.writeheader(); w.writerows(sims)
        cols = ["date", "buches", "stock_compte", "stock_restant", "kwh", "evenement_hq_saisi", "evenements_hq_donnees", "jour_temoin", "remarque", "t_moy", "dj18",
                "kwh_attendu_modele", "kwh_sans_feu_modele", "kwh_evites_modele", "valeur_base", "ecart_kwh"]
        with open(D(SAISON["saisie_enrichie"]), "w", newline="", encoding="utf-8") as fo:
            w = csv.DictWriter(fo, cols); w.writeheader(); w.writerows(saisie)
    return out


if __name__ == "__main__":
    o = analyser()
    print(json.dumps({k: o[k] for k in ("prix_ref", "cout_buche", "valeur_buche", "seuils", "critique", "stats_creux", "proba_evt", "evts_par_hiver")}, indent=1, default=str))
    for h, r in o["resume_sim"].items():
        print(h, r["dj_saison"], r["strategies"])

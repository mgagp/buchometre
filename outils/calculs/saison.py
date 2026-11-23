"""État de la saison à une date (couche calculs, aucun HTML).

Réunit : saisie enrichie, plan (simulation à stock limité, météo de référence), météo réelle et prévision,
événements Flex D (données ouvertes HQ), règles du protocole. Utilisé par les pages Saison et Journal ;
exporté tel quel dans rapports/data/saison_courante.json.
"""
import csv, json, os, datetime as dt
from chemins import DATA, SOURCES
from calculs import protocole
from calculs.recommandation import recommander

J = dt.timedelta(days=1)


def _lire(nom):
    p = os.path.join(DATA, nom)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x):
    return float(x) if x not in ("", None) else None


def prevision():
    """Prévision Open-Meteo (sources/prevision_open-meteo.json, écrite par --maj) : date → {t, tmin, tmax}."""
    p = os.path.join(SOURCES, "prevision_open-meteo.json")
    if not os.path.exists(p):
        return {}, None
    o = json.load(open(p, encoding="utf-8")); d = o["daily"]
    out = {}
    for i, t in enumerate(d["time"]):
        if d["temperature_2m_mean"][i] is not None:
            out[dt.date.fromisoformat(t)] = {"t": d["temperature_2m_mean"][i], "tmin": d["temperature_2m_min"][i], "tmax": d["temperature_2m_max"][i]}
    return out, dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")


def statut_maj():
    p = os.path.join(SOURCES, "maj_statut.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def etat(saison, aujourd_hui=None):
    P = json.load(open(os.path.join(DATA, "protocole.json"), encoding="utf-8"))
    deb, fin = dt.date.fromisoformat(saison["debut"]), dt.date.fromisoformat(saison["fin"])
    vrai_auj = aujourd_hui or dt.date.today()
    terminee = vrai_auj > fin
    auj = min(vrai_auj, fin)
    stock0 = P["stock"]["buches"]; date_inv = dt.date.fromisoformat(P["stock"]["inventaire"]["param"]["date"])
    hv = saison["plan_meteo"]

    # ---- plan (simulation, règle de budget) : météo de référence + fourchette sur les 3 météos ----
    SS = _lire("protocole_simulation_stock.csv")
    par_meteo = {}
    for r in SS:
        if not r["date_2026_2027"]:
            continue
        d = dt.date.fromisoformat(r["date_2026_2027"])
        par_meteo.setdefault(r["hiver_meteo"], {})[d] = {"stock": float(r["stock_restant"]), "reserve": float(r["reserve_evt"]),
                                                        "buches": float(r["buches"]), "kwh": float(r["kwh_evites"]),
                                                        "base": float(r["valeur_base"]), "prime": float(r["valeur_pointe"])}
    plan = par_meteo.get(hv, {})
    dates_plan = sorted(plan)

    def plan_a(d):
        prev = [x for x in dates_plan if x <= d]
        if not prev:
            return {"stock": stock0, "reserve": plan[dates_plan[0]]["reserve"] if dates_plan else 0}
        return plan[prev[-1]]

    def cumul(pl, jusqu_a=None):
        rows = [v for d, v in pl.items() if jusqu_a is None or d <= jusqu_a]
        return {"buches": sum(v["buches"] for v in rows), "kwh": sum(v["kwh"] for v in rows),
                "base": sum(v["base"] for v in rows), "prime": sum(v["prime"] for v in rows)}
    plan_saison = cumul(plan); plan_date = cumul(plan, auj)
    # fourchette de la valeur totale (avec prime) sur les 3 météos : mêmes chiffres que la page Stratégie
    res = [v["regle_stock"] for v in P["stock"]["resultats"].values() if "regle_stock" in v]
    fourchette = {"base": (min(r["valeur"] for r in res), max(r["valeur"] for r in res)),
                  "buches": (min(r["buches"] for r in res), max(r["buches"] for r in res))} if res else {}

    # ---- saisie ----
    SA = _lire(saison["saisie_enrichie"])
    sai = {}
    for r in SA:
        d = dt.date.fromisoformat(r["date"])
        sai[d] = {"date": r["date"], "buches": _f(r["buches"]) or 0, "kwh": _f(r["kwh"]), "stock": _f(r["stock_restant"]),
                  "compte": bool(r["stock_compte"]), "evt_saisi": r["evenement_hq_saisi"] == "1", "temoin": r["jour_temoin"] == "1",
                  "remarque": r["remarque"], "t": _f(r["t_moy"]), "attendu": _f(r["kwh_attendu_modele"]), "ecart": _f(r["ecart_kwh"]),
                  "kwh_evites": _f(r["kwh_evites_modele"]) or 0, "valeur": _f(r["valeur_base"]) or 0}
    jours_saisis = sorted(sai)
    reel = {"buches": sum(v["buches"] for v in sai.values()), "kwh": sum(v["kwh_evites"] for v in sai.values()),
            "base": sum(v["valeur"] for v in sai.values())}
    stock = sai[jours_saisis[-1]]["stock"] if jours_saisis else stock0
    p_auj = plan_a(auj)
    ecart_plan = stock - p_auj["stock"]

    # ---- suivi : jours manquants (à partir du 1er déc., ou de la 1re saisie si plus tôt) ----
    debut_suivi = dt.date.fromisoformat(saison["debut_suivi"])
    if jours_saisis:
        debut_suivi = min(debut_suivi, jours_saisis[0])
    manquants = []
    d = debut_suivi
    while d < auj or (terminee and d <= fin):
        if d not in sai:
            manquants.append(d)
        d += J
    kwh_attente = [d for d in jours_saisis if sai[d]["kwh"] is None]

    # ---- météo réelle et prévision ----
    M = protocole.charger_meteo()
    PV, pv_quand = prevision()

    def temp(d):
        if d in M and d < vrai_auj:
            return M[d]["t"], False
        if d in PV:
            return PV[d]["t"], d >= vrai_auj
        if d in M:
            return M[d]["t"], False
        return None, False

    # ---- événements Flex D de la saison ----
    EV = {d: v for d, v in protocole.charger_evenements().items() if deb <= d <= fin}
    evts = []
    for d in sorted(EV):
        n = len(EV[d]); h = sum(e["heures"] for e in EV[d])
        plages = [f"{e['debut']}-{e['fin']}" for e in EV[d]]
        if d > auj:
            st = "annonce"
        elif d in sai:
            st = "couvert" if sai[d]["buches"] > 0 else "manque"
        else:
            st = "nonsaisi" if d < auj else "aujourdhui"
        evts.append({"date": d, "n": n, "heures": h, "plages": plages, "statut": st})
    ev_bilan = {k: sum(e["n"] for e in evts if e["statut"] == k) for k in ("annonce", "couvert", "manque", "nonsaisi", "aujourdhui")}
    heures = sum(e["heures"] for e in evts if e["date"] <= auj)

    # ---- recommandation : hier, aujourd'hui, demain, après-demain ----
    reco = []
    for k in range(-1, 3):
        d = vrai_auj + k * J
        t, est_prev = temp(d)
        tmin = (PV.get(d) or M.get(d) or {}).get("tmin"); tmax = (PV.get(d) or M.get(d) or {}).get("tmax")
        e = EV.get(d, [])
        if k < 0:
            s = sai.get(d)
            v = {"saisi": s is not None, "buches": s["buches"] if s else None, "a_saisir": (s is None and d >= debut_suivi)}
        else:
            v = recommander(d, t, len(e), [f"{x['debut']}-{x['fin']}" for x in e], stock, plan_a(d)["reserve"], ecart_plan if jours_saisis else None, P, saison)
        v.update({"date": d, "t": t, "tmin": tmin, "tmax": tmax, "prevision": est_prev, "evt": len(e)})
        reco.append(v)

    # ---- calendrier ----
    cal = {}
    d = deb
    while d <= fin:
        t, est_prev = temp(d)
        s = sai.get(d)
        ev = next((x for x in evts if x["date"] == d), None)
        stt = "saisi" if s else ("manquant" if d in manquants else ("futur" if d >= auj else "avant"))
        info = f"{d.isoformat()}" + (f" · {t:.1f} °C".replace(".", ",") if t is not None else "") + (" (prévision)" if est_prev else "")
        if s:
            info += f" · {s['buches']:.0f} bûches" + (f", {s['kwh']:.0f} kWh" if s["kwh"] is not None else ", kWh en attente")
            if s["remarque"]:
                info += f" · {s['remarque']}"
        if ev:
            info += f" · événement Flex D {', '.join(ev['plages'])}"
        if stt == "manquant":
            info += " · à saisir"
        cal[d] = {"t": t, "prevision": est_prev, "buches": s["buches"] if s else None, "evt": ev["n"] if ev else 0,
                  "evt_statut": ev["statut"] if ev else "", "statut": stt, "info": info}
        d += J

    # ---- courbe de stock : plan, réserve, réel (depuis l'inventaire jusqu'à la dernière saisie) ----
    courbe = []
    d = deb; st_r = stock0
    for d in (deb + i * J for i in range((fin - deb).days + 1)):
        pa = plan_a(d)
        r = None
        if d >= date_inv and (jours_saisis and d <= jours_saisis[-1] or d == date_inv):
            if d in sai:
                st_r = sai[d]["stock"]
            r = st_r
        courbe.append({"date": d, "plan": pa["stock"], "reserve": pa["reserve"], "reel": r})

    return {
        "saison": saison, "aujourd_hui": vrai_auj, "date_calcul": auj, "terminee": terminee,
        "jour": (auj - deb).days + 1, "jours_total": (fin - deb).days + 1, "jours_restants": max((fin - vrai_auj).days, 0),
        "critique": (dt.date.fromisoformat(P["critique"]["debut"]), dt.date.fromisoformat(P["critique"]["fin"])),
        "flex_d": tuple(dt.date.fromisoformat(x) for x in saison["flex_d"]),
        "stock": {"depart": stock0, "date_inventaire": date_inv, "actuel": stock, "plan": p_auj["stock"], "reserve": p_auj["reserve"],
                  "marge": stock - p_auj["reserve"], "ecart_plan": ecart_plan, "frein": bool(jours_saisis) and ecart_plan < -50},
        "reel": reel, "plan_date": plan_date, "plan_saison": plan_saison, "fourchette": fourchette, "plan_meteo": hv,
        "evenements": evts, "ev_bilan": ev_bilan, "heures": heures, "plafond_heures": saison.get("plafond_heures_evt", 120),
        "evts_historique": {h: v["evenements"] for h, v in P["evts_par_hiver"].items() if h != saison["id"]},
        "saisie": [sai[d] for d in jours_saisis], "manquants": manquants, "kwh_attente": kwh_attente, "debut_suivi": debut_suivi,
        "reco": reco, "prevision_quand": pv_quand, "maj": statut_maj(), "meteo_derniere": max(M) if M else None,
        "calendrier": cal, "courbe": courbe, "regles": {k: P["hypotheses"][k] for k in ("regle_seuil_coeur", "regle_max_coeur", "regle_liberation", "regle_buches_evt")},
    }


def en_json(e):
    """Version sérialisable (dates ISO) pour rapports/data/saison_courante.json."""
    def conv(x):
        if isinstance(x, dict):
            return {(k.isoformat() if isinstance(k, dt.date) else k): conv(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [conv(v) for v in x]
        if isinstance(x, (dt.date, dt.datetime)):
            return x.isoformat()
        return x
    o = conv({k: v for k, v in e.items() if k not in ("calendrier", "courbe")})
    return o

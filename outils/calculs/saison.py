"""État de la saison à une date (couche calculs, aucun HTML).

Réunit : saisie enrichie, météo réelle et prévision (Environnement Canada, Open-Meteo en secours), creux froids,
événements Flex D (données ouvertes HQ), règle de budget (calculs/recommandation.py), plan recalculé sur la météo
réelle, projection jusqu'à la fin de la saison et historique des recommandations. Utilisé par les pages Saison et
Journal ; exporté dans rapports/data/saison_courante.json et rapports/data/recommandation.json.
"""
import csv, json, os, datetime as dt
from chemins import DATA, SOURCES
from calculs import protocole, prevision, saisons
from calculs import meteo as meteo_obs
from calculs import recommandation as RG

J = dt.timedelta(days=1)
COLS_RECO = ["date", "recommandation", "buches", "moment", "raison", "regle", "source_meteo", "t_prevue", "evenement",
             "stock", "reserve", "genere_le"]
SITE = "https://mgagp.github.io/buchometre/"


def _lire(nom):
    p = os.path.join(DATA, nom)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x):
    return float(x) if x not in ("", None) else None


def fichier_reco(saison):
    return saison.get("recommandations") or f"recommandations_{saison['id']}.csv"


def lire_historique(saison):
    """data/recommandations_AAAA-AAAA.csv : une ligne par matin (écrite par outils/enregistrer_recommandation.py)."""
    return {dt.date.fromisoformat(r["date"]): r for r in _lire(fichier_reco(saison)) if r.get("date")}


def statut_maj():
    p = os.path.join(SOURCES, "maj_statut.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def verdict(r):
    if r["feu"] is None:
        return "indéterminé"
    return "feu" if r["feu"] else "pas de feu"


def etat(saison, aujourd_hui=None):
    P = json.load(open(os.path.join(DATA, "protocole.json"), encoding="utf-8"))
    H = P["hypotheses"]; kb = P["kwh_par_buche"]; cdj = P["coef"][1]; rp = RG.regles(H)
    pb = P["valeur_buche"]["flex_hors_evt"] / kb  # $ par kWh évité hors événement (taxes incluses)
    deb, fin = dt.date.fromisoformat(saison["debut"]), dt.date.fromisoformat(saison["fin"])
    vrai_auj = aujourd_hui or saisons.aujourdhui()
    terminee = vrai_auj > fin
    auj = min(vrai_auj, fin)
    stock0 = P["stock"]["buches"]; date_inv = dt.date.fromisoformat(P["stock"]["inventaire"]["param"]["date"])
    crit = (dt.date.fromisoformat(P["critique"]["debut"]), dt.date.fromisoformat(P["critique"]["fin"]))
    fx = tuple(dt.date.fromisoformat(x) for x in saison["flex_d"])
    hv = saison["plan_meteo"]

    # ---- simulation (protocole) : réserve par date, et dépense moyenne des 3 météos sous la règle (projection) ----
    SS = _lire("protocole_simulation_stock.csv")
    reserve_par_date, moy = {}, {}
    for r in SS:
        if not r["date_2026_2027"]:
            continue
        d = dt.date.fromisoformat(r["date_2026_2027"])
        if r["hiver_meteo"] == hv:
            reserve_par_date[d] = float(r["reserve_evt"])
        moy.setdefault(d, []).append(float(r["buches"]))
    moy = {d: sum(v) / len(v) for d, v in moy.items()}
    dates_res = sorted(reserve_par_date)

    def reserve(d):
        prev = [x for x in dates_res if x <= d]
        return reserve_par_date[prev[-1]] if prev else (reserve_par_date[dates_res[0]] if dates_res else 0)
    res = [v["regle_stock"] for v in P["stock"]["resultats"].values() if "regle_stock" in v]
    fourchette = {"base": (min(r["valeur"] for r in res), max(r["valeur"] for r in res)),
                  "buches": (min(r["buches"] for r in res), max(r["buches"] for r in res))} if res else {}

    # ---- saisie ----
    sai = {}
    for r in _lire(saison["saisie_enrichie"]):
        d = dt.date.fromisoformat(r["date"])
        sai[d] = {"date": r["date"], "buches": _f(r["buches"]) or 0, "kwh": _f(r["kwh"]), "stock": _f(r["stock_restant"]),
                  "compte": bool(r["stock_compte"]), "evt_saisi": r["evenement_hq_saisi"] == "1", "temoin": r["jour_temoin"] == "1",
                  "remarque": r["remarque"], "t": _f(r["t_moy"]), "attendu": _f(r["kwh_attendu_modele"]), "ecart": _f(r["ecart_kwh"]),
                  "kwh_evites": _f(r["kwh_evites_modele"]) or 0, "valeur": _f(r["valeur_base"]) or 0}
    jours_saisis = sorted(sai)
    reel = {"buches": sum(v["buches"] for v in sai.values()), "kwh": sum(v["kwh_evites"] for v in sai.values()),
            "base": sum(v["valeur"] for v in sai.values())}
    dern = jours_saisis[-1] if jours_saisis else None
    stock = sai[dern]["stock"] if dern else stock0
    date_ref = max(dern, date_inv) if dern else date_inv  # date du dernier stock connu

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

    # ---- météo : réelle (archive) avant aujourd'hui, prévision ensuite ----
    M = meteo_obs.observee()  # EC Ste-Anne-de-Bellevue 1, repli Trudeau, puis modèle (étiqueté)
    maj = statut_maj()
    PV = prevision.combiner(vrai_auj, maj)

    def temp(d):
        """→ (t, prévision ?, source)."""
        if d < vrai_auj and d in M:
            return M[d]["t"], False, meteo_obs.etiquette(M[d])
        v = PV["jours"].get(d)
        if v:
            return v["t"], d >= vrai_auj, v["source"]
        return None, False, None

    # ---- creux froids : même définition que l'analyse historique, sur la météo réelle puis la prévision ----
    serie = []
    d = dt.date(deb.year if deb.month >= 7 else deb.year - 1, 10, 1)
    horizon = max(PV["horizon"] or auj, auj)
    while d <= min(horizon, fin):
        t, est_prev, _ = temp(d)
        if t is not None:
            serie.append({"date": d, "t": t, "prevision": est_prev})
        d += J
    ts = [j["t"] for j in serie]
    s3 = protocole.moyenne_mobile(ts, 1); base = protocole.mediane_mobile(ts, 15)
    for j, a, b in zip(serie, s3, base):
        j.update({"s3": a, "base": b, "anom": a - b, "coeur": False, "creux": False})
    runs = RG.creux(serie, H)
    for run in runs:
        for j in run:
            j["creux"] = True
    meteo = {j["date"]: j for j in serie}
    creux_prevus = []
    for run in runs:
        if run[-1]["date"] >= vrai_auj and run[-1]["prevision"]:
            jm = min(run, key=lambda j: j["t"])
            creux_prevus.append({"debut": run[0]["date"], "fin": run[-1]["date"], "en_cours": run[0]["date"] < vrai_auj,
                                 "coeur": [j["date"] for j in run if j["coeur"]], "t_min": jm["t"], "date_min": jm["date"]})

    # ---- événements Flex D de la saison ----
    EV = {d: v for d, v in protocole.charger_evenements().items() if deb <= d <= fin}
    plages = {d: [f"{e['debut']}-{e['fin']}" for e in v] for d, v in EV.items()}
    evts = []
    for d in sorted(EV):
        n = len(EV[d]); h = sum(e["heures"] for e in EV[d])
        if d > auj:
            st = "annonce"
        elif d in sai:
            st = "couvert" if sai[d]["buches"] > 0 else "manque"
        else:
            st = "nonsaisi" if d < auj else "aujourdhui"
        evts.append({"date": d, "n": n, "heures": h, "plages": plages[d], "statut": st})
    ev_bilan = {k: sum(e["n"] for e in evts if e["statut"] == k) for k in ("annonce", "couvert", "manque", "nonsaisi", "aujourdhui")}
    heures = sum(e["heures"] for e in evts if e["date"] <= auj)

    def regle_jour(d, st_, frein=False):
        """Bûches que la règle brûle ce jour-là (météo connue), ou None si la température manque."""
        j = meteo.get(d)
        if not j:
            return None
        n, _ = RG.decider(len(EV.get(d, [])), max(18 - j["t"], 0), j["t"], j["coeur"], crit[0] <= d <= crit[1],
                          RG.apres_liberation(d, rp["liberation"]), st_, reserve(d), H, kb, cdj, rp, frein)
        return n

    # ---- plan recalculé sur la météo réelle : la règle appliquée depuis l'inventaire, jusqu'au dernier stock connu ----
    plan_reel, st_ = {}, stock0
    d = date_inv + J
    fin_plan = min(max(date_ref, vrai_auj - J), fin)
    while d <= fin_plan:
        n = regle_jour(d, st_)
        n = 0 if n is None else n
        st_ -= n
        plan_reel[d] = {"stock": st_, "buches": n}
        d += J
    plan_ref = plan_reel.get(date_ref, {"stock": stock0})["stock"] if date_ref > date_inv else stock0
    ecart_plan = stock - plan_ref
    frein = bool(jours_saisis) and ecart_plan < -50
    bp = sum(v["buches"] for d, v in plan_reel.items() if d <= date_ref)
    plan_date = {"buches": bp, "kwh": bp * kb, "base": bp * kb * pb}

    # ---- projection : du dernier stock connu à la fin de la saison ----
    # jours passés non saisis et jours prévus : la règle sur la météo connue ; au-delà : dépense moyenne des 3 météos sous la règle
    proj, st_ = {}, stock
    d = date_ref + J
    while d <= fin:
        n = regle_jour(d, st_, frein) if (d < vrai_auj or d <= horizon) else None
        if n is None:
            n = moy.get(d, 0)
        n = min(n, max(st_, 0))
        st_ -= n
        proj[d] = {"stock": st_, "buches": n}
        d += J
    bproj = sum(v["buches"] for v in proj.values())
    projection_saison = {"buches": reel["buches"] + bproj, "kwh": reel["kwh"] + bproj * kb, "base": reel["base"] + bproj * kb * pb,
                         "stock_fin": st_}

    # ---- recommandation : hier (fait), aujourd'hui, demain, après-demain ----
    hist_reco = lire_historique(saison)
    reco, st_ = [], stock
    for k in range(-1, 3):
        d = vrai_auj + k * J
        t, est_prev, src = temp(d)
        info = PV["jours"].get(d) if d >= vrai_auj else (M.get(d) or PV["jours"].get(d))
        info = info or {}
        if k < 0:
            s = sai.get(d); h = hist_reco.get(d)
            v = {"saisi": s is not None, "buches": s["buches"] if s else None, "kwh": s["kwh"] if s else None,
                 "a_saisir": (s is None and d >= debut_suivi), "recommande": h}
        else:
            j = meteo.get(d) or ({"t": t, "coeur": False, "creux": False} if t is not None else None)
            v = RG.recommander(d, j, plages.get(d, []), st_, reserve(d), ecart_plan, P, saison, frein)
            st_ -= v["buches"]
            v["verdict"] = verdict(v)
        v.update({"date": d, "t": t, "tmin": info.get("tmin"), "tmax": info.get("tmax"), "prevision": est_prev,
                  "source": src, "evt": len(EV.get(d, [])), "plages": plages.get(d, []),
                  "coeur": bool(meteo.get(d, {}).get("coeur")), "creux": bool(meteo.get(d, {}).get("creux"))})
        reco.append(v)

    # ---- historique : ce qui était recommandé, puis ce qui a été fait ----
    historique = []
    if hist_reco or jours_saisis:
        d0 = min(list(hist_reco) + jours_saisis)
        d = d0
        while d <= auj:
            h = hist_reco.get(d); s = sai.get(d)
            if h or s:
                fait = s["buches"] if s else None
                conc = None
                if h and s and h["recommandation"] in ("feu", "pas de feu"):
                    conc = (h["recommandation"] == "feu") == (fait > 0)
                historique.append({"date": d, "reco": h, "fait": fait, "kwh": s["kwh"] if s else None, "suivi": conc})
            d += J

    # ---- calendrier ----
    cal = {}
    d = deb
    while d <= fin:
        t, est_prev, src = temp(d)
        s = sai.get(d); h = hist_reco.get(d)
        ev = next((x for x in evts if x["date"] == d), None)
        stt = "saisi" if s else ("manquant" if d in manquants else ("futur" if d >= auj else "avant"))
        mo = M.get(d) if d < vrai_auj else None
        if mo:
            fr = lambda x: f"{x:.1f}".replace(".", ",")
            info = f"{d.isoformat()} · min {fr(mo['tmin'])}, max {fr(mo['tmax'])}, moy. {fr(mo['t'])} °C ({src})"
        else:
            info = f"{d.isoformat()}" + (f" · {t:.1f} °C".replace(".", ",") if t is not None else "") + (f" (prévision {src})" if est_prev else "")
        if meteo.get(d, {}).get("coeur"):
            info += " · cœur d'un creux froid"
        elif meteo.get(d, {}).get("creux"):
            info += " · creux froid"
        if h:
            info += f" · recommandé : {h['recommandation']}" + (f" ({h['buches']} bûches)" if h["recommandation"] == "feu" else "")
        if s:
            info += f" · fait : {s['buches']:.0f} bûches" + (f", {s['kwh']:.0f} kWh" if s["kwh"] is not None else ", kWh en attente")
            if s["remarque"]:
                info += f" · {s['remarque']}"
        if ev:
            info += f" · événement Flex D {', '.join(ev['plages'])}"
        if stt == "manquant":
            info += " · à saisir"
        cal[d] = {"t": t, "prevision": est_prev, "buches": s["buches"] if s else None, "evt": ev["n"] if ev else 0,
                  "evt_statut": ev["statut"] if ev else "", "statut": stt, "info": info,
                  "reco_feu": bool(h and h["recommandation"] == "feu"), "coeur": bool(meteo.get(d, {}).get("coeur"))}
        d += J

    # ---- courbe de stock : réel, plan sur la météo réelle, projection, réserve ----
    courbe = []
    st_r = stock0
    for d in (deb + i * J for i in range((fin - deb).days + 1)):
        r = None
        if date_inv <= d <= date_ref:
            if d in sai:
                st_r = sai[d]["stock"]
            r = st_r
        pl = stock0 if d == date_inv else (plan_reel[d]["stock"] if d in plan_reel else None)
        pr = stock if d == date_ref else (proj[d]["stock"] if d in proj else None)
        # valeur évitée cumulée (hors prime d'événement) : plan sur la météo réelle, puis projection depuis le réel
        courbe.append({"date": d, "plan": pl, "projection": pr, "reserve": reserve(d), "reel": r,
                       "v_plan": None if pl is None else (stock0 - pl) * kb * pb,
                       "v_proj": None if pr is None else reel["base"] + (stock - pr) * kb * pb,
                       "v_reel": None if r is None else sum(v["valeur"] for x, v in sai.items() if x <= d)})

    return {
        "saison": saison, "aujourd_hui": vrai_auj, "date_calcul": auj, "terminee": terminee,
        "jour": (auj - deb).days + 1, "jours_total": (fin - deb).days + 1, "jours_restants": max((fin - vrai_auj).days, 0),
        "critique": crit, "flex_d": fx,
        "stock": {"depart": stock0, "date_inventaire": date_inv, "actuel": stock, "date_reference": date_ref, "plan": plan_ref,
                  "reserve": reserve(auj), "marge": stock - reserve(auj), "ecart_plan": ecart_plan, "frein": frein,
                  "fin_projetee": projection_saison["stock_fin"]},
        "reel": reel, "plan_date": plan_date, "projection_saison": projection_saison, "fourchette": fourchette, "plan_meteo": hv,
        "evenements": evts, "ev_bilan": ev_bilan, "heures": heures, "plafond_heures": saison.get("plafond_heures_evt", 120),
        "evts_historique": {h: v["evenements"] for h, v in P["evts_par_hiver"].items() if h != saison["id"]},
        "saisie": [sai[d] for d in jours_saisis], "manquants": manquants, "kwh_attente": kwh_attente, "debut_suivi": debut_suivi,
        "reco": reco, "creux_prevus": creux_prevus, "historique": historique,
        "prevision": {k: v for k, v in PV.items() if k != "jours"}, "maj": maj, "meteo_derniere": max(M) if M else None,
        "meteo_observee": [dict(M[d], date=d, etiquette=meteo_obs.etiquette(M[d])) for d in sorted(M) if vrai_auj - 30 * J <= d < vrai_auj],
        "meteo_libelle": meteo_obs.LIBELLE,
        "calendrier": cal, "courbe": courbe,
        "regles": {k: H[k] for k in ("regle_seuil_coeur", "regle_max_coeur", "regle_liberation", "regle_buches_evt")},
    }


def _conv(x):
    if isinstance(x, dict):
        return {(k.isoformat() if isinstance(k, dt.date) else k): _conv(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_conv(v) for v in x]
    if isinstance(x, (dt.date, dt.datetime)):
        return x.isoformat()
    if isinstance(x, float):
        return round(x, 2)
    return x


def en_json(e):
    """Version sérialisable (dates ISO) pour rapports/data/saison_courante.json."""
    return _conv(dict({k: v for k, v in e.items() if k not in ("calendrier", "courbe")},
                      genere_le=dt.datetime.now().astimezone().isoformat(timespec="minutes")))


def ligne_reco(e):
    """Recommandation du jour, au format de data/recommandations_AAAA-AAAA.csv."""
    r = e["reco"][1]
    return {"date": r["date"].isoformat(), "recommandation": r["verdict"], "buches": r["buches"], "moment": r["moment"],
            "raison": r["raison"], "regle": r["regle"], "source_meteo": r["source"] or "aucune",
            "t_prevue": "" if r["t"] is None else round(r["t"], 1), "evenement": r["evenement"],
            "stock": round(e["stock"]["actuel"]), "reserve": round(e["stock"]["reserve"]),
            "genere_le": dt.datetime.now().astimezone().isoformat(timespec="minutes")}


def pour_routine(e):
    """rapports/data/recommandation.json : ce que lit la routine du matin (petit, stable, en français)."""
    a = e["reco"][1]; s = e["stock"]; pv = e["prevision"]; h = e["reco"][0]
    jours = []
    for k, r in zip(("hier", "aujourd'hui", "demain", "après-demain"), e["reco"]):
        j = {"jour": k, "date": r["date"], "t_moy": None if r["t"] is None else round(r["t"], 1),
             "t_min": r["tmin"], "t_max": r["tmax"], "source": r["source"], "evenement": " et ".join(r["plages"]) or None}
        if k == "hier":
            j.update({"buches_saisies": r["buches"], "kwh_saisis": r["kwh"], "a_saisir": r["a_saisir"],
                      "recommande": (r["recommande"] or {}).get("recommandation")})
        else:
            j.update({"recommandation": r["verdict"], "buches": r["buches"], "moment": r["moment"] or None, "raison": r["raison"]})
        jours.append(j)
    alertes = []
    if pv["source"] is None:
        alertes.append("prévision indisponible : recommandation en mode ouvert")
    elif pv["secours"]:
        alertes.append("Environnement Canada indisponible : prévision Open-Meteo (secours)")
    if (e["maj"] or {}).get("sources", {}).get("evenements_hq", {}).get("ok") is False:
        alertes.append("événements Hydro-Québec non rafraîchis ce matin : vérifier l'avis officiel")
    if s["frein"]:
        alertes.append("stock plus de 50 bûches sous le plan : événements seulement (règle 5)")
    if e["manquants"]:
        alertes.append(f"{len(e['manquants'])} jour(s) à saisir")
    creux = [f"creux froid {'en cours' if c['en_cours'] else 'prévu'} du {RG.dfr(c['debut'])} au {RG.dfr(c['fin'])}, "
             f"minimum {RG.fmt(c['t_min'])} °C le {RG.dfr(c['date_min'])}" for c in e["creux_prevus"]]
    return _conv({
        "genere_le": dt.datetime.now().astimezone().isoformat(timespec="minutes"), "date": a["date"],
        "recommandation": a["verdict"], "buches": a["buches"], "moment": a["moment"] or None, "raison": a["raison"], "regle": a["regle"] or None,
        "evenement": a["evenement"] or None, "source_meteo": pv["source"], "prevision_emise": pv["ec_emis"] if pv["source"] == prevision.EC else pv["om_quand"],
        "jours": jours, "creux": creux,
        "stock": {"actuel": round(s["actuel"]), "au": s["date_reference"], "reserve": round(s["reserve"]),
                  "ecart_plan": round(s["ecart_plan"]), "fin_saison_projetee": round(s["fin_projetee"])},
        "alertes": alertes, "page": SITE,
    })

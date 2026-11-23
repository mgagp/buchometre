#!/usr/bin/env python3
"""Prépare les données du projet bois-chauffage.

Usage : python outils/preparer_donnees.py

Lit sources/ (copies en lecture seule du chiffrier « Bois de chauffage » et de la météo Open-Meteo)
et écrit data/ :
  journal_brut.csv      fidèle au chiffrier (Feuille 1), une ligne par ligne de feuille, totaux compris
  journal_nettoye.csv   une ligne par jour, drapeau mesure/extrapole, météo, anomalies, modèle
  meteo.csv             météo quotidienne Open-Meteo (archive ERA5) pour Vaudreuil-Dorion
  factures.csv          factures Hydro (Feuille 2)
  anomalies.csv         une ligne par anomalie détectée
  modele.json           coefficients et incertitudes du modèle kWh ~ degrés-jours + bûches
Bibliothèque standard seulement.
"""
import csv, json, os, math, datetime as dt

from chemins import RACINE
S = lambda *p: os.path.join(RACINE, "sources", *p)
D = lambda *p: os.path.join(RACINE, "data", *p)

TARIF_2023 = {"p1": 0.06509, "p2": 0.10041, "acces_jour": 0.43505, "seuil_jour": 40}  # tarif D, 1er avril 2023
TAXES = 0.14975  # TPS 5 % + TVQ 9,975 % (s'appliquent à l'électricité résidentielle)
BASE_DJ = 18.0  # degrés-jours de chauffe, base 18 °C
FIN_MESURE = dt.date(2024, 2, 16)  # dernière ligne sans « E » ; chiffrier modifié le 2024-02-17


def serial(n):
    return dt.date(1899, 12, 30) + dt.timedelta(days=int(float(n)))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------- petite algèbre (moindres carrés) ----------
def resoudre(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                k = M[r][c] / M[c][c]
                M[r] = [a - k * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def inverse(A):
    n = len(A)
    return [list(col) for col in zip(*[resoudre(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)])]


def mco(X, y):
    """Moindres carrés ordinaires : coefficients, erreurs-types, R², RMSE."""
    k = len(X[0]); n = len(y)
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(k)]
    c = resoudre(XtX, Xty)
    pred = [sum(ci * xi for ci, xi in zip(c, row)) for row in X]
    sse = sum((a - p) ** 2 for a, p in zip(y, pred)); moy = sum(y) / n
    sst = sum((a - moy) ** 2 for a in y)
    s2 = sse / (n - k); inv = inverse(XtX)
    return {"coef": c, "se": [math.sqrt(s2 * inv[i][i]) for i in range(k)], "r2": 1 - sse / sst,
            "rmse": math.sqrt(s2), "n": n}


def main():
    os.makedirs(D(), exist_ok=True)
    af = list(csv.reader(open(S("bois_Feuille1_A-F_valeurs.csv"), encoding="utf-8")))
    gt = list(csv.reader(open(S("bois_Feuille1_G-T_valeurs.csv"), encoding="utf-8")))
    entete = af[0][1:] + gt[0]
    entete = ["Drapeau"] + entete[:]  # colonne A du chiffrier (« E » = extrapolé)
    meteo = json.load(open(S("meteo_open-meteo_vaudreuil_2023-2024.json"), encoding="utf-8"))
    md = meteo["daily"]
    MET = {d: {"t_moy": md["temperature_2m_mean"][i], "t_min": md["temperature_2m_min"][i],
               "t_max": md["temperature_2m_max"][i], "vent_max": md["wind_speed_10m_max"][i],
               "rayonnement": md["shortwave_radiation_sum"][i]} for i, d in enumerate(md["time"])}
    with open(D("meteo.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(["date", "t_moy", "t_min", "t_max", "vent_max_kmh", "rayonnement_MJ_m2", "dj18"])
        for d in md["time"]:
            m = MET[d]; w.writerow([d, m["t_moy"], m["t_min"], m["t_max"], m["vent_max"], m["rayonnement"], round(max(BASE_DJ - m["t_moy"], 0), 1)])

    # ---------- journal brut (fidèle) ----------
    brut, jours = [], []
    for i, (a, g) in enumerate(zip(af[1:], gt[1:]), start=2):
        ligne = a + g
        typ = "jour" if a[1] else "total_mois"
        date = serial(a[1]).isoformat() if a[1] else ""
        brut.append([i, typ, date] + ligne)
        if typ == "jour":
            jours.append({"ligne": i, "date": serial(a[1]), "drapeau": a[0], "b": int(float(a[2])), "k": float(a[3]),
                          "e": float(a[4]), "t": float(a[5]), "G": f(g[0]), "H": f(g[1]), "I": f(g[2]), "J": f(g[3]),
                          "M": f(g[6]), "R": f(g[11]), "S": f(g[12])})
    with open(D("journal_brut.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["ligne_feuille", "type_ligne", "date_iso", "drapeau", "date_serie", "nb_buches", "kwh_reel", "kwh_eq_estime",
                    "temperature", "prix_sous_40", "prix_plus_40", "reel_nb_sous_40", "reel_nb_plus_40", "reel_montant_ss40",
                    "reel_montant_pl40", "reel_montant_total", "est_nb_sous_40", "est_nb_plus_40", "est_montant_ss40",
                    "est_montant_pl40", "est_montant_total", "economie", "prix_bois_solde"])
        w.writerows(brut)

    # ---------- anomalies ----------
    anomalies = []
    def ano(j, code, detail):
        anomalies.append({"date": j["date"].isoformat(), "ligne": j["ligne"], "code": code, "detail": detail})
        j.setdefault("anos", []).append(code)
    for j in jours:
        j["anos"] = []
        mesure = j["drapeau"] != "E"
        if not mesure:
            ano(j, "extrapole", "Ligne marquée « E » : valeurs saisies d'avance, pas mesurées")
            if j["b"] == 0 and j["e"] > j["k"]:
                ano(j, "eco_sans_buche", f"0 bûche mais kWh estimés {j['e']:.0f} > réels {j['k']:.0f} : économie comptée sans feu")
        if j["G"] is None or j["H"] is None:
            ano(j, "tarif_vide", "Prix du kWh vide (la formule pointe une ligne de total) : coût calculé = 0")
        bon_i, bon_j = min(j["k"], 40), max(j["k"] - 40, 0)
        if j["I"] is not None and (abs(j["I"] - bon_i) > 0.01 or abs(j["J"] - bon_j) > 0.01):
            ano(j, "palier_errone", f"Paliers saisis {j['I']:.0f}/{j['J']:.0f} au lieu de {bon_i:.0f}/{bon_j:.0f}")
        if mesure and j["b"] > 0 and j["e"] <= j["k"]:
            ano(j, "feu_sans_gain", f"{j['b']} bûches mais kWh estimés ({j['e']:.0f}) ≤ réels ({j['k']:.0f})")
        if mesure and j["b"] == 0 and j["e"] != j["k"]:
            ano(j, "sans_feu_ecart", f"Aucun feu mais kWh estimés {j['e']:.0f} ≠ réels {j['k']:.0f}")
        m = MET.get(j["date"].isoformat())
        if mesure and m and abs(j["t"] - m["t_moy"]) >= 6:
            ano(j, "temp_ecart", f"Température notée {j['t']:.0f} °C vs moyenne Open-Meteo {m['t_moy']:.1f} °C")
    with open(D("anomalies.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, ["date", "ligne", "code", "detail"]); w.writeheader(); w.writerows(anomalies)

    # ---------- modèle ----------
    for j in jours:
        m = MET[j["date"].isoformat()]
        j.update(t_moy=m["t_moy"], t_min=m["t_min"], t_max=m["t_max"], dj=max(BASE_DJ - m["t_moy"], 0))
        j["mesure"] = j["drapeau"] != "E"
    mes = [j for j in jours if j["mesure"]]
    modeles = {}
    modeles["principal"] = mco([[1, j["dj"], j["b"]] for j in mes], [j["k"] for j in mes])
    modeles["temp_marc"] = mco([[1, max(BASE_DJ - j["t"], 0), j["b"]] for j in mes], [j["k"] for j in mes])
    modeles["sans_buches"] = mco([[1, j["dj"]] for j in mes], [j["k"] for j in mes])
    sf = [j for j in mes if j["b"] == 0]
    modeles["jours_sans_feu"] = mco([[1, j["dj"]] for j in sf], [j["k"] for j in sf])
    lag = [(mes[i], mes[i - 1]) for i in range(1, len(mes))]
    modeles["avec_veille"] = mco([[1, a["dj"], a["b"], p["b"]] for a, p in lag], [a["k"] for a, p in lag])
    modeles["avec_veille_dj"] = mco([[1, a["dj"], a["b"], p["b"], p["dj"]] for a, p in lag], [a["k"] for a, p in lag])
    c0, cdj, cb = modeles["principal"]["coef"]
    kwh_buche = -cb
    se_b = modeles["principal"]["se"][2]
    lag1 = -(modeles["avec_veille"]["coef"][2] + modeles["avec_veille"]["coef"][3])
    lag2 = -(modeles["avec_veille_dj"]["coef"][2] + modeles["avec_veille_dj"]["coef"][3])
    bas = min(kwh_buche - 1.96 * se_b, -modeles["temp_marc"]["coef"][2])
    haut = max(lag1, lag2, kwh_buche + 1.96 * se_b)

    # ---------- journal nettoyé ----------
    p2, tx = TARIF_2023["p2"], 1 + TAXES
    for j in jours:
        j["kwh_evites"] = kwh_buche * j["b"] if j["mesure"] else 0.0
        j["kwh_sans_feu"] = j["k"] + j["kwh_evites"]
        j["kwh_attendu"] = c0 + cdj * j["dj"] + cb * j["b"]
        j["eco_ht"] = j["kwh_evites"] * p2
        j["eco_ttc"] = j["eco_ht"] * tx
        j["kwh_evites_marc"] = (j["e"] - j["k"])
    with open(D("journal_nettoye.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["date", "mois", "jour_semaine", "statut", "feu", "nb_buches", "kwh_reel", "kwh_eq_marc", "temp_marc",
                    "t_moy_om", "t_min_om", "t_max_om", "dj18", "kwh_attendu_modele", "kwh_sans_feu_modele",
                    "kwh_evites_modele", "kwh_evites_marc", "eco_modele_ht", "eco_modele_ttc", "eco_feuille_marc", "anomalies"])
        js = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
        for j in jours:
            w.writerow([j["date"].isoformat(), j["date"].strftime("%Y-%m"), js[j["date"].weekday()],
                        "mesure" if j["mesure"] else "extrapole", int(j["b"] > 0), j["b"], j["k"], j["e"], j["t"],
                        j["t_moy"], j["t_min"], j["t_max"], round(j["dj"], 1), round(j["kwh_attendu"], 1),
                        round(j["kwh_sans_feu"], 1), round(j["kwh_evites"], 1), j["kwh_evites_marc"],
                        round(j["eco_ht"], 2), round(j["eco_ttc"], 2), "" if j["S"] is None else round(j["S"], 2),
                        ";".join(j["anos"])])

    # ---------- factures (Feuille 2) ----------
    fact = [("20SEP-16NOV", 196.94, None), ("17NOV-18JAN", 432.68, 374.81), ("19JAN-17MAR", 330.79, 404.24),
            ("19MAR-18MAI", 314.73, 330.0), ("19MAI-18JUL", 154.0, 155.0), ("19JUL-19SEP", 133.67, 140.0),
            ("20SEP-16NOV", None, 200.0)]
    with open(D("factures.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(["periode", "colonne_2023", "colonne_2024", "note"])
        notes = ["", "", "Facture 2024 postérieure à la dernière modification du chiffrier (2024-02-17) ?",
                 "Montant rond : probablement une estimation", "Montant rond : probablement une estimation",
                 "Montant rond : probablement une estimation", "Montant rond : probablement une estimation"]
        for (p, a, b), n in zip(fact, notes):
            w.writerow([p, a if a is not None else "", b if b is not None else "", n])

    # contrôle facture 17 nov. 2023 – 18 janv. 2024 (entièrement mesurée)
    d1, d2 = dt.date(2023, 11, 17), dt.date(2024, 1, 18)
    n = (d2 - d1).days + 1
    kwh = sum(j["k"] for j in jours if d1 <= j["date"] <= d2)
    cout = 40 * n * TARIF_2023["p1"] + (kwh - 40 * n) * p2 + n * TARIF_2023["acces_jour"]
    controle = {"periode": "2023-11-17 → 2024-01-18", "jours": n, "kwh_journal": kwh, "cout_ht": round(cout, 2),
                "cout_ttc": round(cout * tx, 2), "facture": 374.81, "ecart_pct": round((cout * tx / 374.81 - 1) * 100, 2)}

    # ---------- saison ----------
    def dj(a, b):
        return sum(max(BASE_DJ - MET[(a + dt.timedelta(i)).isoformat()]["t_moy"], 0) for i in range((b - a).days + 1))
    dj_mes = dj(dt.date(2023, 11, 7), FIN_MESURE); dj_saison = dj(dt.date(2023, 11, 1), dt.date(2024, 3, 31))
    b_mes = sum(j["b"] for j in mes)
    saison = {"dj_mesure": round(dj_mes, 1), "dj_saison": round(dj_saison, 1), "part_dj_mesuree": round(dj_mes / dj_saison, 3),
              "buches_mesurees": b_mes, "buches_saison_central": round(b_mes * dj_saison / dj_mes),
              "buches_saison_bas": b_mes}

    json.dump({"base_dj": BASE_DJ, "tarif_2023": TARIF_2023, "taxes": TAXES, "fin_mesure": FIN_MESURE.isoformat(),
               "kwh_par_buche": kwh_buche, "se_kwh_par_buche": se_b, "kwh_par_buche_bas": bas, "kwh_par_buche_haut": haut,
               "kwh_par_buche_avec_veille": lag1, "kwh_par_buche_avec_veille_dj": lag2,
               "modeles": modeles, "controle_facture": controle, "saison": saison,
               "meteo_source": {"api": "Open-Meteo archive (réanalyse ERA5)", "lat": meteo["latitude"], "lon": meteo["longitude"],
                                "lieu_hypothese": "Vaudreuil-Dorion (QC)"}},
              open(D("modele.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(jours)} jours ({len(mes)} mesurés), {len(anomalies)} anomalies, {kwh_buche:.2f} kWh/bûche ± {se_b:.2f}")
    print("contrôle facture :", controle); print("saison :", saison)


def _telecharger(url, dest, valider):
    """Télécharge dans un fichier temporaire, valide, puis remplace. En cas d'échec, garde le fichier versionné."""
    import urllib.request
    tmp = dest + ".tmp"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "buchometre (github.com/mgagp/buchometre)"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            f.write(r.read())
        valider(tmp)
        os.replace(tmp, dest)
        return {"ok": True}
    except Exception as e:  # réseau, HTTP, contenu invalide : on retombe sur les données versionnées
        if os.path.exists(tmp):
            os.remove(tmp)
        return {"ok": False, "erreur": f"{type(e).__name__}: {e}"[:300]}


def _json_daily(p):
    d = json.load(open(p, encoding="utf-8"))["daily"]
    assert d["time"] and d["temperature_2m_mean"], "réponse sans données quotidiennes"


def _json_ec(p):
    from calculs.prevision import lire_ec
    assert lire_ec(p)[0], "bulletin d'Environnement Canada sans prévision lisible"


def _csv_hq(p):
    lignes = open(p, encoding="utf-8-sig").read().splitlines()
    assert lignes and lignes[0].startswith("offre;datedebut"), "en-tête inattendu"


def mettre_a_jour_sources():
    """--maj : télécharge la météo Open-Meteo (archive 1er juil. 2023 → hier, et prévision 2 jours passés + 7 jours),
    la prévision d'Environnement Canada pour Vaudreuil-Dorion (source principale de la recommandation),
    et les événements de pointe HQ. Chaque source est indépendante ; un échec n'interrompt rien (fichiers versionnés gardés).
    L'état est écrit dans sources/maj_statut.json (non versionné) et affiché sur le site."""
    from calculs.prevision import EC_URL, EC_FICHIER
    fin = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    lat_lon = "latitude=45.40&longitude=-74.03"
    srcs = {
        "meteo_archive": ("https://archive-api.open-meteo.com/v1/archive?" + lat_lon + "&start_date=2023-07-01&end_date=" + fin +
                          "&daily=temperature_2m_mean,temperature_2m_min,temperature_2m_max,wind_speed_10m_max&timezone=America%2FToronto",
                          S("meteo_open-meteo_vaudreuil_2023-2026.json"), _json_daily),
        "prevision": ("https://api.open-meteo.com/v1/forecast?" + lat_lon +
                      "&daily=temperature_2m_mean,temperature_2m_min,temperature_2m_max&timezone=America%2FToronto&past_days=2&forecast_days=7",
                      S("prevision_open-meteo.json"), _json_daily),
        "prevision_ec": (EC_URL, S(EC_FICHIER), _json_ec),
        "evenements_hq": ("https://donnees.hydroquebec.com/api/explore/v2.1/catalog/datasets/evenements-pointe/exports/csv?delimiter=%3B",
                          S("hq_evenements_pointe.csv"), _csv_hq),
    }
    statut = {"quand": dt.datetime.now().astimezone().isoformat(timespec="minutes"), "sources": {}}
    for nom, (url, dest, val) in srcs.items():
        statut["sources"][nom] = _telecharger(url, dest, val)
        print(f"--maj {nom} :", "ok" if statut["sources"][nom]["ok"] else "ÉCHEC, données versionnées gardées (" + statut["sources"][nom]["erreur"] + ")")
    json.dump(statut, open(S("maj_statut.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return statut

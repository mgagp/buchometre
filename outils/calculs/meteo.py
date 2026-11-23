"""Météo observée : la source canonique (couche calculs, aucun HTML).

Environnement Canada, données climatiques quotidiennes (API GeoMet, collection « climate-daily ») :
  1. STE-ANNE-DE-BELLEVUE 1 (Climate ID 702FHL8), à environ 8 km de Vaudreuil-Dorion ;
  2. repli : MONTREAL INTL A (Montréal-Trudeau, 7025251) si le minimum ou le maximum manque ;
  3. dernier repli : Open-Meteo (archive, modèle ECMWF IFS), étiqueté « estimation par modèle », jamais présenté comme une mesure.
Moyenne quotidienne = (max + min) / 2, la définition d'EC.

Fichiers (même format : date, station, min, max, moyenne, source) :
  - sources/meteo_ec_2023-2026.csv : 1er juill. 2023 → 30 juin 2026, téléchargé une fois (python outils/calculs/meteo.py --historique) ;
  - data/meteo_observee_AAAA-AAAA.csv : la saison (à partir du 1er juill.), versionné ; chaque matin, --maj retélécharge
    les 30 derniers jours et accepte les révisions d'EC (le changement se voit dans le commit quotidien).
"""
import csv, json, os, sys, datetime as dt, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chemins import DATA, SOURCES

API = "https://api.weather.gc.ca/collections/climate-daily/items"
STATIONS = [("702FHL8", "Ste-Anne-de-Bellevue 1"), ("7025251", "Montréal-Trudeau")]
SRC_EC, SRC_MODELE = "EC climate-daily (mesure)", "Open-Meteo (estimation par modèle)"
COLS = ["date", "station", "min", "max", "moyenne", "source"]
HISTORIQUE = "meteo_ec_2023-2026.csv"
LIBELLE = "Environnement Canada, Ste-Anne-de-Bellevue 1 (repli : Montréal-Trudeau)"
JOURS_REVISES = 30


def moyenne(tmin, tmax):
    return round((tmin + tmax) / 2, 1)


def _ec(climate_id, debut, fin):
    """{date: (min, max, moyenne publiée par EC)} pour une station EC (jours avec min et max seulement)."""
    url = (f"{API}?f=json&CLIMATE_IDENTIFIER={climate_id}&datetime={debut.isoformat()}/{fin.isoformat()}"
           "&properties=LOCAL_DATE,MIN_TEMPERATURE,MAX_TEMPERATURE,MEAN_TEMPERATURE&sortby=LOCAL_DATE&limit=10000")
    req = urllib.request.Request(url, headers={"User-Agent": "buchometre (github.com/mgagp/buchometre)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        fs = json.load(r)["features"]
    out = {}
    for f in fs:
        p = f["properties"]
        if p["MIN_TEMPERATURE"] is not None and p["MAX_TEMPERATURE"] is not None:
            a, b = float(p["MIN_TEMPERATURE"]), float(p["MAX_TEMPERATURE"])
            m = p.get("MEAN_TEMPERATURE")  # (max + min) / 2, arrondi par EC
            out[dt.date.fromisoformat(p["LOCAL_DATE"][:10])] = (a, b, float(m) if m is not None else moyenne(a, b))
    return out


def _modele():
    """Open-Meteo (archive, versionnée dans sources/) : {date: (min, max)}."""
    p = os.path.join(SOURCES, "meteo_open-meteo_vaudreuil_2023-2026.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding="utf-8"))["daily"]
    return {dt.date.fromisoformat(t): (a, b) for t, a, b in zip(d["time"], d["temperature_2m_min"], d["temperature_2m_max"])
            if a is not None and b is not None}


def lignes(debut, fin):
    """Télécharge et choisit, jour par jour, la meilleure source (EC Ste-Anne, EC Trudeau, modèle)."""
    par_station = [(cid, nom, _ec(cid, debut, fin)) for cid, nom in STATIONS]
    om = _modele()
    out = []
    d = debut
    while d <= fin:
        for cid, nom, v in par_station:
            if d in v:
                a, b, m = v[d]
                out.append({"date": d.isoformat(), "station": f"{nom} ({cid})", "min": a, "max": b, "moyenne": m, "source": SRC_EC})
                break
        else:
            if d in om:
                a, b = om[d]
                out.append({"date": d.isoformat(), "station": "Open-Meteo 45,40 N −74,03 O", "min": a, "max": b, "moyenne": moyenne(a, b), "source": SRC_MODELE})
        d += dt.timedelta(days=1)
    return out


def _lire(p):
    if not os.path.exists(p):
        return {}
    with open(p, newline="", encoding="utf-8") as f:
        return {r["date"]: r for r in csv.DictReader(f)}


def _ecrire(p, rows):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: r["date"]))


def fichier_saison(saison):
    return saison.get("meteo_observee") or f"meteo_observee_{saison['id']}.csv"


def mettre_a_jour(saison, hier=None):
    """--maj, pendant la saison seulement (comme le journal des recommandations : pas de commit quotidien hors saison) :
    retélécharge les 30 derniers jours, plus tout trou depuis le dernier jour versionné (tout depuis le 1er juill. si le
    fichier est neuf) ; révisions d'EC acceptées. Renvoie le nombre de jours écrits et de jours révisés.
    Lève une exception si EC ne répond pas (le fichier versionné reste)."""
    hier = hier or (dt.date.today() - dt.timedelta(days=1))
    if not (dt.date.fromisoformat(saison["debut"]) - dt.timedelta(days=1) <= hier <= dt.date.fromisoformat(saison["fin"])):
        return {"ok": True, "hors_saison": True, "jours": 0, "revises": 0, "de": None}
    p = os.path.join(DATA, fichier_saison(saison))
    rows = _lire(p)
    y = int(saison["id"][:4])
    d0 = dt.date(y, 7, 1)
    debut = d0
    if rows:
        suite = dt.date.fromisoformat(max(rows)) + dt.timedelta(days=1)
        debut = max(d0, min(suite, hier - dt.timedelta(days=JOURS_REVISES - 1)))
    neuves = lignes(debut, min(hier, dt.date(y + 1, 6, 30)))
    assert any(r["source"] == SRC_EC for r in neuves), "aucune mesure d'Environnement Canada reçue"
    revises = 0
    for r in neuves:
        r = {k: str(v) for k, v in r.items()}
        anc = rows.get(r["date"])
        if anc and anc != r:
            revises += 1
        rows[r["date"]] = r
    _ecrire(p, rows)
    return {"ok": True, "jours": len(neuves), "revises": revises, "de": debut.isoformat()}


def observee():
    """Météo observée canonique : {date: {t, tmin, tmax, station, source, mesure}} (historique, puis saisons).
    Un jour absent des fichiers (ex. hier, avant la publication d'EC) est complété par le modèle, étiqueté comme tel."""
    out = {}
    fichiers = [os.path.join(SOURCES, HISTORIQUE)] + sorted(os.path.join(DATA, f) for f in os.listdir(DATA) if f.startswith("meteo_observee_"))
    for p in fichiers:
        for k, r in _lire(p).items():
            out[dt.date.fromisoformat(k)] = {"t": float(r["moyenne"]), "tmin": float(r["min"]), "tmax": float(r["max"]),
                                            "station": r["station"], "source": r["source"], "mesure": r["source"] == SRC_EC}
    for d, (a, b) in _modele().items():
        if d not in out:
            out[d] = {"t": moyenne(a, b), "tmin": a, "tmax": b, "station": "Open-Meteo 45,40 N −74,03 O", "source": SRC_MODELE, "mesure": False}
    return out


def etiquette(j):
    """« Ste-Anne-de-Bellevue 1, EC » ou « estimation par modèle (Open-Meteo) »."""
    if not j:
        return ""
    return f"{j['station'].split(' (')[0]}, EC" if j["mesure"] else "estimation par modèle (Open-Meteo)"


if __name__ == "__main__":
    if "--historique" in sys.argv:
        rows = {r["date"]: {k: str(v) for k, v in r.items()} for r in lignes(dt.date(2023, 7, 1), dt.date(2026, 6, 30))}
        _ecrire(os.path.join(SOURCES, HISTORIQUE), rows)
        n = {}
        for r in rows.values():
            n[r["station"]] = n.get(r["station"], 0) + 1
        print(f"{len(rows)} jours :", n)

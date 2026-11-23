"""Prévision météo pour Vaudreuil-Dorion (couche calculs, aucun HTML).

Environnement Canada d'abord (bulletin de la ville, API GeoMet « citypageweather », lieu qc-66),
Open-Meteo en secours (et pour les jours que le bulletin ne couvre pas). Les fichiers sont téléchargés par
« preparer_donnees.py --maj » dans sources/ ; sans téléchargement, les fichiers versionnés servent (souvent périmés,
donc sans jour « aujourd'hui » : la recommandation passe alors en mode ouvert, de façon visible).

Température moyenne d'un jour selon Environnement Canada : (maximum + minimum) / 2, la même définition que la météo
observée (calculs/meteo.py) ; minimum = celui de la nuit précédente (petit matin), sinon celui de la nuit suivante.
"""
import json, os, datetime as dt
from chemins import SOURCES

EC_FICHIER = "prevision_environnement-canada.json"
EC_URL = "https://api.weather.gc.ca/collections/citypageweather-realtime/items/qc-66?f=json"
EC_PAGE = "https://meteo.gc.ca/fr/location/index.html?coords=45.4,-74.04"
OM_FICHIER = "prevision_open-meteo.json"
JOURS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
EC, OM = "Environnement Canada", "Open-Meteo"


def _val(x):
    return x.get("en") if isinstance(x, dict) else x


def lire_ec(p=None):
    """→ ({date: {t, tmin, tmax}}, émission locale « AAAA-MM-JJ HH:MM ») ; ({}, None) si absent ou illisible."""
    p = p or os.path.join(SOURCES, EC_FICHIER)
    try:
        fg = json.load(open(p, encoding="utf-8"))["properties"]["forecastGroup"]
        emis = dt.datetime.fromisoformat(_val(fg["timestamp"]).replace("Z", "+00:00")).astimezone()
        hauts, bas = {}, {}
        for f in fg["forecasts"]:
            nom = (_val(f["period"]["value"]) or "").lower()
            nuit = "night" in nom or (_val(f["period"].get("textForecastName")) or "").lower() == "tonight"
            jsem = JOURS_EN.index(nom.split()[0])
            d = emis.date() + dt.timedelta(days=(jsem - emis.weekday()) % 7)
            for tp in f["temperatures"]["temperature"]:
                v = _val(tp["value"])
                if v is None:
                    continue
                (bas if _val(tp["class"]) == "low" else hauts)[d] = float(v)
        out = {}
        for d, tmax in hauts.items():
            # minimum du jour : celui de la nuit précédente (petit matin), sinon celui de la nuit suivante
            tmin = bas.get(d - dt.timedelta(days=1), bas.get(d))
            if tmin is None:
                continue
            out[d] = {"t": (tmax + tmin) / 2, "tmin": tmin, "tmax": tmax}
        return out, emis.strftime("%Y-%m-%d %H:%M")
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return {}, None


def lire_om(p=None):
    """Prévision Open-Meteo (2 jours passés + 7 jours) : ({date: {t, tmin, tmax}}, heure du fichier)."""
    p = p or os.path.join(SOURCES, OM_FICHIER)
    if not os.path.exists(p):
        return {}, None
    d = json.load(open(p, encoding="utf-8"))["daily"]
    out = {}
    for i, t in enumerate(d["time"]):
        if d["temperature_2m_mean"][i] is not None:
            out[dt.date.fromisoformat(t)] = {"t": d["temperature_2m_mean"][i], "tmin": d["temperature_2m_min"][i], "tmax": d["temperature_2m_max"][i]}
    return out, dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")


def combiner(auj, statut_maj=None):
    """Prévision retenue jour par jour à partir d'aujourd'hui (EC, sinon Open-Meteo), plus les jours récents d'Open-Meteo.
    Renvoie {jours: {date: {t, tmin, tmax, source}}, source: source d'aujourd'hui ou None, secours: bool,
    ec_emis, om_quand, ec_echec, om_echec, horizon}."""
    ec, ec_emis = lire_ec(); om, om_quand = lire_om()
    src = (statut_maj or {}).get("sources", {})
    jours = {}
    for d, v in om.items():
        jours[d] = dict(v, source=OM)
    for d, v in ec.items():
        if d >= auj:
            jours[d] = dict(v, source=EC)
    s_auj = jours.get(auj, {}).get("source")
    futurs = [d for d in jours if d >= auj]
    return {"jours": jours, "source": s_auj, "secours": s_auj == OM, "ec_emis": ec_emis, "om_quand": om_quand,
            "ec_echec": src.get("prevision_ec", {}).get("ok") is False or auj not in ec,
            "om_echec": src.get("prevision", {}).get("ok") is False, "horizon": max(futurs) if futurs else None}

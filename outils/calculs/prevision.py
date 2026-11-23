"""Prévision météo pour Vaudreuil-Dorion (couche calculs, aucun HTML).

Environnement Canada d'abord (bulletin de la ville, API GeoMet « citypageweather », lieu qc-66),
Open-Meteo en secours (et pour les jours que le bulletin ne couvre pas). Les fichiers sont téléchargés par
« preparer_donnees.py --maj » dans sources/ ; sans téléchargement, les fichiers versionnés servent (souvent périmés,
donc sans jour « aujourd'hui » : la recommandation passe alors en mode ouvert, de façon visible).

Heure du minimum (affichage et plan de feu, jamais pour la décision) : celle du minimum affiché (EC : la nuit qui
mène au jour, ou la nuit qui suit quand le bulletin ne donne plus la précédente ; Open-Meteo : le jour civil), d'après la prévision horaire d'EC (24 h seulement) si elle couvre cette nuit,
sinon d'après Open-Meteo horaire, marqué « (modèle) ».

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
EC_HORAIRE, OM_HORAIRE = "Environnement Canada (horaire)", "Open-Meteo (modèle)"


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
            veille = d - dt.timedelta(days=1) in bas
            tmin = bas.get(d - dt.timedelta(days=1), bas.get(d))
            if tmin is None:
                continue
            out[d] = {"t": (tmax + tmin) / 2, "tmin": tmin, "tmax": tmax, "nuit_min": "veille" if veille else "suivante"}
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


def lire_ec_horaire(p=None):
    """Prévision horaire d'EC (24 h à partir de l'émission, degrés entiers) → {datetime local naïf: °C}."""
    p = p or os.path.join(SOURCES, EC_FICHIER)
    try:
        hf = json.load(open(p, encoding="utf-8"))["properties"]["hourlyForecastGroup"]["hourlyForecasts"]
        out = {}
        for x in hf:
            t = dt.datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
            v = _val(x["temperature"]["value"])
            if v is not None:
                out[t] = float(v)
        return out
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def lire_om_horaire(p=None):
    """Prévision horaire d'Open-Meteo (modèle, heure de Toronto) → {datetime local naïf: °C}."""
    p = p or os.path.join(SOURCES, OM_FICHIER)
    try:
        h = json.load(open(p, encoding="utf-8")).get("hourly") or {}
        return {dt.datetime.fromisoformat(t): float(v) for t, v in zip(h.get("time", []), h.get("temperature_2m", [])) if v is not None}
    except (OSError, ValueError, TypeError):
        return {}


def fenetre_min(d, nuit="veille"):
    """Fenêtre où chercher l'heure du minimum affiché pour le jour d, la même que celle de ce minimum :
    EC « veille » : la veille 18 h → d 12 h ; EC « suivante » (aujourd'hui, la nuit passée n'est plus au bulletin) :
    d 18 h → lendemain 12 h ; Open-Meteo (minimum du jour civil) : d 0 h → 23 h."""
    if nuit == "suivante":
        d = d + dt.timedelta(days=1)
    if nuit == "jour":
        return dt.datetime.combine(d, dt.time(0)), dt.datetime.combine(d, dt.time(23))
    return dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18)), dt.datetime.combine(d, dt.time(12))


def creux_horaire(serie, debut, fin, partielle=False):
    """Heure la plus froide de serie entre debut et fin (inclus) → (datetime, °C) ou None.
    Série complète exigée ; avec partielle=True (EC : 24 h seulement), elle peut s'arrêter avant fin, à condition
    que le minimum soit suivi d'une remontée dans la série (sinon le vrai creux peut être après la fin du bulletin)."""
    h, heures = debut, []
    while h <= fin:
        heures.append(h); h += dt.timedelta(hours=1)
    pres = [x for x in heures if x in serie]
    if not pres or pres[0] != debut or (len(pres) < len(heures) and not partielle):
        return None
    if pres != heures[:len(pres)]:
        return None
    tm = min(pres, key=lambda x: (serie[x], x))
    if len(pres) < len(heures) and not any(serie[x] > serie[tm] for x in pres if x > tm):
        return None
    return tm, serie[tm]


def heure_min(d, h_ec, h_om, nuit="veille"):
    """Heure du minimum affiché pour le jour d (fenetre_min) : EC horaire si son bulletin couvre la fenêtre,
    sinon Open-Meteo (modèle). → {"a": datetime, "t": °C, "source": ...} ou None."""
    a, b = fenetre_min(d, nuit)
    for serie, src, part in ((h_ec, EC_HORAIRE, True), (h_om, OM_HORAIRE, False)):
        r = creux_horaire(serie, a, b, part)
        if r:
            return {"a": r[0], "t": r[1], "source": src}
    return None


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
    h_ec, h_om = lire_ec_horaire(), lire_om_horaire()
    for d, v in jours.items():
        if d >= auj:
            v["heure_min"] = heure_min(d, h_ec, h_om, v.get("nuit_min", "jour") if v["source"] == EC else "jour")
            v["heure_min_suivante"] = heure_min(d, h_ec, h_om, "suivante")   # creux de la nuit qui suit (plan de feu)
    return {"jours": jours, "source": s_auj, "secours": s_auj == OM, "ec_emis": ec_emis, "om_quand": om_quand,
            "ec_echec": src.get("prevision_ec", {}).get("ok") is False or auj not in ec,
            "om_echec": src.get("prevision", {}).get("ok") is False, "horizon": max(futurs) if futurs else None}

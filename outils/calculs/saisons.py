"""Lecture de data/saisons.json : quelle saison est courante, lesquelles sont archivées."""
import json, os, datetime as dt
from chemins import DATA


def charger():
    return json.load(open(os.path.join(DATA, "saisons.json"), encoding="utf-8"))


def courante():
    c = charger()
    return next(s for s in c["saisons"] if s["id"] == c["courante"])


def archivees():
    """Saisons affichées dans Archives : tout sauf la courante, plus récente d'abord."""
    c = charger()
    return sorted([s for s in c["saisons"] if s["id"] != c["courante"]], key=lambda s: s["debut"], reverse=True)


def d(s):
    return dt.date.fromisoformat(s)


def aujourdhui():
    """Date du jour (fuseau du système : TZ=America/Toronto en CI). BUCHOMETRE_DATE=AAAA-MM-JJ la remplace pour un essai."""
    v = os.environ.get("BUCHOMETRE_DATE")
    return dt.date.fromisoformat(v) if v else dt.date.today()

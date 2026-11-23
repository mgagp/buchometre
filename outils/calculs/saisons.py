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

"""Gabarit des pages (couche rendu) : en-tête, menu à 5 entrées, sous-menus, pied de page,
résolution des liens et pages de redirection des anciennes adresses.

Les pages écrivent leurs liens en chemins « logiques » depuis la racine du site (ex. « strategie/plan.html »,
« data/meteo.csv ») ou avec les anciens noms (« protocole.html ») ; page() les convertit en chemins relatifs
au fichier écrit, ce qui marche en local (file://) comme sur GitHub Pages.
"""
import os, re, html, shutil, posixpath, datetime as dt
from chemins import OUT, THEME

E = html.escape
SITE = "Bûchomètre"
DEPOT = "https://github.com/mgagp/buchometre"
ARCH23 = "archives/2023-2024/"

MENU = [("index.html", "Saison", "saison"), ("journal.html", "Journal", "journal"), ("strategie/index.html", "Stratégie", "strategie"),
        ("archives/index.html", "Archives", "archives"), ("methode.html", "Méthode", "methode")]

SOUSMENUS = {
    "strategie/": [("strategie/index.html", "Règles et tarif"), ("strategie/plan.html", "Plan de saison"),
                   ("strategie/meteo.html", "Étude météo"), ("strategie/inventaire.html", "Inventaire de la pile")],
    ARCH23: [(ARCH23 + "index.html", "Sommaire"), (ARCH23 + "mensuel.html", "Mensuel"), (ARCH23 + "mois-2023-11.html", "nov."),
             (ARCH23 + "mois-2023-12.html", "déc."), (ARCH23 + "mois-2024-01.html", "janv."), (ARCH23 + "mois-2024-02.html", "févr."),
             (ARCH23 + "mois-2024-03.html", "mars"), (ARCH23 + "jours.html", "Jour par jour"), (ARCH23 + "donnees.html", "Données brutes"),
             (ARCH23 + "factures.html", "Factures"), (ARCH23 + "qualite.html", "Qualité")],
}
SOUSMENU_TITRE = {"strategie/": "Stratégie 2026-2027", ARCH23: "Archives · hiver 2023-2024"}

# Anciennes adresses (avant la restructuration du 23 nov. 2026) → nouvelles
ROUTES = {
    "mensuel.html": ARCH23 + "mensuel.html", "jours.html": ARCH23 + "jours.html", "donnees.html": ARCH23 + "donnees.html",
    "factures.html": ARCH23 + "factures.html", "qualite.html": ARCH23 + "qualite.html",
    "decisions.html": "methode.html#decisions", "inventaire.html": "strategie/inventaire.html",
    "protocole.html": "strategie/index.html", "protocole-meteo.html": "strategie/meteo.html",
    "protocole-sim.html": "strategie/plan.html", "protocole-sim-mensuel.html": "strategie/plan.html#mensuel",
    "protocole-sim-jours.html": "strategie/plan.html#jours", "protocole-saisie.html": "journal.html",
}
RE_MOIS = re.compile(r"^mois-(\d{4}-\d{2})\.html$")
_ecrites = []


def route(chemin):
    """Ancien nom ou chemin logique → (chemin cible, fragment par défaut)."""
    if chemin in ROUTES:
        c, _, f = ROUTES[chemin].partition("#")
        return c, f
    if RE_MOIS.match(chemin):
        return ARCH23 + chemin, ""
    return chemin, ""


def _relatif(cible, depuis):
    rel = posixpath.relpath(cible, posixpath.dirname(depuis) or ".")
    return rel


RE_LIEN = re.compile(r"""(\b(?:href|src)=)(['"])([^'"]*)\2""")


def relier(h, chemin_page):
    def sub(m):
        v = m.group(3)
        if not v or v.startswith(("#", "http:", "https:", "mailto:", "data:", "javascript:", "//")):
            return m.group(0)
        chemin, _, frag = v.partition("#")
        cible, frag_def = route(chemin)
        frag = frag or frag_def
        return m.group(1) + m.group(2) + _relatif(cible, chemin_page) + ("#" + frag if frag else "") + m.group(2)
    return RE_LIEN.sub(sub, h)


def section_de(chemin):
    for u, _, cle in MENU:
        if chemin == u:
            return cle
    if chemin.startswith("strategie/"):
        return "strategie"
    if chemin.startswith("archives/"):
        return "archives"
    return ""


def entete(chemin, contexte=""):
    sec = section_de(chemin)
    menu = "".join(f"<a href='{u}' class='onglet{' actif' if cle == sec else ''}'" + (" aria-current='page'" if cle == sec else "") + f">{E(t)}</a>"
                   for u, t, cle in MENU)
    sm = ""
    for pref, items in SOUSMENUS.items():
        if chemin.startswith(pref):
            sm = (f"<nav class='sousnav' aria-label='{E(SOUSMENU_TITRE[pref])}'><span class='sousnav-titre'>{E(SOUSMENU_TITRE[pref])}</span>" +
                  "".join(f"<a href='{u}'" + (" class='actif' aria-current='page'" if u == chemin else "") + f">{E(t)}</a>" for u, t in items) + "</nav>")
    return (f"<header class='site'><a class='marque' href='index.html'>{SITE}</a><span class='contexte'>{contexte}</span></header>"
            f"<nav class='menu' aria-label='Menu principal'>{menu}</nav>{sm}")


def page(nom, titre, corps, quand=None, sous=None, contexte="Saison 2026-2027", classe=""):
    """Écrit une page. nom : chemin logique ou ancien nom (converti par ROUTES)."""
    chemin, _ = route(nom)
    quand = quand or dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if sous is None:
        sous = ""
    h = ("<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
         f"<title>{E(titre)} · {SITE}</title><link rel='stylesheet' href='assets/site.css'><link rel='icon' href='assets/favicon.svg'></head>"
         f"<body class='{classe}'>{entete(chemin, contexte)}<main class='contenu'><h1>{E(titre)}</h1>{sous}{corps}</main>"
         f"<footer class='pied'>{SITE} · généré le {E(quand)} à partir de <a href='{DEPOT}/tree/main/data'>data/</a> · "
         f"<a href='{DEPOT}'>code source</a> · <a href='methode.html'>méthode</a></footer></body></html>")
    # Tableaux larges : défilement horizontal sur téléphone
    h = h.replace("<table", "<div class='tab'><table").replace("</table>", "</table></div>")
    h = relier(h, chemin)
    dest = os.path.join(OUT, *chemin.split("/"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(h)
    _ecrites.append(chemin)
    return chemin


def redirections():
    """Pages minuscules aux anciennes adresses : redirigent vers la nouvelle (en gardant l'ancre éventuelle)."""
    anciens = list(ROUTES) + [os.path.basename(c) for c in _ecrites if c.startswith(ARCH23) and RE_MOIS.match(os.path.basename(c))]
    for a in anciens:
        cible, frag = route(a)
        url = _relatif(cible, a) + ("#" + frag if frag else "")
        h = ("<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='robots' content='noindex'>"
             f"<title>Page déplacée · {SITE}</title><link rel='canonical' href='{url}'>"
             f"<meta http-equiv='refresh' content='0; url={url}'>"
             f"<script>location.replace('{url.split('#')[0]}' + (location.hash || '{('#' + frag) if frag else ''}'));</script></head>"
             f"<body><p>Cette page a déménagé : <a href='{url}'>{E(cible)}</a>.</p></body></html>")
        with open(os.path.join(OUT, a), "w", encoding="utf-8") as f:
            f.write(h)
    return anciens


def copier_theme():
    """theme/ → rapports/assets/ (CSS, images). Le thème ne contient aucune donnée."""
    dest = os.path.join(OUT, "assets")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(THEME, dest, ignore=shutil.ignore_patterns("README.md"))

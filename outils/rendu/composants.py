"""Composants HTML réutilisables (couche rendu).

Règle : HTML sémantique avec des classes stables (documentées dans theme/README.md).
Aucune couleur ici : seules des géométries (largeur, position en %) passent par style=.
"""
import html, datetime as dt

E = html.escape
MOIS_FR = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
JOURS_FR = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def nb(x, dec=0):
    if x is None or x == "":
        return "—"
    return f"{float(x):,.{dec}f}".replace(",", " ").replace(".", ",")


def argent(x, dec=2):
    return (f"{x:,.{dec}f}".replace(",", " ").replace(".", ",") + " $") if x is not None else "—"


def pct(x, dec=0):
    return nb(x * 100, dec) + " %"


def dfr(d, annee=False, jour=False):
    d = dt.date.fromisoformat(d) if isinstance(d, str) else d
    s = f"{d.day}{'er' if d.day == 1 else ''} {MOIS_FR[d.month]}" + (f" {d.year}" if annee else "")
    return (JOURS_FR[d.weekday()] + " " + s) if jour else s


def carte(v, l, cl="", lien=None, sous=""):
    inner = f"<div class='v'>{v}</div><div class='l'>{l}</div>" + (f"<div class='petit'>{sous}</div>" if sous else "")
    return f"<a class='carte {cl}' href='{lien}'>{inner}</a>" if lien else f"<div class='carte {cl}'>{inner}</div>"


def bloc(titre, contenu, cl="", ident=None, lien=None):
    """Bloc du tableau de bord (carte pleine largeur avec titre court)."""
    tl = f"<a class='bloc-lien' href='{lien[0]}'>{E(lien[1])} →</a>" if lien else ""
    return (f"<section class='bloc {cl}'" + (f" id='{ident}'" if ident else "") + f"><h2 class='bloc-titre'>{E(titre)}{tl}</h2>{contenu}</section>")


def jauge(valeur, maximum, reserve=None, repere=None, lib_repere=""):
    """Jauge horizontale : barre = valeur ; zone = réserve ; trait = repère (plan à ce jour)."""
    m = max(maximum, 1)
    p = lambda v: f"{max(0, min(100, v / m * 100)):.1f}%"
    o = ["<div class='jauge' role='img' aria-label='jauge'>"]
    if reserve:
        o.append(f"<div class='jauge-reserve' style='width:{p(reserve)}'></div>")
    o.append(f"<div class='jauge-valeur' style='width:{p(valeur)}'></div>")
    if repere is not None:
        o.append(f"<div class='jauge-repere' style='left:{p(repere)}' title='{E(lib_repere)}'></div>")
    o.append("</div>")
    return "".join(o)


def barre_temps(debut, fin, auj, marques=(), zones=()):
    """Barre de saison : partie écoulée, zones (hachurées), marques verticales, repère « aujourd'hui »."""
    tot = (fin - debut).days + 1
    p = lambda d: f"{max(0, min(100, (d - debut).days / tot * 100)):.1f}%"
    w = lambda a, b: f"{max(0, min(100, ((b - a).days + 1) / tot * 100)):.1f}%"
    o = ["<div class='temps'>"]
    for a, b, cl in zones:
        o.append(f"<div class='temps-zone {cl}' style='left:{p(a)};width:{w(a, b)}'></div>")
    ecoule = min(max((auj - debut).days, 0), tot)
    o.append(f"<div class='temps-ecoule' style='width:{ecoule / tot * 100:.1f}%'></div>")
    for d, cl, lib in marques:
        o.append(f"<div class='temps-marque {cl}' style='left:{p(d)}' title='{E(lib)}'></div>")
    if debut <= auj <= fin:
        o.append(f"<div class='temps-auj' style='left:{p(auj)}' title=\"aujourd'hui\"></div>")
    o.append("</div><div class='temps-axe'>")
    d = debut
    while d <= fin:
        if d.day == 1:
            o.append(f"<span style='left:{p(d)}'>{MOIS_FR[d.month]}</span>")
        d += dt.timedelta(days=1)
    o.append("</div>")
    return "".join(o)


def mini_barre(libelle, reel, plan_date, total, fmt=nb, unite=""):
    """Ligne « réel / plan à ce jour / total de saison » : barre = réel, trait = plan à ce jour."""
    m = max(total or 0, reel or 0, plan_date or 0, 1)
    return (f"<div class='mini'><span class='mini-lib'>{E(libelle)}</span>"
            f"<span class='mini-barre'><i class='mini-reel' style='width:{(reel or 0) / m * 100:.1f}%'></i>"
            f"<u class='mini-plan' style='left:{(plan_date or 0) / m * 100:.1f}%'></u></span>"
            f"<span class='mini-val'><b>{fmt(reel)}</b>{unite} / {fmt(plan_date)} · {fmt(total)}{unite}</span></div>")


def sousnav(items, actif):
    return ("<nav class='sousnav'>" + "".join(f"<a href='{u}'" + (" class='actif' aria-current='page'" if u == actif else "") + f">{E(t)}</a>" for u, t in items) + "</nav>")


def classe_temp(t):
    """Classe de température (5 paliers) pour le calendrier ; les teintes viennent du thème."""
    if t is None:
        return "t-na"
    return "t-chaud" if t >= 10 else "t-doux" if t >= 5 else "t-frais" if t >= 0 else "t-froid" if t >= -5 else "t-tresfroid" if t >= -15 else "t-glacial"


def calendrier_saison(jours, debut, fin, auj):
    """Calendrier de saison : une ligne par semaine (lundi → dimanche), une case par jour.
    jours : dict date → {t, prevision, buches, evt, statut, info}. statut : saisi | manquant | futur | avant."""
    d0 = debut - dt.timedelta(days=debut.weekday())
    o = ["<table class='calendrier'><thead><tr><th></th>" + "".join(f"<th>{j}</th>" for j in "LMMJVSD") + "</tr></thead><tbody>"]
    d = d0
    while d <= fin:
        lab = ""
        for k in range(7):
            x = d + dt.timedelta(days=k)
            if x.day == 1 and debut <= x <= fin:
                lab = MOIS_FR[x.month]
        o.append(f"<tr><th>{lab}</th>")
        for k in range(7):
            x = d + dt.timedelta(days=k)
            if not (debut <= x <= fin):
                o.append("<td class='hors'></td>"); continue
            j = jours.get(x, {})
            cl = [classe_temp(j.get("t")), "st-" + j.get("statut", "futur")]
            if j.get("prevision"):
                cl.append("prev")
            if x == auj:
                cl.append("auj")
            if j.get("evt"):
                cl.append("evt-" + j.get("evt_statut", "annonce"))
            b = j.get("buches")
            contenu = (f"<span class='pastille'>{nb(b)}</span>" if b else "")
            if j.get("evt"):
                contenu += "<span class='losange'>◆</span>"
            if j.get("statut") == "manquant":
                contenu += "<span class='croix'>✕</span>"
            if not contenu and (x.day == 1 or x == auj):
                contenu = f"<span class='num'>{x.day}</span>"
            o.append(f"<td class='{' '.join(cl)}' title='{E(j.get('info', x.isoformat()))}'>{contenu}</td>")
        o.append("</tr>")
        d += dt.timedelta(days=7)
    o.append("</tbody></table>")
    return "".join(o)


def legende_calendrier():
    return ("<div class='legende'><span class='leg'><i class='t-chaud'></i>≥ 10 °C</span><span class='leg'><i class='t-doux'></i>5 à 10</span>"
            "<span class='leg'><i class='t-frais'></i>0 à 5</span><span class='leg'><i class='t-froid'></i>−5 à 0</span><span class='leg'><i class='t-tresfroid'></i>−15 à −5</span>"
            "<span class='leg'><i class='t-glacial'></i>&lt; −15</span><br><span class='leg'><i class='prev'></i>prévision</span>"
            "<span class='leg'><i class='auj'></i>aujourd'hui</span><span class='leg'><span class='pastille'>6</span> bûches saisies</span>"
            "<span class='leg'><span class='losange'>◆</span> événement Flex D</span><span class='leg'><span class='croix'>✕</span> jour à saisir</span>"
            "<br>Losange plein : événement couvert par un feu ; contour seul : manqué ou non saisi. Toucher une case affiche le détail.</div>")

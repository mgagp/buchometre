"""Petits graphiques SVG autonomes (aucune librairie, fonctionnent hors ligne).
Chaque fonction renvoie une chaîne <svg>. Les infobulles passent par <title>."""
import html, math

E = html.escape
# Couleurs : aucune valeur ici. Chaque clé renvoie à une variable CSS --g-<clé> définie dans theme/site.css.
CLES = ["reel", "sansfeu", "marc", "buche", "temp", "gris", "vert", "fond_e", "ardoise", "temp_pale", "encre", "gris_bleu", "gris_pale",
        "bleu_pale", "violet_pale", "bleu_fonce", "evt", "plan", "reserve", "zone_creux", "zone_marc", "zone_critique", "cal_sansfeu",
        "cal_extrapole", "pile_rect", "pile_pente", "pile_tri", "pile_trait", "axe"]
COUL = {k: f"var(--g-{k})" for k in CLES}


def coul(x):
    """Clé de couleur (« reel ») ou valeur déjà résolue (« var(--g-reel) », « color-mix(...) ») → valeur CSS."""
    if x in COUL:
        return COUL[x]
    if x.startswith(("var(", "color-mix(")) or x == "none":
        return x
    raise ValueError(f"couleur codée en dur interdite (utiliser une clé du thème) : {x}")


def intensite(cle, r):
    """Teinte d'une clé du thème à r (0..1) d'opacité, sans couleur codée en dur."""
    return f"color-mix(in srgb, {coul(cle)} {max(0, min(1, r)) * 100:.0f}%, transparent)"


def _echelle(vmin, vmax, n=5):
    if vmax == vmin:
        vmax = vmin + 1
    brut = (vmax - vmin) / n
    p = 10 ** math.floor(math.log10(brut))
    pas = min((m * p for m in (1, 2, 2.5, 5, 10) if m * p >= brut), default=10 * p)
    lo = math.floor(vmin / pas) * pas; hi = math.ceil(vmax / pas) * pas
    ticks = []; v = lo
    while v <= hi + 1e-9:
        ticks.append(round(v, 6)); v += pas
    return lo, hi, ticks


def fmt(v):
    s = f"{v:,.0f}" if abs(v) >= 10 or v == int(v) else f"{v:,.1f}"
    return s.replace(",", " ").replace(".", ",")


def series(labels, series, h=300, w=1100, titre_g="", titre_d="", zones=(), etiq_tous=7, liens=None, auj=None, auj_lib="aujourd'hui"):
    """labels : liste de str (axe x). series : dicts {nom, valeurs, couleur, type: line|bar|area, axe: g|d, pointille}.
    zones : liste (i_debut, i_fin, libellé) ombrées. liens : liste d'URL par point (barres cliquables)."""
    ml, mr, mt, mb = 52, 52, 26, 46
    pw, ph = w - ml - mr, h - mt - mb
    n = len(labels)
    def bornes(axe):
        vals = [v for s in series if s.get("axe", "g") == axe for v in s["valeurs"] if v is not None]
        if not vals:
            return None
        lo = min(0, min(vals)); return _echelle(lo, max(vals))
    bg, bd = bornes("g"), bornes("d")
    bw = pw / n
    X = lambda i: ml + bw * (i + 0.5)
    def Y(v, b):
        lo, hi, _ = b; return mt + ph - (v - lo) / (hi - lo) * ph
    o = [f"<svg viewBox='0 0 {w} {h}' class='graphe' role='img' xmlns='http://www.w3.org/2000/svg'>"]
    for z in zones:
        i0, i1, lib = z[:3]; zc = z[3] if len(z) > 3 else 'fond_e'
        o.append(f"<rect x='{ml + bw * i0:.1f}' y='{mt}' width='{bw * (i1 - i0 + 1):.1f}' height='{ph}' style='fill:{coul(zc)}'><title>{E(lib)}</title></rect>"
                 + (f"<text x='{ml + bw * (i0 + i1 + 1) / 2:.1f}' y='{mt + 14}' text-anchor='middle' class='ax'>{E(lib)}</text>" if len(z) < 5 or z[4] else ""))
    if bg:
        for t in bg[2]:
            y = Y(t, bg); o.append(f"<line x1='{ml}' x2='{ml + pw}' y1='{y:.1f}' y2='{y:.1f}' class='grille'/>"
                                   f"<text x='{ml - 6}' y='{y + 4:.1f}' text-anchor='end' class='ax'>{fmt(t)}</text>")
    if bd:
        for t in bd[2]:
            y = Y(t, bd); o.append(f"<text x='{ml + pw + 6}' y='{y + 4:.1f}' class='ax'>{fmt(t)}</text>")
    if bg and bg[0] < 0 < bg[1]:
        y = Y(0, bg); o.append(f"<line x1='{ml}' x2='{ml + pw}' y1='{y:.1f}' y2='{y:.1f}' class='axe0'/>")
    pas = max(1, round(n / (pw / 60)))
    for i, l in enumerate(labels):
        if i % pas == 0:
            o.append(f"<text x='{X(i):.1f}' y='{mt + ph + 16}' text-anchor='middle' class='ax'>{E(l)}</text>")
    o.append(f"<text x='{ml - 40}' y='{mt - 10}' class='ax b'>{E(titre_g)}</text>")
    o.append(f"<text x='{ml + pw + 40}' y='{mt - 10}' text-anchor='end' class='ax b'>{E(titre_d)}</text>")
    barres = [s for s in series if s.get("type") == "bar"]
    for k, s in enumerate(barres):
        b = bg if s.get("axe", "g") == "g" else bd
        larg = bw * 0.8 / len(barres)
        for i, v in enumerate(s["valeurs"]):
            if not v:
                continue
            y0, y1 = Y(0, b), Y(v, b)
            r = (f"<rect x='{ml + bw * i + bw * 0.1 + k * larg:.1f}' y='{min(y0, y1):.1f}' width='{max(larg, 1):.1f}' "
                 f"height='{abs(y0 - y1):.1f}' style='fill:{coul(s['couleur'])}' opacity='{s.get('opacite', 0.55)}'>"
                 f"<title>{E(labels[i])} – {E(s['nom'])} : {fmt(v)}</title></rect>")
            o.append(f"<a href='{E(liens[i])}'>{r}</a>" if liens else r)
    for s in series:
        if s.get("type") == "bar":
            continue
        b = bg if s.get("axe", "g") == "g" else bd
        segs, cur = [], []
        for i, v in enumerate(s["valeurs"]):
            if v is None:
                if cur: segs.append(cur); cur = []
            else:
                cur.append((X(i), Y(v, b), i, v))
        if cur: segs.append(cur)
        dash = " stroke-dasharray='5 4'" if s.get("pointille") else ""
        for seg in segs:
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in seg)
            if s.get("type") == "area":
                y0 = Y(0, b)
                o.append(f"<polygon points='{seg[0][0]:.1f},{y0:.1f} {pts} {seg[-1][0]:.1f},{y0:.1f}' style='fill:{coul(s['couleur'])}' opacity='0.18'/>")
            o.append(f"<polyline points='{pts}' fill='none' style='stroke:{coul(s['couleur'])}' stroke-width='{s.get('epaisseur', 2)}'{dash}/>")
            if s.get("points", n <= 60):
                for x, y, i, v in seg:
                    o.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.6' style='fill:{coul(s['couleur'])}'><title>{E(labels[i])} – {E(s['nom'])} : {fmt(v)}</title></circle>")
    if auj is not None and 0 <= auj < n:
        o.append(f"<line x1='{X(auj):.1f}' x2='{X(auj):.1f}' y1='{mt - 4}' y2='{mt + ph}' class='ligne-auj'/>"
                 f"<text x='{X(auj) + 4:.1f}' y='{mt + 8}' class='ax b'>{E(auj_lib)}</text>")
    o.append(legende(series, ml, h - 10))
    o.append("</svg>")
    return "".join(o)


def legende(series, x, y):
    o, cx = [], x
    for s in series:
        if s.get("sans_legende"):
            continue
        o.append(f"<rect x='{cx}' y='{y - 9}' width='12' height='10' style='fill:{coul(s['couleur'])}' opacity='{0.6 if s.get('type') == 'bar' else 1}'/>"
                 f"<text x='{cx + 16}' y='{y}' class='ax'>{E(s['nom'])}</text>")
        cx += 30 + 6.3 * len(s["nom"])
    return "".join(o)


def nuage(groupes, lignes=(), h=360, w=540, tx="", ty="", xlim=None, ylim=None):
    """groupes : dicts {nom, couleur, points: [(x, y, info)]}. lignes : dicts {nom, couleur, x0, x1, f}."""
    ml, mr, mt, mb = 52, 16, 20, 56
    pw, ph = w - ml - mr, h - mt - mb
    xs = [p[0] for g in groupes for p in g["points"]]; ys = [p[1] for g in groupes for p in g["points"]]
    bx = _echelle(*(xlim or (min(xs), max(xs)))); by = _echelle(*(ylim or (min(0, min(ys)), max(ys))))
    X = lambda v: ml + (v - bx[0]) / (bx[1] - bx[0]) * pw
    Y = lambda v: mt + ph - (v - by[0]) / (by[1] - by[0]) * ph
    o = [f"<svg viewBox='0 0 {w} {h}' class='graphe' xmlns='http://www.w3.org/2000/svg'>"]
    for t in by[2]:
        o.append(f"<line x1='{ml}' x2='{ml + pw}' y1='{Y(t):.1f}' y2='{Y(t):.1f}' class='grille'/><text x='{ml - 6}' y='{Y(t) + 4:.1f}' text-anchor='end' class='ax'>{fmt(t)}</text>")
    for t in bx[2]:
        o.append(f"<line y1='{mt}' y2='{mt + ph}' x1='{X(t):.1f}' x2='{X(t):.1f}' class='grille'/><text x='{X(t):.1f}' y='{mt + ph + 16}' text-anchor='middle' class='ax'>{fmt(t)}</text>")
    o.append(f"<text x='{ml + pw / 2}' y='{h - 24}' text-anchor='middle' class='ax b'>{E(tx)}</text>"
             f"<text x='12' y='{mt + ph / 2}' transform='rotate(-90 12 {mt + ph / 2})' text-anchor='middle' class='ax b'>{E(ty)}</text>")
    for g in groupes:
        for x, y, info in g["points"]:
            o.append(f"<circle cx='{X(x):.1f}' cy='{Y(y):.1f}' r='4' style='fill:{coul(g['couleur'])}' opacity='0.7'><title>{E(info)}</title></circle>")
    for l in lignes:
        pts = [(l["x0"] + (l["x1"] - l["x0"]) * k / 20) for k in range(21)]
        o.append("<polyline fill='none' style='stroke:{}' stroke-width='2' {} points='{}'/>".format(
            coul(l["couleur"]), "stroke-dasharray='6 4'" if l.get("pointille") else "",
            " ".join(f"{X(x):.1f},{Y(l['f'](x)):.1f}" for x in pts)))
    o.append(legende([{"nom": g["nom"], "couleur": g["couleur"]} for g in groupes] + list(lignes), ml, h - 6))
    o.append("</svg>")
    return "".join(o)


def calendrier(jours, valeur, couleur, info, lien, vmax=None):
    """Calendrier mensuel (colonnes = semaines). jours : liste de dicts avec 'date'."""
    import datetime as dt
    vmax = vmax or max(valeur(j) for j in jours) or 1
    d0 = jours[0]["date"]; d0 = d0 - dt.timedelta(days=d0.weekday())
    c = 15; ml, mt = 30, 22
    nsem = (jours[-1]["date"] - d0).days // 7 + 1
    w, h = ml + nsem * c + 10, mt + 7 * c + 10
    o = [f"<svg viewBox='0 0 {w} {h}' class='graphe cal' xmlns='http://www.w3.org/2000/svg'>"]
    for k, n in enumerate("LMMJVSD"):
        o.append(f"<text x='{ml - 8}' y='{mt + k * c + 11}' text-anchor='end' class='ax'>{n}</text>")
    mois_vus = set()
    for j in jours:
        d = j["date"]; s = (d - d0).days // 7; k = d.weekday()
        if (d.year, d.month) not in mois_vus and d.day <= 7:
            mois_vus.add((d.year, d.month)); o.append(f"<text x='{ml + s * c}' y='{mt - 8}' class='ax'>{d.strftime('%Y-%m')}</text>")
        v = valeur(j); fill = couleur(j, v / vmax)
        o.append(f"<a href='{E(lien(j))}'><rect x='{ml + s * c}' y='{mt + k * c}' width='{c - 2}' height='{c - 2}' rx='2' style='fill:{coul(fill)}'>"
                 f"<title>{E(info(j))}</title></rect></a>")
    o.append("</svg>")
    return "".join(o)


def courbes(lignes, h=320, w=540, tx="", ty=""):
    """lignes : dicts {nom, couleur, pts: [(x, y)]} avec x et y dans [0, 1] (affichés en %)."""
    ml, mr, mt, mb = 52, 16, 16, 56
    pw, ph = w - ml - mr, h - mt - mb
    X = lambda v: ml + v * pw; Y = lambda v: mt + ph - v * ph
    o = [f"<svg viewBox='0 0 {w} {h}' class='graphe' xmlns='http://www.w3.org/2000/svg'>"]
    for t in range(0, 101, 20):
        o.append(f"<line x1='{ml}' x2='{ml + pw}' y1='{Y(t / 100):.1f}' y2='{Y(t / 100):.1f}' class='grille'/><text x='{ml - 6}' y='{Y(t / 100) + 4:.1f}' text-anchor='end' class='ax'>{t} %</text>"
                 f"<text x='{X(t / 100):.1f}' y='{mt + ph + 16}' text-anchor='middle' class='ax'>{t} %</text>")
    o.append(f"<line x1='{X(0)}' y1='{Y(0)}' x2='{X(1)}' y2='{Y(1)}' class='diag'/>")
    o.append(f"<text x='{ml + pw / 2}' y='{h - 24}' text-anchor='middle' class='ax b'>{E(tx)}</text>"
             f"<text x='12' y='{mt + ph / 2}' transform='rotate(-90 12 {mt + ph / 2})' text-anchor='middle' class='ax b'>{E(ty)}</text>")
    for l in lignes:
        o.append(f"<polyline fill='none' style='stroke:{coul(l['couleur'])}' stroke-width='2' points='" + " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in l["pts"]) + "'/>")
    o.append(legende(lignes, ml, h - 6)); o.append("</svg>")
    return "".join(o)

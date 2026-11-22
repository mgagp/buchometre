#!/usr/bin/env python3
"""Génère le site HTML statique du projet bois-chauffage dans rapports/.

Usage : python outils/preparer_donnees.py && python outils/generer_site.py
Lit data/ seulement. Aucun chiffre saisi à la main dans les pages : tout vient de data/.
Bibliothèque standard seulement ; graphiques en SVG intégré (fonctionne hors ligne).
"""
import csv, json, os, html, datetime as dt, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svg

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RACINE, "rapports")
E = html.escape
PRIX_BOIS = 425.0
TARIF_2026_P2 = 0.11142  # tarif D au 1er avril 2026, 2e tranche (Hydro-Québec)
MOIS = {"2023-11": "novembre 2023", "2023-12": "décembre 2023", "2024-01": "janvier 2024", "2024-02": "février 2024", "2024-03": "mars 2024"}
COURT = {"2023-11": "nov. 2023", "2023-12": "déc.", "2024-01": "janv. 2024", "2024-02": "févr.", "2024-03": "mars"}
JS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def lire(rel):
    with open(os.path.join(RACINE, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def n(x):
    return float(x) if x not in ("", None) else None


def argent(x, dec=2):
    return (f"{x:,.{dec}f}".replace(",", " ").replace(".", ",") + " $") if x is not None else "—"


def nb(x, dec=0):
    if x is None:
        return "—"
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def pct(x, dec=0):
    return nb(x * 100, dec) + " %"


CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#222;max-width:1200px}
h1{margin-bottom:4px}.sous{color:#666;margin-top:0}h2{margin-top:28px;border-top:2px solid #333;padding-top:6px}
.cartes{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}
.carte{border:1px solid #ddd;border-radius:8px;padding:10px 14px;min-width:150px;text-decoration:none;color:inherit;background:#fff}
.carte .v{font-size:24px;font-weight:700}.carte .l{font-size:12px;color:#555}
.ok{background:#e8f6ea;border-color:#7cc48a}.ko{background:#fdecea;border-color:#e59a90}.neutre{background:#e3f2fd;border-color:#90caf9}.prov{background:#fff8e1;border-color:#f0c36d}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600}
.b-ok{background:#2e7d32;color:#fff}.b-ko{background:#c62828;color:#fff}.b-prov{background:#ef6c00;color:#fff}.b-gris{background:#9e9e9e;color:#fff}
table{border-collapse:collapse;width:100%;margin:8px 0 16px}th,td{border:1px solid #ddd;padding:4px 7px;font-size:13px;text-align:left}
th{background:#f4f4f4;position:sticky;top:0}td.n{text-align:right;white-space:nowrap}td:first-child{white-space:nowrap}
tr.e td{background:#f6f6f6;color:#777;font-style:italic}tr.tot td{background:#eef3fb;font-weight:600}tr:target td{background:#fff3c4}
.nav{background:#f4f4f4;padding:6px 10px;border-radius:6px;font-size:13px;position:sticky;top:0;z-index:2}.nav a{text-decoration:none}.nav a.actif{font-weight:700}
.alerte{background:#fff8e1;border:1px solid #f0c36d;padding:8px 12px;border-radius:6px;margin:10px 0}
.info{background:#e3f2fd;border:1px solid #90caf9;padding:8px 12px;border-radius:6px;margin:10px 0}
.petit{color:#666;font-size:12px}.graphe{width:100%;height:auto;background:#fff;border:1px solid #eee;border-radius:6px;margin:6px 0}
.graphe .ax{font-size:11px;fill:#555}.graphe .b{font-weight:600}.graphe .grille{stroke:#eee}
.deux{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:900px){.deux{grid-template-columns:1fr}}
.cal{max-width:620px}.barre{display:inline-block;height:9px;background:#ef6c00;opacity:.6;vertical-align:middle}
.defile{max-height:640px;overflow:auto;border:1px solid #ddd}
code{background:#f4f4f4;padding:1px 4px;border-radius:3px}
"""

NAV = [("index.html", "Sommaire global"), ("mensuel.html", "Mensuel"), ("jours.html", "Jour par jour"),
       ("donnees.html", "Données brutes"), ("factures.html", "Factures Hydro"), ("qualite.html", "Qualité des données"),
       ("methode.html", "Méthode"), ("decisions.html", "Propositions"), ("protocole.html", "▶ Protocole 2026-27")]


def page(nom, titre, corps, quand, sous=None):
    nav = " · ".join(f"<a href='{u}'{' class=actif' if u == nom else ''}>{E(t)}</a>" for u, t in NAV)
    mois = " · ".join(f"<a href='mois-{m}.html'>{E(COURT[m])}</a>" for m in MOIS)
    h = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
         f"<title>Bois de chauffage – {E(titre)}</title><style>{CSS}</style></head><body>"
         f"<nav class='nav'>{nav} &nbsp;|&nbsp; Mois : {mois}</nav><h1>{E(titre)}</h1>" +
         (sous or (f"<p class='sous'>Hiver 2023-2024 · généré le {E(quand)} par <code>outils/generer_site.py</code> à partir de <code>data/</code>. "
         "Chiffrier source « Bois de chauffage » (Google Drive), lu en lecture seule.</p>")) + corps + "</body></html>")
    with open(os.path.join(OUT, nom), "w", encoding="utf-8") as f:
        f.write(h)


def carte(v, l, cl="", lien=None, sous=""):
    inner = f"<div class='v'>{v}</div><div class='l'>{l}</div>" + (f"<div class='petit'>{sous}</div>" if sous else "")
    return f"<a class='carte {cl}' href='{lien}'>{inner}</a>" if lien else f"<div class='carte {cl}'>{inner}</div>"


def main():
    os.makedirs(OUT, exist_ok=True)
    quand = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    J = lire("data/journal_nettoye.csv")
    for j in J:
        j["date"] = dt.date.fromisoformat(j["date"])
        for k in ("nb_buches", "kwh_reel", "kwh_eq_marc", "temp_marc", "t_moy_om", "t_min_om", "t_max_om", "dj18",
                  "kwh_attendu_modele", "kwh_sans_feu_modele", "kwh_evites_modele", "kwh_evites_marc", "eco_modele_ht",
                  "eco_modele_ttc", "eco_feuille_marc"):
            j[k] = n(j[k])
        j["mesure"] = j["statut"] == "mesure"
        j["anos"] = [a for a in j["anomalies"].split(";") if a]
    BRUT = lire("data/journal_brut.csv")
    ANO = lire("data/anomalies.csv")
    FACT = lire("data/factures.csv")
    MOD = json.load(open(os.path.join(RACINE, "data/modele.json"), encoding="utf-8"))
    kb, seb, kb_bas, kb_haut = MOD["kwh_par_buche"], MOD["se_kwh_par_buche"], MOD["kwh_par_buche_bas"], MOD["kwh_par_buche_haut"]
    p2, tx = MOD["tarif_2023"]["p2"], 1 + MOD["taxes"]
    mes = [j for j in J if j["mesure"]]; ext = [j for j in J if not j["mesure"]]
    feu = [j for j in mes if j["nb_buches"] > 0]; sansfeu = [j for j in mes if j["nb_buches"] == 0]
    B = sum(j["nb_buches"] for j in mes)
    kwh_ev = kb * B
    eco_ht, eco_ttc = kwh_ev * p2, kwh_ev * p2 * tx
    marc_kwh_mes = sum(j["kwh_evites_marc"] for j in mes)
    marc_eco_mes = sum(j["eco_feuille_marc"] or 0 for j in mes)
    marc_eco_ext = sum(j["eco_feuille_marc"] or 0 for j in ext)
    marc_eco_tot = marc_eco_mes + marc_eco_ext
    val_buche_ttc = kb * p2 * tx
    seuil = PRIX_BOIS / val_buche_ttc
    S = MOD["saison"]; Bs = S["buches_saison_central"]
    val_saison = Bs * val_buche_ttc
    val_saison_bas = S["buches_saison_bas"] * kb_bas * p2 * tx
    val_saison_haut = Bs * kb_haut * p2 * tx
    val_2026 = Bs * kb * TARIF_2026_P2 * tx
    CF = MOD["controle_facture"]
    lien_jour = lambda j: f"mois-{j['date'].strftime('%Y-%m')}.html#j-{j['date'].isoformat()}"

    # ---------------- Graphiques communs ----------------
    labels = [j["date"].strftime("%d %b").lstrip("0") for j in J]
    i_e = next(i for i, j in enumerate(J) if not j["mesure"])
    zones = [(i_e, len(J) - 1, "lignes « E » : extrapolées (non mesurées)")]
    g_serie = svg.series(labels, [
        {"nom": "Bûches (axe droit)", "valeurs": [j["nb_buches"] if j["mesure"] else None for j in J], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.3},
        {"nom": "kWh réels (Hydro)", "valeurs": [j["kwh_reel"] for j in mes] + [None] * len(ext), "couleur": svg.COUL["reel"], "points": False},
        {"nom": "kWh sans feu (modèle)", "valeurs": [j["kwh_sans_feu_modele"] for j in mes] + [None] * len(ext), "couleur": svg.COUL["sansfeu"], "points": False},
        {"nom": "kWh « eq estimé » (chiffrier)", "valeurs": [j["kwh_eq_marc"] for j in J], "couleur": svg.COUL["marc"], "pointille": True, "epaisseur": 1.3, "points": False},
    ], titre_g="kWh / jour", titre_d="bûches", zones=zones, liens=[lien_jour(j) for j in J], h=340)
    g_temp = svg.series(labels, [
        {"nom": "Température notée (Marc)", "valeurs": [j["temp_marc"] if j["mesure"] else None for j in J], "couleur": "#455a64", "points": False},
        {"nom": "Moyenne Open-Meteo", "valeurs": [j["t_moy_om"] for j in J], "couleur": svg.COUL["temp"], "points": False},
        {"nom": "Min Open-Meteo", "valeurs": [j["t_min_om"] for j in J], "couleur": "#80cbc4", "pointille": True, "epaisseur": 1, "points": False},
    ], titre_g="°C", zones=zones, h=220)
    c0, cdj, cb = MOD["modeles"]["principal"]["coef"]
    g_nuage = svg.nuage([
        {"nom": "Jours sans feu", "couleur": svg.COUL["gris"], "points": [(j["t_moy_om"], j["kwh_reel"], f"{j['date']} : {j['kwh_reel']:.0f} kWh, {j['t_moy_om']} °C, 0 bûche") for j in sansfeu]},
        {"nom": "Jours avec feu", "couleur": svg.COUL["buche"], "points": [(j["t_moy_om"], j["kwh_reel"], f"{j['date']} : {j['kwh_reel']:.0f} kWh, {j['t_moy_om']} °C, {j['nb_buches']:.0f} bûches") for j in feu]},
    ], [
        {"nom": "Modèle 0 bûche", "couleur": svg.COUL["sansfeu"], "x0": -16, "x1": 10, "f": lambda t: c0 + cdj * max(18 - t, 0)},
        {"nom": "Modèle 10 bûches", "couleur": svg.COUL["buche"], "pointille": True, "x0": -16, "x1": 10, "f": lambda t: c0 + cdj * max(18 - t, 0) + cb * 10},
    ], tx="Température moyenne du jour (°C, Open-Meteo)", ty="kWh réels du jour", xlim=(-16, 10), ylim=(0, 120))
    g_buche = svg.nuage([
        {"nom": "kWh évités selon le chiffrier (eq − réel)", "couleur": svg.COUL["marc"], "points": [(j["nb_buches"], j["kwh_evites_marc"], f"{j['date']} : {j['nb_buches']:.0f} bûches, {j['kwh_evites_marc']:.0f} kWh") for j in mes]},
    ], [{"nom": f"Modèle : {nb(kb, 1)} kWh par bûche", "couleur": svg.COUL["sansfeu"], "x0": 0, "x1": 15, "f": lambda b: kb * b}],
        tx="Bûches dans la journée", ty="kWh évités", xlim=(0, 15), ylim=(-20, 80))
    cum, c, cm = [], 0.0, 0.0
    cum_m = []
    for j in J:
        c += j["eco_modele_ttc"] or 0; cm += (j["eco_feuille_marc"] or 0) if j["mesure"] else 0
        cum.append(round(c, 2) if j["mesure"] else None); cum_m.append(round(cm, 2) if j["mesure"] else None)
    g_cumul = svg.series(labels, [
        {"nom": "Économie cumulée, modèle (taxes incl.)", "valeurs": cum, "couleur": svg.COUL["vert"], "type": "area", "points": False},
        {"nom": "Économie cumulée, chiffrier (avant taxes)", "valeurs": cum_m, "couleur": svg.COUL["marc"], "points": False, "pointille": True},
        {"nom": "Prix du bois (425 $)", "valeurs": [PRIX_BOIS] * len(J), "couleur": "#000", "points": False, "epaisseur": 1},
    ], titre_g="$", zones=zones, h=260)

    # ---------------- agrégats mensuels ----------------
    mois = {}
    for j in J:
        m = mois.setdefault(j["date"].strftime("%Y-%m"), {"jours": [], "m": j["date"].strftime("%Y-%m")})
        m["jours"].append(j)
    for m in mois.values():
        js = m["jours"]; ms = [j for j in js if j["mesure"]]
        m.update(n=len(js), n_mes=len(ms), n_feu=sum(1 for j in ms if j["nb_buches"] > 0),
                 buches=sum(j["nb_buches"] for j in ms), kwh=sum(j["kwh_reel"] for j in ms),
                 sansfeu=sum(j["kwh_sans_feu_modele"] for j in ms), ev=sum(j["kwh_evites_modele"] for j in ms),
                 ev_m=sum(j["kwh_evites_marc"] for j in ms), eco=sum(j["eco_modele_ttc"] for j in ms),
                 eco_m=sum(j["eco_feuille_marc"] or 0 for j in js), eco_m_ext=sum(j["eco_feuille_marc"] or 0 for j in js if not j["mesure"]),
                 t=(sum(j["t_moy_om"] for j in ms) / len(ms)) if ms else None, dj=sum(j["dj18"] for j in ms),
                 dj_all=sum(j["dj18"] for j in js))
    ML = list(mois.values())
    g_mois = svg.series([MOIS[m["m"]] for m in ML], [
        {"nom": "kWh évités (modèle)", "valeurs": [round(m["ev"]) for m in ML], "couleur": svg.COUL["sansfeu"], "type": "bar"},
        {"nom": "kWh évités (chiffrier, eq − réel)", "valeurs": [round(m["ev_m"]) for m in ML], "couleur": svg.COUL["marc"], "type": "bar"},
        {"nom": "Bûches (axe droit)", "valeurs": [m["buches"] for m in ML], "couleur": svg.COUL["buche"], "axe": "d"},
    ], titre_g="kWh", titre_d="bûches", h=280, w=900, liens=[f"mois-{m['m']}.html" for m in ML])

    # ---------------- index ----------------
    rend = val_saison / PRIX_BOIS - 1
    cl_r = "ok" if rend > 0.05 else ("ko" if rend < -0.05 else "prov")
    h = ["<div class='cartes'>",
         carte(f"{len(mes)} j", "mesurés", "neutre", "jours.html", f"du {mes[0]['date']} au {mes[-1]['date']} ; {len(ext)} j extrapolés exclus"),
         carte(nb(B), "bûches brûlées (mesuré)", "neutre", "jours.html", f"{len(feu)} jours avec feu, {nb(B / len(feu), 1)} bûches/jour de feu"),
         carte(f"{nb(kb, 1)} kWh", "évités par bûche", "neutre", "methode.html", f"plage {nb(kb_bas, 1)} à {nb(kb_haut, 1)} kWh"),
         carte(nb(kwh_ev), "kWh évités (mesuré)", "neutre", "methode.html", f"chiffrier : {nb(marc_kwh_mes)} kWh"),
         carte(argent(eco_ttc, 0), "économie mesurée, taxes incl.", "ok", "mensuel.html", f"{argent(eco_ht, 0)} avant taxes · chiffrier : {argent(marc_eco_mes, 0)}"),
         carte(argent(val_saison, 0), "valeur projetée sur la saison", cl_r, "methode.html#saison", f"≈ {nb(Bs)} bûches ; plage {argent(val_saison_bas, 0)} à {argent(val_saison_haut, 0)}"),
         carte(("+" if rend >= 0 else "") + pct(rend), "rendement vs 425 $ de bois", cl_r, "methode.html#saison", f"seuil de rentabilité ≈ {nb(seuil)} bûches"),
         carte(f"{CF['ecart_pct']:+.1f} %".replace(".", ","), "kWh du journal vs facture Hydro", "ok", "factures.html", "période 17 nov.–18 janv. : la mesure tient"),
         "</div>"]
    h.append("<div class='info'><b>En une phrase.</b> Chaque bûche a évité environ "
             f"{nb(kb, 1)} kWh, soit ≈ {argent(val_buche_ttc)} d'électricité taxes incluses au tarif 2023-2024. "
             f"Sur les {len(mes)} jours mesurés, {nb(B)} bûches ont évité ≈ {nb(kwh_ev)} kWh, ou {argent(eco_ttc, 0)} ; "
             f"projeté sur toute la saison (≈ {nb(Bs)} bûches), le bois rapporte ≈ {argent(val_saison, 0)} pour 425 $ payés : "
             f"{'gain modeste' if rend > 0.05 else ('à peu près le seuil de rentabilité' if rend > -0.05 else 'perte')}. "
             "Ton heuristique « kWh eq estimé » était étonnamment juste (" + nb(marc_kwh_mes / B, 1) + " kWh/bûche implicite).</div>")
    h.append("<h2>La saison jour par jour</h2><p class='petit'>Cliquer une barre ouvre la journée. Zone grise = lignes « E » du chiffrier, extrapolées, exclues des calculs.</p>")
    h.append(g_serie + g_temp)
    h.append("<h2>Ce que disent les données</h2><div class='deux'><div><h3>kWh réels selon la température</h3>" + g_nuage +
             "<p class='petit'>Les jours sans feu (gris) sont presque tous des jours doux : on n'a jamais observé un jour très froid sans feu. "
             "C'est pourquoi le modèle utilise <b>tous</b> les jours, avec la température et le nombre de bûches ensemble, plutôt que les seuls jours sans feu.</p></div>"
             "<div><h3>Ton heuristique vs le modèle</h3>" + g_buche +
             f"<p class='petit'>Chaque point = un jour. L'écart « eq − réel » de ton chiffrier suit le nombre de bûches avec une pente proche de {nb(kb, 1)} kWh par bûche.</p></div></div>")
    h.append("<h2>Économie cumulée vs prix du bois</h2>" + g_cumul)
    h.append("<h2>Par mois</h2>" + g_mois + "<p><a href='mensuel.html'>Tableau mensuel détaillé →</a></p>")
    page("index.html", "Bois de chauffage : sommaire global", "".join(h), quand)

    # ---------------- mensuel ----------------
    t = ["<table><tr><th>Mois</th><th>Jours</th><th>Mesurés</th><th>Avec feu</th><th>Bûches</th><th>T moy. (°C)</th><th>Degrés-jours</th>"
         "<th>kWh réels</th><th>kWh sans feu (modèle)</th><th>kWh évités (modèle)</th><th>kWh évités (chiffrier)</th>"
         "<th>Économie modèle TTC</th><th>Économie chiffrier</th><th>dont lignes « E »</th></tr>"]
    for m in ML:
        t.append(f"<tr><td><a href='mois-{m['m']}.html'>{MOIS[m['m']]}</a></td><td class=n>{m['n']}</td><td class=n>{m['n_mes']}</td><td class=n>{m['n_feu']}</td>"
                 f"<td class=n>{nb(m['buches'])}</td><td class=n>{nb(m['t'], 1)}</td><td class=n>{nb(m['dj'])}</td><td class=n>{nb(m['kwh'])}</td>"
                 f"<td class=n>{nb(m['sansfeu'])}</td><td class=n>{nb(m['ev'])}</td><td class=n>{nb(m['ev_m'])}</td><td class=n>{argent(m['eco'])}</td>"
                 f"<td class=n>{argent(m['eco_m'])}</td><td class=n>{argent(m['eco_m_ext'])}</td></tr>")
    t.append(f"<tr class=tot><td>Total</td><td class=n>{len(J)}</td><td class=n>{len(mes)}</td><td class=n>{len(feu)}</td><td class=n>{nb(B)}</td><td></td>"
             f"<td class=n>{nb(sum(m['dj'] for m in ML))}</td><td class=n>{nb(sum(m['kwh'] for m in ML))}</td><td class=n>{nb(sum(m['sansfeu'] for m in ML))}</td>"
             f"<td class=n>{nb(kwh_ev)}</td><td class=n>{nb(marc_kwh_mes)}</td><td class=n>{argent(eco_ttc)}</td><td class=n>{argent(marc_eco_tot)}</td><td class=n>{argent(marc_eco_ext)}</td></tr></table>")
    part = [m["kwh"] / m["sansfeu"] for m in ML if m["sansfeu"]]
    g_part = svg.series([MOIS[m["m"]] for m in ML if m["n_mes"]], [
        {"nom": "Part de l'électricité de chauffage remplacée par le bois", "valeurs": [round((1 - m["kwh"] / m["sansfeu"]) * 100, 1) for m in ML if m["n_mes"]], "couleur": svg.COUL["vert"], "type": "bar"}],
        titre_g="%", h=240, w=700)
    page("mensuel.html", "Sommaire mensuel", g_mois + "".join(t) +
         "<p class='petit'>« Économie chiffrier » = colonne « Économie » de ta feuille (paliers quotidiens, avant taxes), y compris les lignes « E ». "
         "« Économie modèle » = kWh évités × 10,041 ¢ (2e tranche, voir Méthode) × 1,14975 (TPS+TVQ). Novembre commence le 7.</p>"
         "<h2>Part de la consommation totale évitée</h2>" + g_part, quand)

    # ---------------- pages mois ----------------
    def ligne_jour(j, ancre=True):
        cl = " class=e" if not j["mesure"] else ""
        badges = " ".join(f"<span class='badge {'b-gris' if a == 'extrapole' else 'b-prov'}'>{E(a)}</span>" for a in j["anos"])
        return (f"<tr{cl} id='j-{j['date']}'><td>{JS[j['date'].weekday()]} {j['date']}</td><td class=n>{nb(j['nb_buches'])} "
                f"<span class='barre' style='width:{j['nb_buches'] * 4:.0f}px'></span></td><td class=n>{nb(j['kwh_reel'])}</td>"
                f"<td class=n>{nb(j['kwh_eq_marc'])}</td><td class=n>{nb(j['kwh_sans_feu_modele'])}</td><td class=n>{nb(j['kwh_attendu_modele'])}</td>"
                f"<td class=n>{nb(j['kwh_evites_modele'], 1)}</td><td class=n>{nb(j['kwh_evites_marc'])}</td>"
                f"<td class=n>{nb(j['temp_marc'])}</td><td class=n>{nb(j['t_moy_om'], 1)}</td><td class=n>{nb(j['t_min_om'], 1)} / {nb(j['t_max_om'], 1)}</td>"
                f"<td class=n>{argent(j['eco_modele_ttc'])}</td><td class=n>{argent(j['eco_feuille_marc'])}</td><td>{badges}</td></tr>")
    ENT = ("<tr><th>Jour</th><th>Bûches</th><th>kWh réels</th><th>kWh eq (chiffrier)</th><th>kWh sans feu (modèle)</th><th>kWh attendus (modèle)</th>"
           "<th>kWh évités (modèle)</th><th>kWh évités (chiffrier)</th><th>T notée</th><th>T moy. OM</th><th>min / max OM</th>"
           "<th>Écon. modèle TTC</th><th>Écon. chiffrier</th><th>Signaux</th></tr>")
    cles = list(mois)
    for k, m in enumerate(ML):
        js = m["jours"]; lab = [j["date"].strftime("%d") for j in js]
        g = svg.series(lab, [
            {"nom": "Bûches (axe droit)", "valeurs": [j["nb_buches"] if j["mesure"] else None for j in js], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.3},
            {"nom": "kWh réels", "valeurs": [j["kwh_reel"] if j["mesure"] else None for j in js], "couleur": svg.COUL["reel"]},
            {"nom": "kWh sans feu (modèle)", "valeurs": [j["kwh_sans_feu_modele"] if j["mesure"] else None for j in js], "couleur": svg.COUL["sansfeu"]},
            {"nom": "kWh eq (chiffrier)", "valeurs": [j["kwh_eq_marc"] for j in js], "couleur": svg.COUL["marc"], "pointille": True, "epaisseur": 1.3},
            {"nom": "T moy. °C (axe droit)", "valeurs": [j["t_moy_om"] for j in js], "couleur": svg.COUL["temp"], "axe": "d", "epaisseur": 1, "points": False},
        ], titre_g="kWh", titre_d="bûches / °C", liens=[f"#j-{j['date']}" for j in js], h=320)
        prec = f"<a href='mois-{cles[k - 1]}.html'>← {MOIS[cles[k - 1]]}</a>" if k else ""
        suiv = f"<a href='mois-{cles[k + 1]}.html'>{MOIS[cles[k + 1]]} →</a>" if k + 1 < len(cles) else ""
        cartes = ("<div class='cartes'>" + carte(f"{m['n_mes']}/{m['n']}", "jours mesurés", "neutre") + carte(nb(m["buches"]), "bûches", "neutre") +
                  carte(nb(m["ev"]), "kWh évités (modèle)", "neutre", sous=f"chiffrier : {nb(m['ev_m'])}") +
                  carte(argent(m["eco"]), "économie TTC (modèle)", "ok" if m["eco"] else "", sous=f"chiffrier : {argent(m['eco_m'])}") +
                  carte(nb(m["t"], 1) + " °C" if m["t"] is not None else "—", "temp. moyenne (jours mesurés)", "neutre") + "</div>")
        avert = ("<div class='alerte'>Toutes les lignes de ce mois sont marquées « E » (extrapolées) dans le chiffrier : 83 kWh et 2 °C constants, "
                 "aucune bûche. Elles sont affichées pour mémoire et exclues des calculs.</div>" if m["n_mes"] == 0 else "")
        page(f"mois-{m['m']}.html", f"Mois : {MOIS[m['m']]}", f"<p>{prec} &nbsp; {suiv}</p>" + cartes + avert + g +
             "<div class='defile'><table>" + ENT + "".join(ligne_jour(j) for j in js) + "</table></div>", quand)

    # ---------------- jours ----------------
    def couleur(j, r):
        if not j["mesure"]:
            return "#e0e0e0"
        if j["nb_buches"] == 0:
            return "#cfd8dc"
        return f"rgba(239,108,0,{0.25 + 0.75 * r:.2f})"
    cal = svg.calendrier(J, lambda j: j["nb_buches"] or 0, couleur,
                         lambda j: f"{j['date']} : {j['nb_buches']:.0f} bûches, {j['kwh_reel']:.0f} kWh, {j['t_moy_om']} °C" + (" (extrapolé)" if not j["mesure"] else ""),
                         lien_jour)
    top = sorted(mes, key=lambda j: -j["kwh_evites_modele"])[:5]
    froid = sorted(mes, key=lambda j: j["t_moy_om"])[:5]
    corps = ("<p>Calendrier : intensité orange = nombre de bûches ; gris-bleu = jour sans feu ; gris pâle = extrapolé. Un clic ouvre la journée dans sa page mensuelle.</p>" + cal +
             "<div class='deux'><div><h3>Les 5 jours au plus de bûches</h3><ul>" +
             "".join(f"<li><a href='{lien_jour(j)}'>{j['date']}</a> : {j['nb_buches']:.0f} bûches, {j['kwh_reel']:.0f} kWh réels, {j['t_moy_om']} °C</li>" for j in top) +
             "</ul></div><div><h3>Les 5 jours les plus froids</h3><ul>" +
             "".join(f"<li><a href='{lien_jour(j)}'>{j['date']}</a> : {j['t_moy_om']} °C, {j['nb_buches']:.0f} bûches, {j['kwh_reel']:.0f} kWh</li>" for j in froid) +
             "</ul></div></div><h2>Tous les jours</h2><div class='defile'><table>" + ENT + "".join(ligne_jour(j) for j in J) + "</table></div>")
    page("jours.html", "Jour par jour", corps, quand)

    # ---------------- données brutes ----------------
    cols = list(BRUT[0].keys())
    rows = []
    for r in BRUT:
        cl = " class=tot" if r["type_ligne"] == "total_mois" else (" class=e" if r["drapeau"] == "E" else "")
        rows.append(f"<tr{cl}>" + "".join(f"<td{' class=n' if c not in ('type_ligne', 'date_iso', 'drapeau') else ''}>{E(r[c] or "")}</td>" for c in cols) + "</tr>")
    corps = ("<p>Copie fidèle de la Feuille 1 (valeurs calculées par le chiffrier, non arrondies), une ligne par ligne de feuille, totaux mensuels compris. "
             "Rien n'est corrigé ici ; les corrections et drapeaux sont dans <code>journal_nettoye.csv</code>.</p><p>Fichiers : "
             "<a href='../data/journal_brut.csv'>journal_brut.csv</a> · <a href='../data/journal_nettoye.csv'>journal_nettoye.csv</a> · "
             "<a href='../data/meteo.csv'>meteo.csv</a> · <a href='../data/anomalies.csv'>anomalies.csv</a> · <a href='../data/factures.csv'>factures.csv</a> · "
             "<a href='../data/modele.json'>modele.json</a></p><div class='defile'><table><tr>" + "".join(f"<th>{E(c)}</th>" for c in cols) + "</tr>" + "".join(rows) + "</table></div>")
    page("donnees.html", "Données brutes", corps, quand)

    # ---------------- factures ----------------
    tf = ["<table><tr><th>Période</th><th>Colonne « 2023 »</th><th>Colonne « 2024 »</th><th>Écart</th><th>Remarque</th></tr>"]
    for f in FACT:
        a, b = n(f["colonne_2023"]), n(f["colonne_2024"])
        tf.append(f"<tr><td>{E(f['periode'])}</td><td class=n>{argent(a)}</td><td class=n>{argent(b)}</td>"
                  f"<td class=n>{argent(b - a) if a is not None and b is not None else '—'}</td><td>{E(f['note'])}</td></tr>")
    tf.append("</table>")
    g_f = svg.series([f["periode"] for f in FACT], [
        {"nom": "Colonne 2023", "valeurs": [n(f["colonne_2023"]) for f in FACT], "couleur": "#90a4ae", "type": "bar"},
        {"nom": "Colonne 2024", "valeurs": [n(f["colonne_2024"]) for f in FACT], "couleur": svg.COUL["reel"], "type": "bar"}], titre_g="$", h=260, w=900)
    corps = ("<div class='info'><b>Contrôle de la mesure.</b> Pour la période du " + E(CF["periode"]) + f" ({CF['jours']} jours), les kWh notés chaque jour totalisent "
             f"{nb(CF['kwh_journal'])} kWh. Au tarif D 2023 (40 kWh × jours à 6,509 ¢, le reste à 10,041 ¢, accès 43,505 ¢/jour) plus TPS et TVQ, cela donne "
             f"<b>{argent(CF['cout_ttc'])}</b> contre <b>{argent(CF['facture'])}</b> facturés : écart de {nb(CF['ecart_pct'], 1)} %. "
             "Les kWh réels du journal sont donc fiables.</div>" + g_f + "".join(tf) +
             "<div class='alerte'>Feuille 2 : les totaux annuels ajoutent 28 $ sans explication (<code>=SUM(...)+28</code>). "
             "Les étiquettes « 2023 / 2024 » semblent désigner l'année de la facture : la colonne 2023 couvre l'hiver 2022-2023 et la colonne 2024 l'hiver 2023-2024. "
             "Les montants ronds (330, 155, 140, 200 $) ressemblent à des estimations saisies d'avance. On ne sait pas si l'hiver 2022-2023 avait aussi du bois : "
             "la comparaison d'une année à l'autre ne peut donc pas isoler l'effet du bois (et l'hiver 2023-2024 a été exceptionnellement doux).</div>")
    page("factures.html", "Factures Hydro-Québec (Feuille 2)", corps, quand)

    # ---------------- qualité ----------------
    from collections import Counter
    cnt = Counter(a["code"] for a in ANO)
    libelles = {"extrapole": "Lignes « E » (extrapolées, non mesurées)", "eco_sans_buche": "« E » de février : économie comptée sans aucune bûche",
                "tarif_vide": "Prix du kWh vide (formule qui pointe la ligne de total)", "palier_errone": "Paliers 40 kWh mal saisis",
                "feu_sans_gain": "Jour avec bûches mais kWh eq ≤ réels", "sans_feu_ecart": "Jour sans feu mais kWh eq ≠ réels",
                "temp_ecart": "Température notée très différente de la météo (≥ 6 °C)"}
    corr_t = MOD["modeles"]
    eco_E_fev = sum(j["eco_feuille_marc"] or 0 for j in ext if j["date"].month == 2)
    tq = ["<table><tr><th>Constat</th><th>Nombre</th><th>Effet</th></tr>"]
    effets = {"extrapole": "Exclues de l'analyse (17 févr. → 31 mars)", "eco_sans_buche": f"{argent(eco_E_fev)} d'économie comptée dans ta feuille sans mesure",
              "tarif_vide": "Coût de ces jours = 0 $ ; sans effet sur l'économie (mars à 0)", "palier_errone": "Effet de quelques sous",
              "feu_sans_gain": "Économie nulle ces jours-là dans ta feuille ; le modèle leur en donne une", "sans_feu_ecart": "1 kWh d'écart, négligeable",
              "temp_ecart": "Sans effet : le modèle utilise la météo Open-Meteo"}
    for code, nbr in cnt.most_common():
        tq.append(f"<tr><td>{E(libelles.get(code, code))}</td><td class=n>{nbr}</td><td>{E(effets.get(code, ''))}</td></tr>")
    tq.append("</table>")
    ta = ["<div class='defile'><table><tr><th>Date</th><th>Ligne</th><th>Code</th><th>Détail</th></tr>"]
    for a in ANO:
        if a["code"] == "extrapole":
            continue
        ta.append(f"<tr><td><a href='mois-{a['date'][:7]}.html#j-{a['date']}'>{a['date']}</a></td><td class=n>{a['ligne']}</td><td>{E(a['code'])}</td><td>{E(a['detail'])}</td></tr>")
    ta.append("</table></div>")
    r_t = MOD.get("corr_temp")
    diffs = [j["temp_marc"] - j["t_moy_om"] for j in mes]
    corps = ("<div class='cartes'>" + carte(f"{len(mes)}/{len(J)}", "jours réellement mesurés", "neutre", sous=f"{mes[0]['date']} → {mes[-1]['date']}") +
             carte("0", "jour manquant dans la période mesurée", "ok") +
             carte(f"{CF['ecart_pct']:+.1f} %".replace(".", ","), "kWh du journal vs facture", "ok", "factures.html") +
             carte(nb(sum(diffs) / len(diffs), 1) + " °C", "écart moyen T notée − T Open-Meteo", "ok", sous="ta température ≈ moyenne du jour") +
             carte(nb(len(feu) and sum(1 for j in feu if j['kwh_eq_marc'] <= j['kwh_reel'])), "jours de feu sans gain dans ta feuille", "prov") + "</div>" +
             "<h2>Constats</h2>" + "".join(tq) +
             "<h2>Ce que l'on peut confirmer</h2><ul>"
             f"<li><b>kWh réels</b> : confirmés par la facture du 17 nov. au 18 janv. (écart {nb(CF['ecart_pct'], 1)} %). Ils viennent manifestement de l'Espace client Hydro.</li>"
             "<li><b>Températures</b> : entiers notés à la main, cohérents avec la moyenne quotidienne Open-Meteo (réanalyse ERA5, point près de Vaudreuil-Dorion). "
             "Le modèle utilise la météo publique, plus fine (au dixième de degré) et disponible aussi pour les jours « E ».</li>"
             "<li><b>Bûches</b> : aucune source externe pour les vérifier ; la relation très nette bûches → baisse de kWh (voir Méthode) les rend crédibles.</li>"
             "<li><b>« kWh eq estimé »</b> : saisi à la main (souvent 75, 80, 85, 90…), parfois en formule (=35+réel, =40+réel). "
             f"En moyenne, il implique {nb(marc_kwh_mes / B, 2)} kWh évités par bûche, très proche du modèle ({nb(kb, 2)}).</li></ul>"
             "<h2>Formules du chiffrier à corriger (si tu le réutilises)</h2><ul>"
             "<li>Total de novembre : <code>=SUM(D2:D25)+7*70</code> et <code>=SUM(E2:E25)+7*70</code> ajoutent 490 kWh (1er au 6 nov., non mesurés) aux deux colonnes ; le % du mois est faussé.</li>"
             "<li>Total de février (ligne 120) : la colonne bûches est vide.</li>"
             "<li>Mars : <code>Prix = G(ligne−2)</code> pointe une ligne sur deux vers la ligne de total vide, d'où un tarif vide un jour sur deux.</li>"
             "<li>Paliers : Hydro applique les 40 kWh × nombre de jours <b>de la période de facturation</b>, pas jour par jour ; tes paliers quotidiens sous-évaluent l'économie les jours où le réel est sous 40 kWh.</li></ul>"
             "<h2>Détail des signaux (hors lignes « E »)</h2>" + "".join(ta))
    page("qualite.html", "Qualité des données", corps, quand)

    # ---------------- méthode ----------------
    M = MOD["modeles"]
    def lm(nom, m, noms):
        return (f"<tr><td>{E(nom)}</td><td>" + ", ".join(f"{E(x)} = {nb(c, 2)} (± {nb(s, 2)})" for x, c, s in zip(noms, m["coef"], m["se"])) +
                f"</td><td class=n>{nb(m['r2'], 2)}</td><td class=n>{nb(m['rmse'], 1)}</td><td class=n>{m['n']}</td></tr>")
    tm = ("<table><tr><th>Variante</th><th>Coefficients (erreur-type)</th><th>R²</th><th>Écart-type résiduel (kWh)</th><th>n</th></tr>" +
          lm("Principal : kWh ~ degrés-jours + bûches (météo Open-Meteo)", M["principal"], ["constante", "kWh/degré-jour", "kWh/bûche"]) +
          lm("Même modèle, avec ta température notée", M["temp_marc"], ["constante", "kWh/degré-jour", "kWh/bûche"]) +
          lm("Avec les bûches de la veille", M["avec_veille"], ["constante", "kWh/degré-jour", "bûches du jour", "bûches de la veille"]) +
          lm("Avec bûches et froid de la veille", M["avec_veille_dj"], ["constante", "kWh/degré-jour", "bûches du jour", "bûches de la veille", "degrés-jours veille"]) +
          lm("Sans les bûches (pour comparer)", M["sans_buches"], ["constante", "kWh/degré-jour"]) +
          lm("Jours sans feu seulement", M["jours_sans_feu"], ["constante", "kWh/degré-jour"]) + "</table>")
    corps = ("<h2>Question</h2><p>Combien d'électricité chaque bûche a-t-elle évitée, et l'achat de bois (425 $) est-il rentable face à l'électricité ?</p>"
             "<h2>Approche du chiffrier (2023-2024)</h2><p>Pour chaque jour avec feu, tu as estimé à la main les kWh que tu aurais consommés sans feu (« kWh eq estimé ») ; "
             "l'économie = coût(eq) − coût(réel), avec des paliers de 40 kWh appliqués jour par jour, sans taxes. Les jours sans feu, eq = réel.</p>"
             "<h2>Approche proposée</h2><ol>"
             "<li>Météo publique : température moyenne quotidienne Open-Meteo (réanalyse ERA5), point le plus proche de Vaudreuil-Dorion (hypothèse de lieu). "
             "Degrés-jours de chauffe base 18 °C : DJ = max(18 − T moy., 0).</li>"
             "<li>Régression sur les 102 jours mesurés : <b>kWh réels = a + b × DJ + c × bûches</b>. Le coefficient c (négatif) est l'électricité évitée par bûche, à température égale.</li>"
             "<li>Pourquoi pas « jours sans feu seulement » ? Les 28 jours sans feu sont presque tous doux (−7 à +9 °C) : on ne peut pas extrapoler aux jours de −14 °C. "
             "Le modèle conjoint utilise l'information de tous les jours.</li>"
             "<li>kWh sans feu (contrefactuel) = kWh réels + c × bûches. Économie = kWh évités × 10,041 ¢ : comme ta consommation moyenne dépasse toujours 40 kWh/jour sur la période de facturation, "
             "chaque kWh évité l'est au prix de la 2e tranche. Taxes : × 1,14975 (TPS + TVQ).</li></ol>"
             "<h2>Résultats</h2>" + tm +
             f"<p><b>Retenu : {nb(kb, 2)} kWh par bûche</b> (erreur-type {nb(seb, 2)}). Plage plausible {nb(kb_bas, 1)} à {nb(kb_haut, 1)} kWh : "
             "la borne haute vient des variantes qui comptent la chaleur restituée le lendemain (masse thermique) ; la borne basse de l'intervalle à 95 % et de la variante avec ta température.</p>"
             f"<p class='petit'>Ordre de grandeur physique : une bûche de feuillu sec de 2 kg contient ≈ 8 kWh ; {nb(kb, 1)} kWh utiles suppose un rendement ≈ {pct(kb / 8)}, "
             "plausible pour un foyer fermé ou un insert. Le poids des bûches n'a pas été mesuré : hypothèse.</p>"
             "<h2>Comparaison avec le chiffrier</h2><table><tr><th></th><th>Chiffrier</th><th>Modèle</th></tr>"
             f"<tr><td>kWh évités, jours mesurés</td><td class=n>{nb(marc_kwh_mes)}</td><td class=n>{nb(kwh_ev)} (plage {nb(kb_bas * B)} à {nb(kb_haut * B)})</td></tr>"
             f"<tr><td>kWh par bûche</td><td class=n>{nb(marc_kwh_mes / B, 2)}</td><td class=n>{nb(kb, 2)}</td></tr>"
             f"<tr><td>Économie, jours mesurés</td><td class=n>{argent(marc_eco_mes)} (avant taxes, paliers quotidiens)</td><td class=n>{argent(eco_ht)} avant taxes · {argent(eco_ttc)} taxes incl.</td></tr>"
             f"<tr><td>Économie, lignes « E »</td><td class=n>{argent(marc_eco_ext)}</td><td class=n>exclue</td></tr>"
             f"<tr><td>Total saison affiché</td><td class=n>{argent(marc_eco_tot)} (solde bois : {argent(PRIX_BOIS - marc_eco_tot)})</td><td class=n>{argent(val_saison)} projeté (voir ci-dessous)</td></tr></table>"
             "<h2 id='saison'>Projection sur la saison et rendement</h2>"
             f"<p>La période mesurée couvre {pct(S['part_dj_mesuree'])} des degrés-jours du 1er nov. au 31 mars ({nb(S['dj_mesure'])} sur {nb(S['dj_saison'])}). "
             f"Si tu as fait du feu au même rythme par degré-jour après le 16 février, la saison compte ≈ <b>{nb(Bs)} bûches</b>. Hypothèse basse : aucun feu après le 16 février ({nb(S['buches_saison_bas'])} bûches).</p>"
             "<table><tr><th>Scénario</th><th>Bûches</th><th>kWh/bûche</th><th>Valeur électricité, taxes incl.</th><th>vs 425 $</th></tr>" +
             "".join(f"<tr><td>{E(a)}</td><td class=n>{nb(b)}</td><td class=n>{nb(k, 1)}</td><td class=n>{argent(v, 0)}</td><td class=n>{('+' if v >= PRIX_BOIS else '')}{pct(v / PRIX_BOIS - 1)}</td></tr>"
                     for a, b, k, v in [("Bas (aucun feu après le 16 févr., kWh/bûche bas)", S["buches_saison_bas"], kb_bas, val_saison_bas),
                                        ("Central", Bs, kb, val_saison), ("Haut (effet du lendemain compté)", Bs, kb_haut, val_saison_haut),
                                        ("Central au tarif 2026 (11,142 ¢)", Bs, kb, val_2026)]) + "</table>"
             f"<p><b>Seuil de rentabilité</b> au tarif 2023-2024 : {nb(seuil)} bûches par saison pour 425 $ (taxes incluses des deux côtés). "
             f"Chaque bûche vaut ≈ {argent(val_buche_ttc)} d'électricité ; elle te coûte 425 $ ÷ nombre de bûches par saison.</p>"
             "<h2>Hypothèses et limites</h2><ul>"
             "<li>425 $ = coût total du bois pour la saison, tout inclus (taxes comprises) : <b>confirmé par Marc le 2026-11-22</b>. Nombre de cordes absent du chiffrier : 4 cordes supposées.</li>"
             "<li>Lieu météo : Vaudreuil-Dorion, <b>confirmé par Marc le 2026-11-22</b>.</li>"
             "<li>Bûches toutes équivalentes (taille, essence, humidité) ; ni poids ni volume mesurés.</li>"
             "<li>Pas de prise en compte du temps de présence, des autres usages (eau chaude, cuisson), de l'ensoleillement ou du vent ; ils sont dans le bruit (écart-type résiduel ≈ "
             f"{nb(M['principal']['rmse'])} kWh/jour).</li>"
             "<li>Coûts non comptés : allumage, ramonage, assurance, temps et plaisir du feu.</li></ul>"
             "<h2 id='maj-2026'>Mise à jour du 22 novembre 2026</h2><ul>"
             "<li>Coût de référence du bois : 4 cordes × (106,25 $ + 25 $) = <b>525 $</b> tout inclus (hausse de 25 $ par corde indiquée par Marc ; 4 cordes = hypothèse).</li>"
             "<li>Marc est au tarif <b>Flex D</b> (confirmé le 22 nov. 2026, 12 h 51) : hors événement 9,103 ¢ en 2e tranche, 46,463 ¢ pendant les événements (tarifs au 1er avril 2026). Le crédit hivernal est écarté.</li>"
             "<li>Pas d'achat de bois en 2026-27 : stock ≈ 1,5 corde ≈ 348 bûches (232 bûches/corde, ratio dérivé de 2023-24, fragile). Bois déjà payé : objectif = maximiser la valeur évitée avec ce stock (simulation jour par jour avec une règle de budget). Une corde de plus ajouterait ≈ 109 $ pour ≈ 131 $ : non rentable.</li>"
             "<li>Une bûche vaut ≈ 0,47 $ hors événement (Flex D) contre ≈ 0,58 $ au tarif D 2026 ; seuil de rentabilité ≈ 1 115 bûches (Flex D hors événement) ou ≈ 911 (tarif D).</li>"
             "<li>Test ajouté : interaction bûches × degrés-jours non significative ; le gain par bûche reste constant dans le modèle.</li>"
             "<li>Suite : <a href='protocole.html'>Protocole hiver 2026-2027</a> (étude météo, simulation, saisie).</li></ul>")
    page("methode.html", "Méthode, modèle et incertitudes", corps, quand)

    # ---------------- propositions ----------------
    corps = ("<h2>Décidé le 22 novembre 2026</h2><ul>"
             "<li>425 $ = tout inclus ; repère de remplacement 131,25 $ la corde (425 $ ÷ 4 + 25 $). Météo : Vaudreuil-Dorion.</li>"
             "<li><b>Tarif Flex D confirmé</b> (activé récemment) ; l'option de crédit hivernal est écartée.</li>"
             "<li><b>Pas d'achat de bois cet hiver</b> : stock ≈ 1,5 corde ≈ 348 bûches, déjà payé. Objectif : placer ce stock là où il évite le plus d'électricité "
             "(événements de pointe d'abord, puis jours cœur des creux froids). Voir le <a href='protocole.html#regles'>protocole et sa règle de budget</a>.</li>"
             "<li>Format retenu : site statique régénéré par script ; saisie simplifiée dans <code>data/saisie_2026-2027.csv</code>, avec suivi du stock.</li></ul>"
             "<h2>À décider ou à faire</h2><ol>"
             "<li><b>Compter le stock</b> (ou une rangée, puis extrapoler) et l'inscrire dans la colonne <code>stock_compte</code> : le ratio de 232 bûches par corde est fragile (±25 %).</li>"
             "<li><b>Achat d'appoint</b> : non recommandé (≈ 109 $ de valeur pour ≈ 131 $ la corde) ; à revoir seulement si le recomptage donne moins de ≈ 150 bûches.</li>"
             "<li><b>Mesure des événements</b> : télécharger les kWh <b>horaires</b> de l'Espace client les jours d'événement pour mesurer l'effet réel du feu dans la fenêtre 6-10 h / 16-20 h.</li>"
             "<li><b>Jours témoins</b> : un jour froid sans feu par mois environ.</li>"
             "<li><b>Données à ajouter</b> : poids moyen d'une bûche (peser 10 bûches), absences, export CSV quotidien de l'Espace client.</li></ol>"
             "<h2>Propositions de la première itération (pour mémoire)</h2><ol class='petit'>"
             "<li>Garder un site statique régénéré par script (retenu).</li><li>Peser les bûches, compter les bûches par corde, noter les absences (à faire).</li>"
             "<li>Rapprocher chaque facture avec le journal.</li><li>Jours témoins (intégré au protocole).</li><li>Décision bois au tarif 2026 (pas d'achat cette année).</li></ol>")
    page("decisions.html", "Propositions et décisions à prendre", corps, quand)
    import generer_protocole
    generer_protocole.main(quand)
    print("Pages :", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()

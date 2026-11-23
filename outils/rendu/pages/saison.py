"""Accueil « Saison » : tableau de bord de la saison courante (ou bilan d'une saison terminée, dans Archives).

Lit l'état calculé par calculs/saison.py ; n'effectue aucun calcul métier.
"""
import html
from rendu import graphes as svg
from rendu.gabarit import page
from rendu.composants import (bloc, jauge, barre_temps, mini_barre, calendrier_saison, legende_calendrier,
                              nb, argent, dfr, JOURS_FR)

E = html.escape


def _t(x):
    return "—" if x is None else (f"{x:.1f}".replace(".", ",").replace("-", "−") + " °C")


def bloc_jour(e):
    r = e["reco"]; auj = r[1]
    if e["terminee"]:
        return bloc("Saison terminée", f"<p class='verdict'>Bilan au {dfr(e['saison']['fin'], annee=True)}</p>"
                    "<p>La saison est close : les chiffres ci-dessous sont définitifs.</p>", "bloc-jour")
    if auj["feu"] is None:
        verdict, cl = "Prévision indisponible", "verdict-na"
    elif auj["feu"]:
        verdict, cl = f"Feu : ≈ {auj['buches']} bûches", "verdict-feu"
    else:
        verdict, cl = "Pas de feu", "verdict-non"
    vign = []
    for k, v in enumerate(r):
        lib = ["hier", "aujourd'hui", "demain", JOURS_FR[v["date"].weekday()]][k]
        if k == 0:
            bas = (f"{nb(v['buches'])} bûches" if v["saisi"] else ("à saisir" if v["a_saisir"] else "—"))
        else:
            bas = "—" if v["feu"] is None else (f"feu · {v['buches']}" if v["feu"] else "pas de feu")
        evt = "<span class='losange' title='événement Flex D'>◆</span>" if v["evt"] else ""
        vign.append(f"<div class='vignette{' actif' if k == 1 else ''}{' feu' if k and v.get('feu') else ''}'><span class='v-lib'>{lib}</span>"
                    f"<b>{_t(v['t'])}</b>{evt}<span class='v-bas'>{bas}</span></div>")
    detail = (f"min {_t(auj['tmin'])}, max {_t(auj['tmax'])}" if auj["tmin"] is not None else "")
    maj = e["maj"]
    if maj:
        ok = [k for k, v in maj["sources"].items() if v["ok"]]; ko = [k for k, v in maj["sources"].items() if not v["ok"]]
        src = f"Données rafraîchies le {E(maj['quand'][:16].replace('T', ' à '))}" + (f" ; échec : {', '.join(ko)} (données versionnées utilisées)" if ko else "")
    else:
        src = "Données versionnées du dépôt (pas de rafraîchissement automatique pour cette construction)"
    raison = auj['raison'][:1].upper() + auj['raison'][1:]
    corps = (f"<p class='verdict {cl}'>{verdict}</p><p class='raison'>{E(raison)}{'' if raison.endswith('.') else '.'}"
             + (f" <span class='petit'>({detail})</span>" if detail else "") + "</p>"
             f"<div class='vignettes'>{''.join(vign)}</div>"
             f"<p class='source'>Règle de budget du protocole appliquée à la prévision Open-Meteo"
             + (f" (téléchargée le {E(e['prevision_quand'])})" if e["prevision_quand"] else "")
             + f" et aux événements annoncés par Hydro-Québec. {src}. L'avis officiel d'Hydro-Québec a priorité.</p>")
    return bloc(f"Aujourd'hui · {dfr(auj['date'], jour=True)}", corps, "bloc-jour", "aujourdhui", ("strategie/index.html#regles", "règles"))


def bloc_stock(e):
    s = e["stock"]
    txt = (f"Plan à ce jour : {nb(s['plan'])} · réserve pour les événements : {nb(s['reserve'])} · marge sur la réserve : <b>{'+' if s['marge'] >= 0 else ''}{nb(s['marge'])}</b>.")
    if not e["saisie"]:
        txt += f" Aucune saisie : stock = inventaire mesuré du {dfr(s['date_inventaire'])}"
    else:
        txt += f" Écart au plan : {'+' if s['ecart_plan'] >= 0 else ''}{nb(s['ecart_plan'])} bûches."
    alerte = ("<p class='alerte'>Le stock est plus de 50 bûches sous le plan : <b>événements seulement</b> jusqu'à revenir sur la courbe (règle 5).</p>" if s["frein"] else "")
    corps = (f"<p class='chiffre'>{nb(s['actuel'])} <span>bûches</span></p>" +
             jauge(s["actuel"], s["depart"], s["reserve"], s["plan"], "plan à ce jour") +
             f"<p class='petit'>{txt}</p>{alerte}")
    return bloc("Stock de bois", corps, "bloc-stock", "stock", ("strategie/inventaire.html", "inventaire"))


def bloc_temps(e):
    sa = e["saison"]; import datetime as dt
    deb, fin = dt.date.fromisoformat(sa["debut"]), dt.date.fromisoformat(sa["fin"])
    c0, c1 = e["critique"]; f0, f1 = e["flex_d"]; auj = e["aujourd_hui"]
    bt = barre_temps(deb, fin, auj, marques=[(f0, "marque-flex", "début Flex D")], zones=[(c0, c1, "zone-critique")])
    j_flex = (f0 - auj).days
    if e["jour"] <= 0:
        morceaux = [f"La saison commence dans {1 - e['jour']} jour{'s' if 1 - e['jour'] > 1 else ''}"]
    else:
        morceaux = [f"Jour {e['jour']} sur {e['jours_total']} ({e['jour'] / e['jours_total'] * 100:.0f} %)".replace(".", ",")]
    if j_flex > 0:
        morceaux.append(f"Flex D dans {j_flex} jour{'s' if j_flex > 1 else ''}")
    elif auj <= f1:
        morceaux.append("saison Flex D en cours")
    morceaux.append(f"{e['jours_restants']} jours restants")
    return bloc("Avancement de la saison", bt + f"<p class='petit'>{' · '.join(morceaux)}. Hachuré : période critique ({dfr(c0)} au {dfr(c1)}) ; trait : début des événements Flex D ({dfr(f0)}).</p>",
                "bloc-temps", "temps")


def bloc_cumuls(e):
    r, pd, ps, fo = e["reel"], e["plan_date"], e["plan_saison"], e["fourchette"]
    a0 = lambda x: argent(x, 0)
    corps = ("<div class='minis'>" + mini_barre("Bûches", r["buches"], pd["buches"], ps["buches"]) +
             mini_barre("kWh évités", r["kwh"], pd["kwh"], ps["kwh"]) +
             mini_barre("$ évités", r["base"], pd["base"], ps["base"], fmt=a0) + "</div>"
             f"<p class='petit'>Barre : réel · trait : plan à ce jour · chiffres : réel / plan à ce jour · plan de saison (règle de budget, météo {e['plan_meteo']}). "
             f"Les $ comptent l'électricité évitée hors prime d'événement ; la prime prévue au plan s'ajoute (≈ {a0(ps['prime'])} sur la saison). "
             + (f"Selon la météo des 3 derniers hivers, la valeur totale du plan va de {a0(fo['base'][0])} à {a0(fo['base'][1])}." if fo else "") + "</p>")
    if not e["saisie"]:
        corps += "<p class='vide'>Aucune saisie pour l'instant : la partie « réel » se remplira au fil des journées.</p>"
    return bloc("Réel et projection", corps, "bloc-cumuls", "cumuls", ("strategie/plan.html", "plan"))


def bloc_evenements(e):
    b = e["ev_bilan"]; f0, f1 = e["flex_d"]
    cpt = [("annonce", "à venir"), ("couvert", "couverts"), ("manque", "manqués"), ("nonsaisi", "non saisis")]
    corps = ("<div class='compteurs'>" + "".join(f"<div class='compteur c-{k}'><b>{b[k] + (b['aujourdhui'] if k == 'annonce' else 0)}</b>{lib}</div>" for k, lib in cpt) +
             f"<div class='compteur'><b>{nb(e['heures'])} h</b>sur {e['plafond_heures']} h</div></div>")
    a_venir = [x for x in e["evenements"] if x["statut"] in ("annonce", "aujourdhui")]
    if a_venir:
        corps += "<ul class='liste-evt'>" + "".join(f"<li><b>{dfr(x['date'], jour=True)}</b> : {', '.join(x['plages'])}</li>" for x in a_venir[:4]) + "</ul>"
    hist = " ; ".join(f"{n} en {h}" for h, n in e["evts_historique"].items())
    if not e["evenements"]:
        corps += f"<p class='vide'>Aucun événement pour l'instant : la saison Flex D va du {dfr(f0)} au {dfr(f1, annee=True)}.</p>"
    corps += f"<p class='petit'>Données ouvertes d'Hydro-Québec (offre Flex D). Historique : {hist}. Couvert = feu saisi ce jour-là.</p>"
    return bloc("Événements de pointe Flex D", corps, "bloc-evt", "evenements")


def bloc_calendrier(e):
    import datetime as dt
    sa = e["saison"]
    return bloc("Calendrier de la saison", calendrier_saison(e["calendrier"], dt.date.fromisoformat(sa["debut"]), dt.date.fromisoformat(sa["fin"]), e["aujourd_hui"]) +
                legende_calendrier(), "bloc-cal", "calendrier", ("journal.html", "journal"))


def graphe_stock(e, h=270, w=480):
    c = e["courbe"]
    labs = [dfr(x["date"]) for x in c]
    auj = next((i for i, x in enumerate(c) if x["date"] == e["aujourd_hui"]), None)
    return svg.series(labs, [
        {"nom": "Plan", "valeurs": [x["plan"] for x in c], "couleur": "plan", "pointille": True, "points": False},
        {"nom": "Réserve", "valeurs": [x["reserve"] for x in c], "couleur": "reserve", "type": "area", "points": False, "epaisseur": 1},
        {"nom": "Réel", "valeurs": [x["reel"] for x in c], "couleur": "buche", "points": len([x for x in c if x["reel"] is not None]) < 3, "epaisseur": 3},
    ], titre_g="bûches", h=h, w=w, auj=auj)


def bloc_courbe(e):
    return bloc("Le stock dans le temps", graphe_stock(e) +
                "<p class='petit'>Pointillé : stock prévu par le plan · zone : réserve à garder pour les événements · trait plein : stock réel (inventaire, puis saisies) · ligne verticale : aujourd'hui.</p>",
                "bloc-courbe", "courbe")


def bloc_derniers(e):
    S = e["saisie"][-5:][::-1]
    if S:
        corps = ("<table class='compact'><tr><th>Jour</th><th>Bûches</th><th>kWh</th><th>Écart au modèle</th></tr>" +
                 "".join(f"<tr><td>{dfr(s['date'], jour=True)}</td><td class=n>{nb(s['buches'])}</td><td class=n>{nb(s['kwh']) if s['kwh'] is not None else 'en attente'}</td>"
                         f"<td class=n>{'' if s['ecart'] is None else ('+' if s['ecart'] >= 0 else '') + nb(s['ecart'])}</td></tr>" for s in S) + "</table>")
    else:
        corps = "<p class='vide'>Aucune saisie pour l'instant. Il suffit d'écrire « hier 8 bûches, 62 kWh » (ou plusieurs jours d'un coup) : la ligne s'ajoute et le site se met à jour.</p>"
    m = e["manquants"]
    if m:
        corps += f"<p class='alerte'>Jours à saisir ({len(m)}) : " + ", ".join(dfr(d) for d in m[-10:]) + (" …" if len(m) > 10 else "") + "</p>"
    else:
        corps += f"<p class='petit'>Jours à saisir : aucun (le suivi des jours manquants commence le {dfr(e['debut_suivi'])}).</p>"
    if e["kwh_attente"]:
        corps += "<p class='petit'>kWh en attente : " + ", ".join(dfr(d) for d in e["kwh_attente"]) + "</p>"
    return bloc("Derniers jours saisis", corps, "bloc-derniers", "derniers", ("journal.html", "journal complet"))


def rendre(e, chemin, quand):
    sa = e["saison"]
    corps = "".join([bloc_jour(e), "<div class='grille-blocs'>", bloc_stock(e), bloc_temps(e), bloc_cumuls(e), bloc_evenements(e), "</div>",
                     "<div class='grille-blocs'>", bloc_calendrier(e), "<div>", bloc_courbe(e), bloc_derniers(e), "</div></div>",
                     "<nav class='liens-bas'><a href='journal.html'>Journal complet</a><a href='strategie/index.html'>Règles et tarif</a>"
                     "<a href='strategie/plan.html'>Plan de saison</a><a href='archives/index.html'>Archives</a></nav>"])
    titre = sa["titre"] + (" : bilan" if e["terminee"] else "")
    sous = f"<p class='sous'>{E(sa['resume'])} Mis à jour le {E(quand)}.</p>"
    page(chemin, titre, corps, quand, sous=sous, contexte=f"{sa['titre']} · {dfr(e['aujourd_hui'], jour=True)}", classe="tableau-de-bord")

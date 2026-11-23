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


def _src(e):
    """Ligne « source » : prévision utilisée, rafraîchissement, et ce qui a échoué (mode ouvert visible)."""
    pv, maj = e["prevision"], e["maj"]
    alertes = []
    if pv["source"] is None:
        alertes.append("Prévision indisponible pour aujourd'hui : la règle n'est pas appliquée (mode ouvert).")
    elif pv["secours"]:
        alertes.append("Environnement Canada indisponible : prévision Open-Meteo utilisée en secours.")
    if maj and maj["sources"].get("evenements_hq", {}).get("ok") is False:
        alertes.append("Événements Hydro-Québec non rafraîchis ce matin : vérifier l'avis officiel.")
    if pv["source"]:
        quand = pv["ec_emis"] if pv["source"] == "Environnement Canada" else pv["om_quand"]
        txt = f"Prévision : {E(pv['source'])}" + (f" (émise le {E(quand.replace(' ', ' à '))})" if quand else "")
    else:
        txt = "Prévision : aucune source à jour"
    if maj:
        ko = [k for k, v in maj["sources"].items() if not v["ok"]]
        txt += f" · données rafraîchies le {E(maj['quand'][:16].replace('T', ' à '))}" + (f" (échec : {', '.join(ko)} ; fichiers versionnés utilisés)" if ko else "")
    else:
        txt += " · données versionnées du dépôt (pas de rafraîchissement pour cette construction)"
    return "".join(f"<p class='alerte'>{E(a)}</p>" for a in alertes), txt


def _verdict(v):
    if v["feu"] is None:
        return "Prévision indisponible", "verdict-na"
    if v["feu"]:
        return f"Feu : ≈ {v['buches']} bûches", "verdict-feu"
    return "Pas de feu", "verdict-non"


def texte_creux(e):
    out = []
    for c in e["creux_prevus"]:
        coeur = (" ; cœur : " + ", ".join(dfr(d) for d in c["coeur"])) if c["coeur"] else " ; pas de jour cœur prévu"
        out.append(f"Creux froid {'en cours' if c['en_cours'] else 'prévu'} du {dfr(c['debut'])} au {dfr(c['fin'])} "
                   f"(minimum {_t(c['t_min'])} le {dfr(c['date_min'])}{coeur}).")
    return " ".join(out)


def bloc_jour(e):
    r = e["reco"]; auj = r[1]
    if e["terminee"]:
        return bloc("Saison terminée", f"<p class='verdict'>Bilan au {dfr(e['saison']['fin'], annee=True)}</p>"
                    "<p>La saison est close : les chiffres ci-dessous sont définitifs.</p>", "bloc-jour")
    verdict, cl = _verdict(auj)
    vign = []
    for k, v in enumerate(r):
        lib = ["hier", "aujourd'hui", "demain", JOURS_FR[v["date"].weekday()]][k]
        if k == 0:
            bas = (f"fait · {nb(v['buches'])}" if v["saisi"] else ("à saisir" if v["a_saisir"] else "—"))
        else:
            bas = "—" if v["feu"] is None else (f"feu · {v['buches']}" if v["feu"] else "pas de feu")
        evt = "<span class='losange' title='événement Flex D'>◆</span>" if v["evt"] else ""
        froid = " coeur" if v["coeur"] else ""
        vign.append(f"<div class='vignette{' actif' if k == 1 else ''}{' feu' if k and v.get('feu') else ''}{froid}'><span class='v-lib'>{lib}</span>"
                    f"<b>{_t(v['t'])}</b>{evt}<span class='v-bas'>{bas}</span></div>")
    detail = (f"min {_t(auj['tmin'])}, max {_t(auj['tmax'])}" if auj["tmin"] is not None else "")
    alertes, src = _src(e)
    raison = auj['raison'][:1].upper() + auj['raison'][1:]
    evt = (f"<p class='evt-jour'><b>Événement Flex D aujourd'hui : {E(auj['evenement'])}.</b> {E(auj['moment'][:1].upper() + auj['moment'][1:])}.</p>"
           if auj["evenement"] else "")
    demain = r[2]
    if demain["evt"]:
        evt += f"<p class='evt-jour'><b>Événement Flex D demain : {E(demain['evenement'])}.</b> {E(demain['moment'][:1].upper() + demain['moment'][1:])}.</p>"
    moment = (f" <span class='petit'>{E(auj['moment'][:1].upper() + auj['moment'][1:])}.</span>" if auj["moment"] and not auj["evenement"] else "")
    cr = texte_creux(e)
    corps = (alertes + f"<p class='verdict {cl}'>{verdict}</p>{evt}<p class='raison'>{E(raison)}{'' if raison.endswith('.') else '.'}{moment}"
             + (f" <span class='petit'>({detail})</span>" if detail else "") + "</p>"
             f"<div class='vignettes'>{''.join(vign)}</div>"
             + (f"<p class='petit'>Hier, observé : min {_t(r[0]['tmin'])}, max {_t(r[0]['tmax'])}, moyenne {_t(r[0]['t'])} ({E(r[0]['source'] or '')}).</p>" if r[0]["tmin"] is not None else "")
             + (f"<p class='petit'>{E(cr)}</p>" if cr else "")
             + f"<p class='source'>{src}. Règle de budget du protocole, événements annoncés par Hydro-Québec ; l'avis officiel d'Hydro-Québec a priorité.</p>")
    return bloc(f"Aujourd'hui · {dfr(auj['date'], jour=True)}", corps, "bloc-jour", "aujourdhui", ("strategie/index.html#regles", "règles"))


def bloc_stock(e):
    s = e["stock"]
    ref = dfr(s["date_reference"])
    txt = (f"Plan au {ref} (règle sur la météo réelle) : {nb(s['plan'])} · réserve pour les événements : {nb(s['reserve'])} · "
           f"marge sur la réserve : <b>{'+' if s['marge'] >= 0 else ''}{nb(s['marge'])}</b>.")
    if not e["saisie"]:
        di = dfr(s['date_inventaire'])
        txt += f" Aucune saisie : stock = inventaire mesuré du {di}" + ("" if di.endswith(".") else ".")
    else:
        txt += f" Écart au plan : <b>{'+' if s['ecart_plan'] >= 0 else ''}{nb(s['ecart_plan'])}</b> bûches (au {ref})."
    txt += f" Fin de saison projetée : ≈ {nb(s['fin_projetee'])} bûches."
    alerte = ("<p class='alerte'>Le stock est plus de 50 bûches sous le plan : <b>événements seulement</b> jusqu'à revenir sur la courbe (règle 5).</p>" if s["frein"] else "")
    corps = (f"<p class='chiffre'>{nb(s['actuel'])} <span>bûches</span></p>" +
             jauge(s["actuel"], s["depart"], s["reserve"], s["plan"], "plan") +
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
    r, pd, ps, fo = e["reel"], e["plan_date"], e["projection_saison"], e["fourchette"]
    a0 = lambda x: argent(x, 0)
    corps = ("<div class='minis'>" + mini_barre("Bûches", r["buches"], pd["buches"], ps["buches"]) +
             mini_barre("kWh évités", r["kwh"], pd["kwh"], ps["kwh"]) +
             mini_barre("$ évités", r["base"], pd["base"], ps["base"], fmt=a0) + "</div>"
             f"<p class='petit'>Barre : réel · trait : plan à ce jour (règle de budget appliquée à la météo réelle depuis l'inventaire) · "
             "chiffres : réel / plan à ce jour · saison projetée (réel, puis la règle sur la prévision, puis la dépense moyenne des 3 derniers hivers sous la règle). "
             "Les $ comptent l'électricité évitée hors prime d'événement. "
             + (f"Selon la météo des 3 derniers hivers, la valeur totale du plan, prime comprise, va de {a0(fo['base'][0])} à {a0(fo['base'][1])}." if fo else "") + "</p>")
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
        {"nom": "Réserve", "valeurs": [x["reserve"] for x in c], "couleur": "reserve", "type": "area", "points": False, "epaisseur": 1},
        {"nom": "Plan (météo réelle)", "valeurs": [x["plan"] for x in c], "couleur": "plan", "pointille": True, "points": False},
        {"nom": "Projection", "valeurs": [x["projection"] for x in c], "couleur": "projection", "pointille": True, "points": False, "epaisseur": 2},
        {"nom": "Réel", "valeurs": [x["reel"] for x in c], "couleur": "buche", "points": len([x for x in c if x["reel"] is not None]) < 3, "epaisseur": 3},
    ], titre_g="bûches", h=h, w=w, auj=auj)


def bloc_courbe(e):
    return bloc("Le stock dans le temps", graphe_stock(e) +
                "<p class='petit'>Trait plein : stock réel (inventaire, puis saisies) · pointillé gris : ce que la règle aurait brûlé avec la météo réelle · "
                "pointillé de couleur : projection jusqu'au 31 mars (prévision, puis dépense moyenne des 3 derniers hivers sous la règle) · "
                "zone : réserve à garder pour les événements · ligne verticale : aujourd'hui.</p>",
                "bloc-courbe", "courbe")


def _reco_court(h):
    if not h:
        return "—"
    if h["recommandation"] == "feu":
        return f"feu · {h['buches']}" + (" ◆" if h["evenement"] else "")
    return h["recommandation"]


def tableau_historique(e, n=None):
    H = e["historique"][::-1]
    if n:
        H = H[:n]
    if not H:
        return ""
    lignes = []
    for x in H:
        suivi = {True: "<span class='b-ok badge'>suivi</span>", False: "<span class='b-prov badge'>écart</span>", None: ""}[x["suivi"]]
        fait = nb(x["fait"]) if x["fait"] is not None else ("en cours" if x["date"] >= e["aujourd_hui"] else "à saisir")
        lignes.append(f"<tr><td>{dfr(x['date'], jour=True)}</td><td>{E(_reco_court(x['reco']))}</td><td class=n>{fait}</td>"
                      f"<td class=n>{nb(x['kwh']) if x['kwh'] is not None else ''}</td><td>{suivi}</td></tr>")
    return ("<table class='compact'><tr><th>Jour</th><th>Recommandé</th><th>Bûches faites</th><th>kWh</th><th></th></tr>" + "".join(lignes) + "</table>")


def bloc_derniers(e):
    t = tableau_historique(e, 7)
    if t:
        corps = t + "<p class='petit'>Recommandé : verdict publié ce matin-là (historique versionné, un commit par jour). Fait : bûches saisies.</p>"
    else:
        corps = ("<p class='vide'>Aucune recommandation enregistrée ni saisie pour l'instant. Chaque matin, la recommandation du jour est conservée ; "
                 "il suffit d'écrire « hier 8 bûches, 62 kWh » pour la comparer à ce qui a été fait.</p>")
    m = e["manquants"]
    if m:
        corps += f"<p class='alerte'>Jours à saisir ({len(m)}) : " + ", ".join(dfr(d) for d in m[-10:]) + (" …" if len(m) > 10 else "") + "</p>"
    else:
        corps += f"<p class='petit'>Jours à saisir : aucun (le suivi des jours manquants commence le {dfr(e['debut_suivi'])}).</p>"
    if e["kwh_attente"]:
        corps += "<p class='petit'>kWh en attente : " + ", ".join(dfr(d) for d in e["kwh_attente"]) + "</p>"
    return bloc("Recommandé et fait", corps, "bloc-derniers", "derniers", ("journal.html#historique", "historique"))


def rendre(e, chemin, quand):
    sa = e["saison"]
    corps = "".join([bloc_jour(e), "<div class='grille-blocs'>", bloc_stock(e), bloc_temps(e), bloc_cumuls(e), bloc_evenements(e), "</div>",
                     "<div class='grille-blocs'>", bloc_calendrier(e), "<div>", bloc_courbe(e), bloc_derniers(e), "</div></div>",
                     "<nav class='liens-bas'><a href='journal.html'>Journal complet</a><a href='strategie/index.html'>Règles et tarif</a>"
                     "<a href='strategie/plan.html'>Plan de saison</a><a href='archives/index.html'>Archives</a></nav>"])
    titre = sa["titre"] + (" : bilan" if e["terminee"] else "")
    sous = f"<p class='sous'>{E(sa['resume'])} Mis à jour le {E(quand)}.</p>"
    page(chemin, titre, corps, quand, sous=sous, contexte=f"{sa['titre']} · {dfr(e['aujourd_hui'], jour=True)}", classe="tableau-de-bord")

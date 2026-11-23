"""Journal de la saison : toutes les journées saisies, calendrier, jours manquants, suivi réel contre plan, mode d'emploi."""
import html, datetime as dt
from rendu import graphes as svg
from rendu.gabarit import page
from rendu.composants import carte, calendrier_saison, legende_calendrier, nb, argent, dfr
from rendu.pages.saison import graphe_stock, tableau_historique
from calculs.saison import fichier_reco
from calculs import valider_saisie

E = html.escape


def _hmin(x):
    """Heure du min observée (EC climate-hourly, heure de Toronto) : « 7 h », « minuit » (0 h le lendemain) ou « — »."""
    h = x.get("heure_min")
    if not h:
        return "—"
    return "minuit" if h[:10] != x["date"].isoformat() else f"{int(h[11:13])} h"


def rendre(e, quand):
    sa = e["saison"]; S = e["saisie"]
    erreurs, avert = valider_saisie.valider()
    h = ["<div class='cartes'>", carte(str(len(S)), "jours saisis", "neutre"),
         carte(str(len(e["manquants"])), "jours à saisir", "ko" if e["manquants"] else "ok", sous=f"depuis le {dfr(e['debut_suivi'])}"),
         carte(str(len(e["kwh_attente"])), "kWh en attente", "prov" if e["kwh_attente"] else "neutre"),
         carte(str(sum(1 for s in S if s["temoin"])), "jours témoins", "neutre"), "</div>"]
    if erreurs or avert:
        h.append("<div class='alerte'><b>Vérification de la saisie</b><ul>" + "".join(f"<li>{E(x)}</li>" for x in erreurs + avert) + "</ul></div>")
    if e["manquants"]:
        h.append("<p class='alerte'>À saisir : " + ", ".join(dfr(d, jour=True) for d in e["manquants"]) + ".</p>")
    h.append("<h2 id='calendrier'>Calendrier</h2>" + calendrier_saison(e["calendrier"], dt.date.fromisoformat(sa["debut"]), dt.date.fromisoformat(sa["fin"]), e["aujourd_hui"]) + legende_calendrier())
    th = tableau_historique(e)
    h.append("<h2 id='historique'>Recommandé, puis fait</h2>" + (th + "<p class='petit'>Recommandé : la recommandation publiée ce matin-là, conservée dans "
             f"<a href='data/{E(fichier_reco(sa))}'>data/{E(fichier_reco(sa))}</a> (un commit automatique par jour). Fait : bûches saisies. "
             "« Suivi » : feu recommandé et fait, ou pas de feu recommandé et aucun feu.</p>" if th else
             "<p class='vide'>Aucune recommandation enregistrée pour l'instant : la première sera conservée au prochain matin.</p>"))
    mo = e["meteo_observee"][::-1]
    if mo:
        h.append("<h2 id='meteo'>Météo observée (30 derniers jours)</h2><table class='compact'><tr><th>Date</th><th>Min</th><th>Max</th><th>Heure du min</th><th>Moyenne</th><th>Source</th></tr>" +
                 "".join(f"<tr><td>{dfr(x['date'], jour=True)}</td><td class=n>{nb(x['tmin'], 1)}</td><td class=n>{nb(x['tmax'], 1)}</td><td class=n>{_hmin(x)}</td><td class=n>{nb(x['t'], 1)}</td>"
                         f"<td>{E(x['etiquette'])}</td></tr>" for x in mo) + "</table>"
                 f"<p class='petit'>Source canonique : {E(e['meteo_libelle'])}, données climatiques quotidiennes ; moyenne = (max + min) / 2 ; heure du min : relevés horaires d'EC (climate-hourly) de la même station, heure de Toronto. "
                 "Les 30 derniers jours sont retéléchargés chaque matin (révisions d'Environnement Canada acceptées) dans "
                 f"<a href='data/{E(e['saison'].get('meteo_observee', ''))}'>data/{E(e['saison'].get('meteo_observee', ''))}</a>. "
                 "Un jour sans mesure (station en panne, ou pas encore publié) est complété par Open-Meteo et marqué « estimation par modèle ».</p>")
    h.append("<h2 id='jours'>Toutes les journées saisies</h2>")
    if S:
        h.append("<table><tr><th>Date</th><th>Bûches</th><th>Stock restant</th><th>kWh</th><th>Événement</th><th>Témoin</th><th>T moy.</th><th>kWh attendus</th><th>Écart</th><th>Valeur</th><th>Remarque</th></tr>" +
                 "".join(f"<tr><td>{dfr(s['date'], jour=True)}</td><td class=n>{nb(s['buches'])}</td><td class=n>{nb(s['stock'])}{' (compté)' if s['compte'] else ''}</td>"
                         f"<td class=n>{nb(s['kwh']) if s['kwh'] is not None else 'en attente'}</td><td>{'oui' if s['evt_saisi'] else ''}</td><td>{'témoin' if s['temoin'] else ''}</td>"
                         f"<td class=n>{nb(s['t'], 1)}</td><td class=n>{nb(s['attendu'])}</td><td class=n>{nb(s['ecart'])}</td><td class=n>{argent(s['valeur'])}</td><td>{E(s['remarque'])}</td></tr>"
                         for s in reversed(S)) + "</table>")
    else:
        h.append("<p class='vide'>Aucune journée saisie pour l'instant : le tableau et les courbes « réel » se rempliront au fil des saisies.</p>")
    # suivi réel contre plan
    h.append("<h2 id='stock'>Stock : réel, plan et projection</h2>" + graphe_stock(e, h=300, w=640) +
             "<p class='petit'>Si la courbe réelle passe plus de 50 bûches sous le plan, ou sous la réserve : ne garder que les événements (règle 5).</p>")
    c = e["courbe"]
    auj = next((i for i, x in enumerate(c) if x["date"] == e["aujourd_hui"]), None)
    h.append("<h2 id='valeur'>Valeur évitée cumulée : réel, plan et projection</h2>" +
             svg.series([dfr(x["date"]) for x in c], [
                 {"nom": "Plan (météo réelle, hors prime)", "valeurs": [x["v_plan"] for x in c], "couleur": "plan", "pointille": True, "points": False},
                 {"nom": "Projection (hors prime)", "valeurs": [x["v_proj"] for x in c], "couleur": "projection", "pointille": True, "points": False},
                 {"nom": "Réel (hors prime)", "valeurs": [x["v_reel"] for x in c], "couleur": "vert", "points": False, "epaisseur": 3}], titre_g="$", h=280, w=640, auj=auj) +
             "<p class='petit'><b>Limite :</b> la prime d'événement réelle (l'électricité évitée pendant les heures de pointe, facturée environ 46 ¢/kWh) "
             "n'est pas mesurée : il faudrait les kWh horaires des jours d'événement. Les montants ci-dessus comptent seulement le tarif hors événement.</p>")
    if S:
        h.append("<h2 id='kwh'>kWh réels et attendus</h2>" + svg.series([dfr(s["date"]) for s in S], [
            {"nom": "kWh réels", "valeurs": [s["kwh"] for s in S], "couleur": "reel"},
            {"nom": "kWh attendus (modèle, météo du jour et bûches)", "valeurs": [s["attendu"] for s in S], "couleur": "sansfeu", "pointille": True}], titre_g="kWh", h=260, w=640))
    h.append("<h2 id='saisir'>Comment saisir</h2><ol>"
             "<li><b>Le plus simple</b> : écrire à l'agent « hier 8 bûches, 62 kWh », ou plusieurs jours d'un coup (« le 20 : 6 bûches, 71 kWh ; le 21 : 0, 65 »). "
             "Il ajoute les lignes, régénère, vérifie, puis fait <b>un commit par saisie</b> ; le site se met à jour en une minute environ.</li>"
             f"<li><b>À la main</b> : <code>data/{E(sa['saisie'])}</code>, une ligne par jour, même sans feu. Colonnes : <code>date</code> (AAAA-MM-JJ) · <code>buches</code> · "
             "<code>kwh</code> (Espace client Hydro-Québec ; peut rester vide et être complété plus tard) · <code>evenement_hq</code> (oui/non) · "
             "<code>jour_temoin</code> (oui si jour froid volontairement sans feu) · <code>stock_compte</code> (facultatif : recomptage réel de la pile) · <code>remarque</code>.</li>"
             "<li>Exemples : <code>2026-12-08,5,61,oui,non,,feu allumé 5 h 30 pour l'événement du matin</code> · <code>2026-12-01,0,72,non,non,330,tas recompté</code></li>"
             "<li>Vérifier et publier : <code>python outils/preparer_donnees.py</code> (valide la saisie : une erreur bloque) puis <code>python outils/generer_site.py</code>, "
             "<code>git commit</code>, <code>git push</code>.</li>"
             "<li>Une valeur inconnue reste vide : on n'invente jamais un chiffre. Les jours sans ligne apparaissent en ✕ à partir du "
             f"{dfr(sa['debut_suivi'])}</li></ol>")
    page("journal.html", f"Journal · {sa['titre']}", "".join(h), quand,
         sous=f"<p class='sous'>Toutes les journées saisies, mises à jour le {E(quand)}. Fichier : <a href='data/{E(sa['saisie'])}'>data/{E(sa['saisie'])}</a>.</p>",
         contexte=f"{sa['titre']} · journal")

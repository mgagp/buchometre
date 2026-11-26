#!/usr/bin/env python3
"""Stratégie 2026-2027 : règles et tarif (strategie/index.html), plan de saison fusionné (strategie/plan.html),
étude météo (strategie/meteo.html), inventaire de la pile (strategie/inventaire.html).
Appelé par outils/generer_site.py ; lit data/protocole*.csv/json."""
import csv, json, os, html, datetime as dt
from chemins import RACINE, OUT
from rendu import graphes as svg
from rendu import gabarit
from rendu.gabarit import page
from rendu.composants import carte, argent, nb, pct
from calculs.recommandation import PLAN, _moins, _plus_min  # paramètres du plan de feu (issue #10), affichés tels quels

E = html.escape
CENTRAL = "2024-2025"  # météo d'hiver « type » (degrés-jours médians des 3 hivers)
MOIS_FR = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
SOURCES = [
    ("Hydro-Québec, Tarifs d'électricité en vigueur le 1er avril 2026, sections 8 (crédit hivernal) et 9 (Flex D)", "https://www.hydroquebec.com/data/documents-donnees/pdf/tarifs-electricite.pdf"),
    ("Hydro-Québec, page Tarif Flex D", "https://www.hydroquebec.com/residentiel/espace-clients/tarifs/tarif-flex-d.html"),
    ("Hydro-Québec, Grille des tarifs 2026 (hausse au 1er avril 2026)", "https://www.hydroquebec.com/data/documents-donnees/pdf/grille-tarifaire.pdf"),
    ("Hydro-Québec, données ouvertes « Événements de pointe – saison hivernale » (TPC-DPC = Flex D, CPC-D = crédit hivernal)", "https://donnees.hydroquebec.com/explore/dataset/evenements-pointe/"),
    ("Hydro-Québec, Historique des résultats (bilan par hiver)", "https://www.hydroquebec.com/residentiel/mieux-consommer/pourquoi-mieux-consommer/bilan-efforts-collectifs/historique-resultats.html"),
    ("Environnement Canada, données climatiques quotidiennes (API GeoMet climate-daily), station Ste-Anne-de-Bellevue 1 (702FHL8), repli Montréal-Trudeau (7025251)", "https://api.weather.gc.ca/collections/climate-daily"),
    ("Open-Meteo, API d'archives (modèle ECMWF IFS), point 45,40 N / −74,03 O : dernier repli, étiqueté « estimation par modèle »", "https://open-meteo.com/en/docs/historical-weather-api"),
    ("Environnement Canada, prévisions pour Vaudreuil-Dorion (recommandation du jour ; Open-Meteo en secours)", "https://meteo.gc.ca/fr/location/index.html?coords=45.4,-74.04"),
]


def lire(rel):
    with open(os.path.join(RACINE, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sousnav(nom):
    return ""  # sous-menu géré par rendu/gabarit.py


def dfr(s):
    d = dt.date.fromisoformat(s) if isinstance(s, str) else s
    return f"{d.day} {MOIS_FR[d.month]}"


def main(quand, a_faire=""):
    P = json.load(open(os.path.join(RACINE, "data/protocole.json"), encoding="utf-8"))
    H = P["hypotheses"]; F = H["flex_D_2026"]; TD = H["tarif_D_2026"]; kb = P["kwh_par_buche"]
    V = P["valeur_buche"]; SE = P["seuils"]; C = P["critique"]; SC = P["stats_creux"]; R = P["resume_sim"]
    MJ = lire("data/protocole_meteo_jours.csv"); CR = lire("data/protocole_creux.csv"); SIM = lire("data/protocole_simulation.csv")
    sous = (f"<p class='sous'>Généré le {E(quand)} par <code>outils/rendu/pages/strategie.py</code>. "
            f"Sources consultées le 2026-11-22 ; météo observée (Environnement Canada) jusqu'au {E(P['meteo_derniere_date'])}.</p>")
    complets = ["2023-2024", "2024-2025", "2025-2026"]
    n_creux = [SC[h]["n"] for h in complets]
    cible_val = [R[h]["strategies"]["cible"]["valeur"] for h in complets]
    quot_val = [R[h]["strategies"]["quotidien"]["valeur"] for h in complets]
    evh = P["evts_par_hiver"]

    def pg(nom, titre, corps):
        page(nom, titre, corps, quand, sous=sous, contexte="Stratégie · saison 2026-2027")

    # ======================= 1. Positionnement =======================
    SK = P["stock"]; SR = SK["resultats"]; NB = SK["buches"]
    rg = [SR[h]["regle_stock"] for h in complets]; op = [SR[h]["optimal_stock"] for h in complets]
    qd = [SR[h]["quotidien_stock"] for h in complets]
    rgp = [SR[h]["regle_stock_plus_corde"] for h in complets]; opp = [SR[h]["optimal_stock_plus_corde"] for h in complets]
    marg = [b["valeur"] - a["valeur"] for a, b in zip(op, opp)]
    marg_r = [b["valeur"] - a["valeur"] for a, b in zip(rg, rgp)]
    import statistics as stt
    rythme = {m: stt.median(SR[h]["regle_stock"]["par_mois"][m] for h in complets) for m in ("11", "12", "01", "02", "03")}
    cc = {h: dict((d[5:], (s, r)) for d, s, r in SK["courbes"][h]) for h in complets}
    jalons = [("1er déc.", "12-01"), ("1er janv.", "01-01"), ("1er févr.", "02-01"), ("1er mars", "03-01")]
    res_j = {lib: cc[CENTRAL].get(k, (None, None))[1] for lib, k in jalons}
    stk_j = {lib: [cc[h].get(k, (None, None))[0] for h in complets] for lib, k in jalons}
    bpe = SK["buches_par_evt_typ"]; bpe_pm = SK.get("buches_par_evt_typ_pm", bpe); bje = SK.get("buches_jour_evt_typ", bpe)
    h = ["<div class='cartes'>",
         carte(f"≈ {NB}", f"bûches en stock (≈ {nb(SK['cordes'], 1)} cordes)", "prov", "inventaire.html", f"inventaire mesuré de la pile, 22 nov. ; fourchette {SK['inventaire']['param']['fourchette_retenue'][0]}–{SK['inventaire']['param']['fourchette_retenue'][1]} ; une seule rangée (confirmé)"),
         carte(f"{min(r['jours_feu'] for r in rg):.0f}–{max(r['jours_feu'] for r in rg):.0f}", "jours de feu que le stock permet", "neutre", "protocole-sim.html", "selon la météo des 3 hivers"),
         carte(f"{argent(min(r['valeur'] for r in rg), 0)}–{argent(max(r['valeur'] for r in rg), 0)}", "valeur évitée cet hiver (règle)", "ok", "protocole-sim.html",
               f"optimum a posteriori {argent(min(r['valeur'] for r in op), 0)}–{argent(max(r['valeur'] for r in op), 0)} ; feu chaque jour {argent(min(r['valeur'] for r in qd), 0)}–{argent(max(r['valeur'] for r in qd), 0)}"),
         carte("100 %", "événements Flex D couverts", "ok", "protocole-sim.html", f"{min(r['evt'] for r in rg):.0f} à {max(r['evt'] for r in rg):.0f} événements selon l'hiver"),
         carte(f"{bje[0]}–{bje[-1]}", "bûches un jour d'événement", "neutre", "#regles", "journée de chauffe complète, un seul feu gardé vivant"),
         carte(f"+{argent(min(marg_r), 0)}–{argent(max(marg_r), 0)}", "valeur d'une corde de plus (règle)", "ko", "#appoint", f"pour ≈ {argent(H['prix_corde_remplacement'], 0)} : achat d'appoint non rentable"),
         "</div>"]
    h.append("<h2>En bref</h2><div class='info'><ol>"
             "<li><b>La situation</b> : tu es au <b>tarif Flex D</b> (confirmé le 22 nov. 2026) et tu n'as pas acheté de bois. L'<a href='inventaire.html'>inventaire mesuré de la pile</a> (22 nov.) donne ≈ " + str(NB) + " bûches (≈ " + nb(SK["cordes"], 1) + " cordes), bien plus que la 1re estimation de " + str(H["stock_ancien"]) + ". "
             "Ce bois est déjà payé : la question n'est plus « le bois est-il rentable ? » mais <b>« où placer ces " + str(NB) + " bûches pour éviter le plus d'électricité possible cet hiver ? »</b></li>"
             f"<li><b>Pourquoi les événements d'abord</b> : hors événement, un kWh évité vaut {nb(F['p2_hiver'] * 100, 3)} ¢ ; pendant un événement (6 h–10 h ou 16 h–20 h, annoncé la veille), "
             f"il vaut {nb(F['pointe'] * 100, 3)} ¢, cinq fois plus. Une bûche brûlée un jour ordinaire vaut {argent(V['flex_hors_evt'])} ; sa chaleur livrée pendant un événement vaut jusqu'à {argent(V['flex_evt'])}.</li>"
             f"<li><b>Ensuite les jours cœur des creux froids</b> : le modèle 2023-24 (kWh = {nb(P['coef'][0], 1)} + {nb(P['coef'][1], 2)} × degrés-jours − {nb(kb, 2)} × bûches) "
             "donne le même gain par bûche quel que soit le froid. Viser les jours froids sert à être prêt pour les grappes d'événements (presque toujours par grand froid) "
             "et à brûler quand la maison peut absorber la chaleur (≈ 0,45 bûche par degré-jour au plus).</li>"
             f"<li><b>Résultat</b> : en suivant la règle de budget ci-dessous, le stock couvre <b>tous les événements</b> et ≈ {min(r['jours_feu'] for r in rg):.0f} à {max(r['jours_feu'] for r in rg):.0f} jours de feu, "
             f"pour ≈ {argent(min(r['valeur'] for r in rg), 0)} à {argent(max(r['valeur'] for r in rg), 0)} d'électricité évitée (taxes incl.), contre {argent(min(r['valeur'] for r in qd), 0)} à "
             f"{argent(max(r['valeur'] for r in qd), 0)} si on étalait le même bois sur chaque jour. Avec ce stock, le bois n'est plus la contrainte : voir <a href='#revision'>ce que change l'inventaire</a>.</li></ol></div>")
    h.append("<h2 id='tarif'>Le tarif Flex D (confirmé)</h2>"
             "<table><tr><th>Élément</th><th>Flex D, tarifs au 1er avril 2026</th></tr>"
             f"<tr><td>Hiver (1er déc.–31 mars), hors événement</td><td>{nb(F['p1_hiver'] * 100, 3)} ¢/kWh jusqu'à 40 kWh × jours de la période, puis <b>{nb(F['p2_hiver'] * 100, 3)} ¢</b></td></tr>"
             f"<tr><td>Pendant un événement de pointe</td><td><b>{nb(F['pointe'] * 100, 3)} ¢/kWh</b> pour toute l'énergie consommée</td></tr>"
             f"<tr><td>Reste de l'année</td><td>Tarif D ({nb(TD['p1'] * 100, 3)} ¢ / {nb(TD['p2'] * 100, 3)} ¢)</td></tr>"
             f"<tr><td>Frais d'accès au réseau</td><td>{nb(F['acces'] * 100, 3)} ¢ par jour</td></tr>"
             "<tr><td>Plages des événements</td><td>6 h–10 h et 16 h–20 h, tous les jours ; sauf 24, 25, 26 et 31 déc., 1er et 2 janv., Vendredi saint et lundi de Pâques</td></tr>"
             "<tr><td>Règles</td><td>4 h par événement, au plus 2 par jour, au moins 6 h entre deux, <b>au plus 120 h par hiver</b> (30 événements de 4 h)</td></tr>"
             "<tr><td>Avis</td><td>Avant 15 h la veille, par courriel ou notification ; aussi affiché sur hydroquebec.com</td></tr>"
             f"<tr><td>Historique (données ouvertes HQ)</td><td>2024-2025 : {evh['2024-2025']['evenements']} événements sur {evh['2024-2025']['jours']} jours ({nb(evh['2024-2025']['heures'])} h) · "
             f"2025-2026 : {evh['2025-2026']['evenements']} sur {evh['2025-2026']['jours']} jours ({nb(evh['2025-2026']['heures'])} h ; 20 selon le bilan HQ) · 2026-2027 : {evh['2026-2027']['evenements']} à ce jour</td></tr></table>"
             f"<p class='petit'>Option écartée : l'option de crédit hivernal (tarif D + crédit de {nb(H['credit_hivernal_2026'] * 100, 3)} ¢ par kWh effacé), fermée aux nouveaux abonnements depuis le 31 mars 2026.</p>")
    h.append("<h2>Valeur d'une bûche selon le moment</h2><table><tr><th>Situation</th><th>Prix du kWh évité</th><th>Valeur d'une bûche (taxes incl.)</th></tr>" +
             "".join(f"<tr><td>{E(a)}</td><td class=n>{nb(p * 100, 3)} ¢</td><td class=n>{argent(v)}</td></tr>" for a, p, v in [
                 ("Flex D, hiver hors événement (jour ordinaire)", F["p2_hiver"], V["flex_hors_evt"]),
                 ("Flex D, pendant un événement (si toute la chaleur tombe dans la fenêtre)", F["pointe"], V["flex_evt"]),
                 ("Pour comparaison : tarif D 2026, 2e tranche", TD["p2"], V["tarif_D"])]) + "</table>"
             f"<p class='petit'>Valeur = {nb(kb, 2)} kWh/bûche × prix × 1,14975 (TPS+TVQ). Pendant un événement, on suppose qu'une bûche livre {pct(H['part_buche_dans_fenetre'])} "
             f"de sa chaleur dans la fenêtre de 16 h (feu allumé dès 6 h, déjà à pleine chaleur), mais seulement {pct(H['part_buche_dans_fenetre_matin'])} dans celle de 6 h (feu allumé à 6 h, pleine chaleur vers 7 h 30), "
             f"et que le besoin de chauffage dans la fenêtre est plafonné (≈ {nb(H['facteur_pointe_horaire'], 2)} × la moyenne horaire du jour) : "
             f"la fenêtre seule demande {bpe[0]} à {bpe[-1]} bûches le matin, {bpe_pm[0]} à {bpe_pm[-1]} l'après-midi (−6 °C à −18 °C). "
             f"Le jour d'un événement reste une journée de chauffe complète ({bje[0]} à {bje[-1]} bûches).</p>")
    IV = SK["inventaire"]; RA = H["regle_ancienne"]
    anc = [SR[hh]["ancien_ancienne_regle"] for hh in complets]; sar = [SR[hh]["stock_ancienne_regle"] for hh in complets]
    sb = [SR[hh]["regle_stock_bas"] for hh in complets]; sh = [SR[hh]["regle_stock_haut"] for hh in complets]
    mm = lambda L, k, f=nb: f"{f(min(r[k] for r in L), 0) if f is argent else f(min(r[k] for r in L))}–{f(max(r[k] for r in L), 0) if f is argent else f(max(r[k] for r in L))}"
    h.append("<h2 id='bois'>Le stock de bois (révisé le 22 nov. 2026)</h2><ul>"
             f"<li><b>Stock de départ</b> : <b>≈ {NB} bûches</b>, tiré de l'<a href='inventaire.html'>inventaire mesuré de la pile</a> "
             f"({nb(IV['surface'], 2)} pi² de face × {nb(IV['param']['densite'], 1)} bûches/pi²), soit ≈ {nb(SK['cordes'], 1)} cordes à {H['buches_par_corde']} bûches/corde "
             f"ou ≈ {nb(IV['cordes_face'], 1)} cordes de face (4 × 8 pi, bûches de 16 po). Fourchette retenue : {IV['param']['fourchette_retenue'][0]} à {IV['param']['fourchette_retenue'][1]} bûches ; "
             f"tests plus larges : {IV['buches_bas']} à {IV['buches_haut']}. Une seule rangée en profondeur : <b>confirmé par Marc</b>. Reste incertaine : la densité, tirée d'une seule corde d'étalonnage.</li>"
             f"<li><b>Ce qu'il remplace</b> : la 1re estimation du même jour, ≈ {nb(H['cordes_restantes_ancien'], 1)} corde × {H['buches_par_corde']} = {H['stock_ancien']} bûches (fourchette 260 à 435), "
             "qui reposait sur une impression et non sur une mesure. L'écart (× 2,5) est signalé : 4,1 cordes, c'est presque l'achat complet de 2023-24 (4 cordes) ; voir la "
             "<a href='inventaire.html#plausibilite'>vérification de plausibilité</a>.</li>"
             "<li><b>Paramètre daté</b> : le stock de départ est un paramètre (<code>data/inventaire_pile_2026-11.csv</code>, <code>outils/calculs/inventaire.py</code>), pas une ligne de saisie. "
             "La colonne <code>stock_compte</code> de la saisie reste réservée à un vrai recomptage.</li>"
             "<li><b>Coût</b> : déjà payé (coût irrécupérable) ; il n'entre pas dans la décision de brûler. "
             f"Repère secondaire : valeur de remplacement ≈ {argent(H['prix_corde_remplacement'])} la corde (425 $ ÷ 4 + 25 $), soit ≈ {argent(SK['valeur_remplacement'], 0)} pour le stock.</li></ul>")
    h.append("<h2 id='revision'>Ce que change l'inventaire (révision du 22 nov. 2026)</h2>"
             "<table><tr><th>Simulation (3 météos)</th><th>Stock</th><th>Jours de feu</th><th>Bûches brûlées</th><th>Restantes au 31 mars</th><th>Événements couverts</th><th>Valeur évitée</th></tr>" +
             "".join(f"<tr{' class=tot' if k == 'rg' else ''}><td>{lib}</td><td class=n>{L[0]['stock_initial']:.0f}</td><td class=n>{mm(L, 'jours_feu')}</td><td class=n>{mm(L, 'buches')}</td>"
                     f"<td class=n>{mm(L, 'reste')}</td><td class=n>{'tous' if all(r['evt_couverts'] == r['evt'] for r in L) else 'non'}</td><td class=n>{mm(L, 'valeur', argent)}</td></tr>"
                     for k, lib, L in (("a", f"Avant : ancien stock, ancienne règle (≤ {nb(RA['seuil'])} °C, {RA['max']} bûches, surplus au 1er févr.)", anc),
                                       ("b", "Inventaire, ancienne règle", sar),
                                       ("rg", f"<b>Inventaire, règle révisée</b> (≤ {nb(H['regle_seuil_coeur'])} °C, {H['regle_max_coeur']} bûches, surplus au 1er janv.)", rg),
                                       ("q", "Inventaire, même bois étalé chaque jour", qd),
                                       ("o", "Inventaire, optimum a posteriori", op),
                                       ("lo", f"Sensibilité : stock bas ({sb[0]['stock_initial']:.0f}), règle révisée", sb),
                                       ("hi", f"Sensibilité : stock haut ({sh[0]['stock_initial']:.0f}), règle révisée", sh))) + "</table>"
             "<div class='info'><b>Lecture honnête</b><ul>"
             "<li><b>Le stock n'est plus la contrainte.</b> Avec ≈ " + str(NB) + " bûches, tous les événements sont couverts dans les trois météos, même dans le scénario bas. "
             f"L'ancienne règle, conçue pour {H['stock_ancien']} bûches, laisserait {mm(sar, 'reste')} bûches inutilisées au 31 mars.</li>"
             f"<li><b>Règles 3 et 4 assouplies</b> : seuil des jours cœur relevé de {nb(RA['seuil'])} °C à {nb(H['regle_seuil_coeur'])} °C ; plafond par jour sans événement de {RA['max']} à {H['regle_max_coeur']} bûches "
             "(toujours sous le plafond d'absorption de 0,45 bûche par degré-jour et sous le maximum observé de 15) ; libération du surplus avancée du 1er février au 1er janvier.</li>"
             "<li><b>Règles 1 et 2 révisées le 26 nov.</b> : un jour d'événement est une journée de chauffe complète (au moins " + str(H["regle_plancher_evt"]) + " bûches), "
             "et la réserve passe à " + str(H["regle_buches_evt"]) + " bûches par événement encore attendu (avant : 4-5 bûches par événement et une réserve de 5). "
             "Règles 5 et 6 inchangées : freinage si le stock passe sous le plan, jours témoins.</li>"
             f"<li><b>Le ciblage compte moins qu'avant.</b> Étaler le même bois chaque jour donnerait une valeur semblable ({mm(qd, 'valeur', argent)}) : dans le modèle, une bûche vaut la même chose chaque jour "
             "hors événement, et le stock suffit maintenant pour couvrir les événements de toute façon. Le protocole garde son utilité : ne jamais rater un événement (5 fois plus payant), "
             "et ne pas s'épuiser trop tôt si l'inventaire est surestimé.</li>"
             "<li><b>Le bois qui reste au 31 mars n'est pas perdu</b> : il sert l'hiver suivant (au même prix de kWh, ou plus cher si les tarifs montent). Brûler plus tôt ou plus tard est presque indifférent ; "
             "l'important est de ne pas manquer de bois les jours d'événement.</li></ul></div>")
    h.append("<h2 id='regles'>La règle de budget (révisée les 22 et 26 nov. 2026)</h2><ol>"
             f"<li><b>Événement annoncé (avis la veille avant 15 h) : toujours, et c'est une journée de chauffe complète</b> (décision du 26 nov.) : "
             f"au moins <b>{H['regle_plancher_evt']} bûches</b>, comme un jour de grand froid (règles 3 et 4), plus si les fenêtres en demandent davantage, au plus {H['buches_max_jour']}. "
             f"Un seul feu gardé vivant toute la journée (voir <a href='#moment'>le moment du feu</a>). On peut puiser dans la réserve. "
             f"<span class='petit'>Avant le 26 nov. : 4 à 5 bûches pour la seule fenêtre.</span></li>"
             f"<li><b>Réserve pour les événements</b> : garder {H['regle_buches_evt']} bûches par événement encore attendu <span class='petit'>(avant le 26 nov. : 5)</span> "
             f"(≈ {H['evts_attendus']} par hiver, surtout en janvier). En pratique : ≈ {res_j['1er déc.']} bûches au 1er déc., ≈ {res_j['1er janv.']} au 1er janv., "
             f"≈ {res_j['1er févr.']} au 1er févr., ≈ {res_j['1er mars']} au 1er mars. Avec l'inventaire, c'est moins du quart du stock.</li>"
             f"<li><b>Jour cœur d'un creux froid</b> (prévision : T moyenne ≤ {nb(H['regle_seuil_coeur'])} °C et nettement sous la normale) : feu, jusqu'à <b>{H['regle_max_coeur']} bûches</b> "
             f"(au plus 0,45 bûche par degré-jour), si le stock après le feu reste au-dessus de la réserve. <span class='petit'>Avant le 22 nov. : ≤ {nb(RA['seuil'])} °C et {RA['max']} bûches.</span></li>"
             f"<li><b>À partir du 1er janvier</b> : le surplus au-dessus de la réserve peut aller à tout jour froid (≤ 0 °C), {H['regle_max_coeur']} bûches au plus. "
             "<span class='petit'>Avant : à partir du 1er février.</span> Le stock qui reste en avril n'est pas perdu (il sert l'hiver suivant).</li>"
             "<li><b>Si le stock baisse plus vite que prévu</b> (plus de 50 bûches sous le plan, c.-à-d. la règle appliquée à la météo réelle, ou recomptage plus bas) : suspendre les feux de jours cœur, "
             "ne garder que les événements jusqu'à revenir sur la courbe.</li>"
             "<li><b>Jour témoin</b> : environ un jour froid par mois sans feu (et sans événement), noté « témoin ».</li>"
             "<li><b>Saisie</b> chaque jour, même sans feu, dans <code>data/saisie_2026-2027.csv</code> ; le <a href='journal.html'>Journal</a> suit le stock restant contre le plan.</li></ol>"
             "<p class='petit'>La recommandation de l'accueil applique ces règles telles quelles (<code>outils/calculs/recommandation.py</code>, la même fonction que la simulation), "
             "à la prévision d'Environnement Canada (Open-Meteo en secours). « Nettement sous la normale » : jour d'un creux froid (moyenne sur 3 jours au moins 2 °C sous la médiane "
             "des 31 jours autour, réel puis prévision) et au moins 3 °C sous cette médiane. Le jour témoin reste au choix de Marc : il n'est pas proposé automatiquement.</p>"
             "<table><tr><th>Jalon</th><th>Stock prévu (3 météos)</th><th>Réserve événements</th></tr>" +
             "".join(f"<tr><td>{lib}</td><td class=n>{' / '.join(str(x) for x in stk_j[lib])}</td><td class=n>{res_j[lib]}</td></tr>" for lib, _ in jalons) + "</table>"
             "<p class='petit'>Rythme médian simulé : nov. " + nb(rythme["11"]) + " · déc. " + nb(rythme["12"]) + " · janv. " + nb(rythme["01"]) + " · févr. " + nb(rythme["02"]) + " · mars " + nb(rythme["03"]) +
             " bûches. Ordre des météos : 2023-24 / 2024-25 / 2025-26.</p>")
    def _hp(hm):
        return f"{int(hm[:2])} h" + (f" {hm[3:]}" if hm[3:] != "00" else "")
    ch = PLAN["chauffe_min"]
    h.append("<h2 id='moment'>Le moment du feu (23 nov. 2026, révisé le 26 nov.)</h2><ul>"
             f"<li><b>Un feu met ≈ {ch // 60} h {ch % 60:02d} à donner sa pleine chaleur</b> : on allume ce temps-là avant le moment visé, événements compris, "
             f"mais jamais avant <b>{_hp(PLAN['allumage_tot'])}</b> (heure réaliste pour Marc). Le matin, la pleine chaleur arrive donc vers {_hp(_plus_min(PLAN['allumage_tot'], ch))}.</li>"
             f"<li><b>Un seul feu, gardé vivant toute la journée</b> (décision du 26 nov. ; c'est ce que Marc faisait en 2023-24, jamais jusqu'aux braises entre deux fenêtres) : "
             f"on allume une fois, puis on recharge ≈ toutes les {PLAN['recharge_min'] // 60} h ; les bûches de la journée sont réparties sur les recharges. "
             f"Tous les jours de feu, jours d'événement compris : allumer à <b>{_hp(max(_moins(PLAN['matin'], ch), PLAN['allumage_tot']))}</b>, "
             "même quand seul l'événement de 16 h est annoncé et que le matin est doux (journée de chauffe complète). "
             "<span class='petit'>Avant le 26 nov. : deux feux, le matin et l'après-midi.</span></li>"
             f"<li><b>La nuit</b> : dernière charge vers {_hp(PLAN['reduire'])}, puis réduire pour ne pas surchauffer l'étage pendant le sommeil, sauf si le min prévu de la nuit est ≤ {nb(PLAN['nuit_froide'])} °C : "
             f"alors dernière charge vers {_hp(PLAN['charge_nuit'])}. Un jour d'événement, on entretient au moins jusqu'à la fin de la fenêtre.</li>"
             "<li>Le plan ne change ni la décision de faire un feu ni le nombre de bûches (règles ci-dessus, sur la moyenne (max + min) / 2). "
             "Heures et seuils : points de départ, à ajuster selon le confort. L'heure du min affichée vient de la prévision horaire d'EC (24 h), sinon d'Open-Meteo, marqué « (modèle) ».</li>"
             "<li>Pourquoi le petit matin : sur trois hivers (Ste-Anne-de-Bellevue), le creux de la nuit tombe entre 4 h et 8 h une nuit sur deux, en soirée une nuit sur cinq ; "
             f"la fenêtre de 6 h à 10 h est la plus froide de la journée. Analyse : <a href='{gabarit.DEPOT}/issues/10'>issue #10</a>.</li></ul>")
    h.append("<h2 id='appoint'>Un achat d'appoint vaut-il la peine ?</h2>"
             f"<p><b>Non.</b> Une corde de plus (≈ {H['buches_par_corde']} bûches, ≈ {argent(H['prix_corde_remplacement'], 0)}) ajouterait {' / '.join(argent(x, 0) for x in marg_r)} de valeur avec la règle "
             f"(selon la météo) et au mieux {argent(min(marg), 0)} à {argent(max(marg), 0)} en connaissant tout l'hiver d'avance. Le stock couvre déjà tous les événements ; chaque bûche de plus irait à un jour ordinaire, "
             f"à {argent(V['flex_hors_evt'])} pièce, sous son coût de remplacement (≈ {argent(H['prix_corde_remplacement'] / H['buches_par_corde'])}). "
             "Même dans le scénario bas de l'inventaire, la réserve d'événements n'est pas menacée. À revoir seulement si un recomptage donne moins de ≈ 300 bûches "
             "(par exemple si une partie de la pile est plus creuse que prévu).</p>")
    h.append("<h2>Sources</h2><ul>" + "".join(f"<li><a href='{u}'>{E(t)}</a></li>" for t, u in SOURCES) +
             "</ul><p class='petit'>Consultées le 22 novembre 2026. Les données ouvertes d'Hydro-Québec sont « brutes, sans garantie » ; l'avis officiel par courriel a priorité.</p>")
    pg("protocole.html", "Stratégie 2026-2027 : règles et tarif", "".join(h) + a_faire)


    # ======================= 2. Étude météo =======================
    clim = P["climatologie"]
    labs = [dfr(c["date"]) for c in clim]
    i_c0 = next(i for i, c in enumerate(clim) if c["date"] == C["debut"]); i_c1 = next(i for i, c in enumerate(clim) if c["date"] == C["fin"])
    i_m0 = next(i for i, c in enumerate(clim) if c["date"].endswith("11-15")); i_m1 = next(i for i, c in enumerate(clim) if c["date"].endswith("03-15"))
    par_h = {}
    for j in MJ:
        par_h.setdefault(j["hiver"], {})[j["date"][5:]] = float(j["t_moy"])
    ser = [{"nom": f"T moy. {hv}", "valeurs": [par_h.get(hv, {}).get(c["date"][5:]) for c in clim], "couleur": col, "epaisseur": 1, "points": False}
           for hv, col in (("2023-2024", "gris_pale"), ("2024-2025", "bleu_pale"), ("2025-2026", "violet_pale"))]
    ser.append({"nom": "Moyenne 3 hivers lissée (15 j)", "valeurs": [c["t_lisse"] for c in clim], "couleur": "encre", "epaisseur": 2.5, "points": False})
    if "2026-2027" in par_h:
        ser.append({"nom": "2026-2027 (à ce jour)", "valeurs": [par_h["2026-2027"].get(c["date"][5:]) for c in clim], "couleur": "evt", "epaisseur": 2, "points": False})
    g_clim = svg.series(labs, ser, titre_g="°C", h=320, zones=[(i_m0, i_m1, "fenêtre de Marc : 15 nov.–15 mars", "zone_marc", False), (i_c0, i_c1, "période critique", "zone_critique", True)])
    h = ["<h2 id='critique'>(a) La période critique</h2>"
         f"<p>Définition : jours où la température moyenne des trois derniers hivers, lissée sur 15 jours, est <b>à 0 °C ou moins</b> (≥ 18 degrés-jours par jour). "
         f"Résultat : <b>du {dfr(C['debut'])} au {dfr(C['fin'])}</b> ({C['jours']} jours). Elle concentre {pct(C['part_dj'])} des degrés-jours d'octobre à avril "
         f"et {pct(C['part_evt'])} des événements Flex D connus. Ta fenêtre « mi-novembre à mi-mars » donne presque la même chose ({pct(C['marc_part_dj'])} des degrés-jours, "
         f"{pct(C['marc_part_evt'])} des événements) : elle commence deux semaines plus tôt et finit deux semaines plus tôt. "
         "Les événements, eux, ne peuvent survenir que du 1er décembre au 31 mars.</p>", g_clim,
         "<p class='petit'>Bleu : période critique calculée ; orangé : ta fenêtre. Fines lignes : chaque hiver ; rouge : 2026-2027 à ce jour.</p>"]
    # cycles
    h.append("<h2 id='cycles'>(b) Les cycles : redoux puis coups de froid</h2>"
             "<p><b>Méthode simple</b> : (1) température moyenne du jour lissée sur 3 jours ; (2) « normale récente » = médiane mobile sur 31 jours ; "
             f"(3) un <b>creux</b> = au moins 2 jours de suite où la température lissée est ≥ {nb(-H['seuil_creux'])} °C sous la normale récente (un jour de répit toléré) ; "
             f"(4) les <b>jours cœur</b> du creux = jours où la température du jour est ≥ {nb(-H['seuil_coeur'])} °C sous la normale. On compte les creux qui touchent la période critique.</p>"
             "<table><tr><th>Hiver</th><th>Creux</th><th>Écart médian entre deux creux</th><th>Durée médiane</th><th>Jours cœur médians</th><th>Jours en creux (total)</th><th>Jours cœur (total)</th><th>Événements Flex D dans un creux</th></tr>" +
             "".join(f"<tr><td>{hv}{'' if s['complet'] else ' (en cours)'}</td><td class=n>{s['n']}</td><td class=n>{nb(s['cycle_med']) + ' j' if s['cycle_med'] else '—'}</td>"
                     f"<td class=n>{nb(s['jours_med'], 1)} j</td><td class=n>{nb(s['coeur_med'], 1)} j</td><td class=n>{s['jours_tot']}</td><td class=n>{s['coeur_tot']}</td>"
                     f"<td class=n>{(str(s['evt_dans_creux']) + ' / ' + str(s['evt_tot'])) if hv in ('2024-2025', '2025-2026') else 'pas de données HQ'}</td></tr>" for hv, s in SC.items()) + "</table>"
             f"<div class='info'><b>Lecture</b> : environ <b>{min(n_creux)} à {max(n_creux)} coups de froid par hiver</b> dans la période critique, un tous les 10 à 16 jours ; "
             f"chacun dure typiquement 3 à 4 jours, dont <b>2 à 3 jours cœur</b>. Viser les jours cœur donne ≈ {min(SC[h]['coeur_tot'] for h in complets)} à "
             f"{max(SC[h]['coeur_tot'] for h in complets)} jours de feu ciblé par hiver, auxquels s'ajoutent les jours d'événement hors creux.</div>")
    for hv in ["2023-2024", "2024-2025", "2025-2026", "2026-2027"]:
        js = [j for j in MJ if j["hiver"] == hv and "11-01" <= j["date"][5:] or (j["hiver"] == hv and j["date"][5:] <= "03-31")]
        js = [j for j in MJ if j["hiver"] == hv and (j["date"][5:] >= "11-01" or j["date"][5:] <= "03-31")]
        if not js:
            continue
        zones, i = [], 0
        while i < len(js):
            if js[i]["creux"]:
                k = i
                while k + 1 < len(js) and js[k + 1]["creux"] == js[i]["creux"]:
                    k += 1
                zones.append((i, k, f"creux {js[i]['creux']}", "zone_creux", False)); i = k + 1
            else:
                i += 1
        g = svg.series([dfr(j["date"]) for j in js], [
            {"nom": "Événements Flex D (axe droit)", "valeurs": [int(j["evenements_flexd"]) or None for j in js], "couleur": "evt", "type": "bar", "axe": "d", "opacite": 0.8},
            {"nom": "T moy. du jour", "valeurs": [float(j["t_moy"]) for j in js], "couleur": "gris_bleu", "epaisseur": 1, "points": False},
            {"nom": "T lissée 3 j", "valeurs": [float(j["t_lisse_3j"]) for j in js], "couleur": "reel", "points": False},
            {"nom": "Normale récente (médiane 31 j)", "valeurs": [float(j["mediane_31j"]) for j in js], "couleur": "encre", "pointille": True, "epaisseur": 1.2, "points": False},
            {"nom": "Jours cœur", "valeurs": [float(j["t_moy"]) if j["coeur"] == "1" else None for j in js], "couleur": "bleu_fonce", "type": "bar", "opacite": 0.35},
        ], titre_g="°C", titre_d="évts", zones=zones, h=280)
        h.append(f"<h3>Hiver {hv}{' (en cours)' if hv == '2026-2027' else ''}</h3>" + g)
    h.append("<details><summary>Liste de tous les creux</summary><table><tr><th>Creux</th><th>Du</th><th>Au</th><th>Jours</th><th>Jours cœur</th><th>Jour le plus froid</th><th>T moy. du creux</th><th>Degrés-jours</th><th>Événements Flex D</th><th>Période critique</th></tr>" +
             "".join(f"<tr><td>{c['id']}</td><td>{c['debut']}</td><td>{c['fin']}</td><td class=n>{c['jours']}</td><td class=n>{c['jours_coeur']}</td><td>{c['date_min']} ({nb(float(c['t_min_jour']), 1)} °C)</td>"
                     f"<td class=n>{nb(float(c['t_moy']), 1)} °C</td><td class=n>{nb(float(c['dj']))}</td><td class=n>{c['evt']}</td><td>{'oui' if c['dans_critique'] == 'True' else 'non'}</td></tr>" for c in CR) + "</table></details>")
    # événements
    pr = P["proba_evt"]
    g_p = svg.series([("≤ −15 °C" if p["de"] == -99 else (f"> {p['de']} °C" if p["a"] == 99 else f"{p['de']} à {p['a']} °C")) for p in pr], [
        {"nom": "Probabilité d'un événement Flex D ce jour-là (%)", "valeurs": [round(p["p"] * 100) for p in pr], "couleur": "evt", "type": "bar"}], titre_g="%", h=240, w=700)
    h.append("<h2 id='evenements'>(c) Quand tombent les événements de pointe ?</h2>"
             "<p>Historique publié par Hydro-Québec (données ouvertes, offre TPC-DPC = Flex D), croisé avec la température moyenne du jour à Vaudreuil-Dorion, hivers 2024-2025 et 2025-2026 (1er déc.–31 mars) :</p>" + g_p +
             "<table><tr><th>T moy. du jour</th><th>Jours</th><th>Jours avec événement</th><th>Probabilité</th></tr>" +
             "".join(f"<tr><td>{'≤ −15' if p['de'] == -99 else ('> ' + str(p['de'])) if p['a'] == 99 else str(p['de']) + ' à ' + str(p['a'])} °C</td><td class=n>{p['jours']}</td><td class=n>{p['jours_evt']}</td><td class=n>{pct(p['p'])}</td></tr>" for p in pr) + "</table>"
             "<p>Les événements suivent la demande de tout le Québec, pas seulement la température locale : sous −12 °C, un jour sur trois à un sur deux ; entre −12 et −9 °C, un sur quatre ; "
             "au-dessus de −6 °C, presque jamais. Ils arrivent en grappes pendant les coups de froid (souvent matin et soir). Le matin (6 h–10 h) domine. "
             "Pour 2023-2024 (avant les données ouvertes), la simulation suppose un événement les jours ≤ −12 °C.</p>")
    # gain
    I = P["interaction"]
    lignes = [{"nom": f"Météo {hv}", "couleur": col, "pts": P["courbes"][hv]} for hv, col in (("2023-2024", "gris_bleu"), ("2024-2025", "reel"), ("2025-2026", "marc"))]
    g_c = svg.courbes(lignes, tx="Part des bûches (les plus rentables d'abord)", ty="Part de la valeur")
    t = ["<table><tr><th>Météo</th><th>Degrés-jours 7 nov.–31 mars</th><th>Événements</th><th>Stratégie</th><th>Jours de feu</th><th>Bûches</th><th>Valeur hors événement</th><th>Prime d'événement</th><th>Valeur totale</th><th>vs " + argent(P["prix_ref"], 0) + "</th></tr>"]
    for hv in complets:
        r = R[hv]
        for sn, lib in (("quotidien", "Chaque jour (comme 2023-24)"), ("cible", "Ciblée (protocole)")):
            s = r["strategies"][sn]
            t.append(f"<tr><td>{hv}</td><td class=n>{nb(r['dj_saison'])}</td><td class=n>{nb(s['evt'])}{'' if r['evts_reels'] else ' (prédits)'}</td><td>{lib}</td><td class=n>{nb(s['jours_feu'])}</td>"
                     f"<td class=n>{nb(s['buches'])}</td><td class=n>{argent(s['base'], 0)}</td><td class=n>{argent(s['prime'], 0)}</td><td class=n><b>{argent(s['valeur'], 0)}</b></td>"
                     f"<td class=n>{'+' if s['valeur'] >= P['prix_ref'] else ''}{pct(s['valeur'] / P['prix_ref'] - 1)}</td></tr>")
    t.append("</table>")
    h.append("<h2 id='gain'>(d) Combien rapporte le ciblage ?</h2>"
             "<div class='info'>Cette section garde la référence d'une <b>saison complète de bois</b> (≈ 928 bûches, comme 2023-24). Pour cet hiver, avec le stock d'environ "
             + str(P["stock"]["buches"]) + " bûches, voir la <a href='protocole-sim.html'>simulation à stock limité</a>.</div>"
             f"<p><b>Honnêtement :</b> avec le modèle linéaire, une bûche évite ≈ {nb(kb, 1)} kWh quel que soit le froid. Le test d'une interaction bûches × degrés-jours donne "
             f"{nb(I['coef'][3], 3)} ± {nb(I['se'][3], 3)} : non significatif, et plutôt dans le sens d'un gain <i>plus faible</i> par grand froid "
             f"({nb(I['kwh_par_buche_selon_dj']['15'], 1)} kWh à 15 DJ, {nb(I['kwh_par_buche_selon_dj']['30'], 1)} kWh à 30 DJ). On ne peut donc pas affirmer qu'une bûche rapporte plus quand il fait froid. "
             "Le gain du ciblage vient de trois choses : (1) les <b>événements</b> facturés 5 fois plus cher, qui tombent presque tous dans les creux ; (2) la <b>limite de bois</b> (≈ 928 bûches) "
             "qu'on réserve aux jours qui comptent au lieu de l'étaler ; (3) le <b>plafond d'absorption</b> : un jour doux ne peut pas utiliser beaucoup de bûches.</p>" + "".join(t) +
             "<div class='deux'><div>" + g_c + "</div><div><p class='petit'>La courbe classe les bûches de la stratégie ciblée de la plus rentable à la moins rentable. "
             "Les premières (celles des événements) captent une part de la valeur nettement supérieure à leur part du bois ; ensuite la courbe devient droite : chaque bûche vaut la même chose.</p>"
             "<p class='petit'>« Chaque jour » : les mêmes bûches réparties selon les degrés-jours, sans viser les fenêtres ; la part de leur chaleur qui tombe dans une fenêtre d'événement "
             "est supposée proportionnelle à la durée (4 h sur 24).</p></div></div>")
    pg("protocole-meteo.html", "Étude statistique météo (3 hivers + 2026-2027)", "".join(h))

    # ======================= 3. Simulation (stock limité) =======================
    SS = lire("data/protocole_simulation_stock.csv")
    def ss(hv):
        rows = [s for s in SS if s["hiver_meteo"] == hv]
        for s in rows:
            for k in ("t_moy", "dj18", "buches", "stock_restant", "reserve_evt", "kwh_evites", "kwh_evites_pointe", "kwh_sans_feu", "kwh_avec_feu", "valeur_base", "valeur_pointe"):
                s[k] = float(s[k])
            s["evenements"] = int(s["evenements"]); s["val"] = s["valeur_base"] + s["valeur_pointe"]
        return rows
    cen = ss(CENTRAL)
    labs = [dfr(s["date_2026_2027"]) for s in cen]
    g_sim = svg.series(labs, [
        {"nom": "Bûches prévues (axe droit)", "valeurs": [s["buches"] or None for s in cen], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.55},
        {"nom": "Événements (axe droit)", "valeurs": [s["evenements"] * 3 or None for s in cen], "couleur": "evt", "type": "bar", "axe": "d", "opacite": 0.9, "sans_legende": True},
        {"nom": "T moy. (°C)", "valeurs": [s["t_moy"] for s in cen], "couleur": svg.COUL["temp"], "points": False, "epaisseur": 1.2},
    ], titre_g="°C", titre_d="bûches", liens=[f"protocole-sim-jours.html#s-{s['date_2026_2027']}" for s in cen], h=300)
    ser_stk = [{"nom": f"Stock restant, météo {hv}", "valeurs": [s["stock_restant"] for s in ss(hv)][:len(cen)], "couleur": col, "points": False, "epaisseur": 2.5 if hv == CENTRAL else 1.3}
               for hv, col in (("2023-2024", "gris_bleu"), ("2024-2025", "reel"), ("2025-2026", "marc"))]
    ser_stk.append({"nom": "Réserve pour les événements", "valeurs": [s["reserve_evt"] for s in cen], "couleur": "evt", "pointille": True, "points": False})
    g_stk = svg.series(labs, ser_stk, titre_g="bûches", h=260)
    tb = ["<table><tr><th>Météo</th><th>Événements</th><th>Stratégie</th><th>Jours de feu</th><th>Bûches brûlées</th><th>Restantes au 31 mars</th><th>Événements couverts</th>"
          "<th>Valeur hors événement</th><th>Prime d'événement</th><th>Valeur totale</th></tr>"]
    for hv in complets:
        for k, lib in (("regle_stock", "Règle de budget"), ("optimal_stock", "Optimum a posteriori"), ("quotidien_stock", "Même bois étalé chaque jour"),
                       ("regle_stock_plus_corde", "Règle + 1 corde"), ("optimal_stock_plus_corde", "Optimum + 1 corde")):
            r = SR[hv][k]
            tb.append(f"<tr{' class=tot' if k == 'regle_stock' else ''}><td>{hv}</td><td class=n>{nb(r['evt'])}{'' if R[hv]['evts_reels'] else ' (prédits)'}</td><td>{lib}</td><td class=n>{nb(r['jours_feu'])}</td>"
                      f"<td class=n>{nb(r['buches'])} / {nb(r['stock_initial'])}</td><td class=n>{nb(r['reste'])}</td><td class=n>{nb(r['evt_couverts'])}/{nb(r['evt'])}</td>"
                      f"<td class=n>{argent(r['base'], 0)}</td><td class=n>{argent(r['prime'], 0)}</td><td class=n><b>{argent(r['valeur'], 0)}</b></td></tr>")
    tb.append("</table>")
    r_c = SR[CENTRAL]["regle_stock"]
    evb = sum(s["buches"] for s in cen if s["evenements"])
    h = ["<div class='alerte'><b>Aperçu simulé</b>, pas des données réelles. Météo d'un hiver type rejouée sur le calendrier 2026-2027 : "
         f"<b>{CENTRAL}</b> (degrés-jours médians ; ses événements Flex D réels). Hypothèses : stock ≈ {NB} bûches (déjà payées), Flex D 2026, {nb(kb, 2)} kWh/bûche, "
         "règle de budget appliquée jour après jour, sans connaître la suite de l'hiver (sauf l'avis de la veille).</div>",
         "<div class='cartes'>", carte(nb(r_c["jours_feu"]), "jours de feu", "neutre", sous=f"dont {sum(1 for s in cen if s['evenements'] and s['buches'])} jours d'événement"),
         carte(f"{nb(r_c['buches'])}/{NB}", "bûches utilisées", "neutre", sous=f"{nb(evb)} pour les événements ; reste {nb(r_c['reste'])}"),
         carte(f"{nb(r_c['evt_couverts'])}/{nb(r_c['evt'])}", "événements couverts", "ok"),
         carte(argent(r_c["valeur"], 0), "valeur évitée, taxes incl.", "ok", sous=f"{argent(r_c['base'], 0)} + prime {argent(r_c['prime'], 0)}"),
         carte(pct(r_c["prime"] / r_c["valeur"]), "de la valeur vient des événements", "neutre", sous=f"avec {pct(evb / max(1, r_c['buches']))} des bûches"),
         "</div><h2>La saison simulée</h2><p class='petit'>Barres rouges : jours d'événement. Cliquer une barre ouvre la journée.</p>", g_sim,
         "<h2>Stock restant (les 3 météos) et réserve pour les événements</h2>", g_stk,
         "<h2>Sur les trois météos</h2>", "".join(tb),
         "<p class='petit'>« Optimum a posteriori » = meilleur placement possible en connaissant tout l'hiver d'avance (borne haute). "
         "« Étalé chaque jour » = mêmes bûches réparties selon les degrés-jours, sans viser les fenêtres (4 h sur 24 de leur chaleur tombe dans une fenêtre). "
         "Les bûches non brûlées au 31 mars restent pour l'hiver suivant.</p>"]
    plan_parts = ["".join(h)]

    mois = {}
    for a in cen:
        m = mois.setdefault(a["date_2026_2027"][:7], {"n": 0, "feu": 0, "b": 0, "evt": 0, "kwh": 0, "val": 0, "prime": 0, "dj": 0, "t": [], "fin": 0})
        m["n"] += 1; m["feu"] += a["buches"] > 0; m["b"] += a["buches"]; m["evt"] += a["evenements"]; m["kwh"] += a["kwh_evites"]
        m["val"] += a["val"]; m["prime"] += a["valeur_pointe"]; m["dj"] += a["dj18"]; m["t"].append(a["t_moy"]); m["fin"] = a["stock_restant"]
    noms = {"2026-11": "novembre 2026", "2026-12": "décembre 2026", "2027-01": "janvier 2027", "2027-02": "février 2027", "2027-03": "mars 2027"}
    g_m = svg.series([noms[k] for k in mois], [
        {"nom": "Bûches brûlées", "valeurs": [round(m["b"]) for m in mois.values()], "couleur": svg.COUL["buche"], "type": "bar"},
        {"nom": "Stock en fin de mois", "valeurs": [round(m["fin"]) for m in mois.values()], "couleur": "reel", "type": "bar"},
        {"nom": "Valeur ($, axe droit)", "valeurs": [round(m["val"]) for m in mois.values()], "couleur": svg.COUL["vert"], "axe": "d"}], titre_g="bûches", titre_d="$", h=280, w=900)
    tm = ("<table><tr><th>Mois</th><th>Jours</th><th>T moy.</th><th>Degrés-jours</th><th>Événements</th><th>Jours de feu</th><th>Bûches</th><th>Stock fin de mois</th><th>kWh évités</th><th>Valeur</th><th>dont prime</th></tr>" +
          "".join(f"<tr><td>{noms[k]}</td><td class=n>{m['n']}</td><td class=n>{nb(sum(m['t']) / len(m['t']), 1)} °C</td><td class=n>{nb(m['dj'])}</td><td class=n>{m['evt']}</td><td class=n>{m['feu']}</td>"
                  f"<td class=n>{nb(m['b'])}</td><td class=n>{nb(m['fin'])}</td><td class=n>{nb(m['kwh'])}</td><td class=n>{argent(m['val'])}</td><td class=n>{argent(m['prime'])}</td></tr>" for k, m in mois.items()) + "</table>")
    plan_parts.append("<h2 id='mensuel'>Par mois</h2>" + "<p class='petit'>Météo " + CENTRAL + f" rejouée sur 2026-2027 (7 nov. → 31 mars), stock ≈ {NB} bûches, règle de budget.</p>" + g_m + tm)

    def coul(j, r):
        if j["evenements"]:
            return "evt"
        return "cal_sansfeu" if not j["buches"] else svg.intensite("buche", 0.35 + 0.65 * r)
    for s in cen:
        s["date"] = dt.date.fromisoformat(s["date_2026_2027"])
    cal = svg.calendrier(cen, lambda j: j["buches"], coul, lambda j: f"{j['date']} : {j['t_moy']} °C, {j['buches']:.0f} bûches, stock {j['stock_restant']:.0f}" + (f", {j['evenements']} événement(s)" if j["evenements"] else ""),
                         lambda j: f"#s-{j['date']}", vmax=10)
    rows = "".join(f"<tr id='s-{s['date']}'{' class=evt' if s['evenements'] else ''}><td>{s['date']}</td><td class=n>{nb(s['t_moy'], 1)}</td><td class=n>{nb(s['dj18'])}</td><td>{E(s['creux'])}{' (cœur)' if s['coeur'] == '1' else ''}</td>"
                   f"<td class=n>{s['evenements'] or ''}</td><td class=n>{nb(s['buches'])} <span class='barre' style='width:{s['buches'] * 4:.0f}px'></span></td><td class=n>{nb(s['stock_restant'])}</td><td class=n>{nb(s['reserve_evt'])}</td>"
                   f"<td class=n>{nb(s['kwh_evites'])}</td><td class=n>{nb(s['kwh_evites_pointe'], 1)}</td><td class=n>{argent(s['val'])}</td></tr>" for s in cen)
    plan_parts.append("<h2 id='jours'>Jour par jour</h2>" +
       "<p>Calendrier : rouge = jour d'événement ; orange = feu prévu ; gris = pas de feu. Météo " + CENTRAL + " rejouée, stock ≈ " + str(NB) + " bûches.</p>" + cal +
       "<div class='defile'><table><tr><th>Jour</th><th>T moy.</th><th>DJ</th><th>Creux</th><th>Évts</th><th>Bûches</th><th>Stock restant</th><th>Réserve évts</th><th>kWh évités</th><th>dont en pointe</th><th>Valeur</th></tr>" + rows + "</table></div>")


    pg("strategie/plan.html", "Plan de saison 2026-2027 (simulation)", "".join(plan_parts))

    page_inventaire(quand, P)


def schema_svg(sections):
    """Schéma simple des formes de face (échelle : 1 pi = 24 px)."""
    k, m = 24, 20
    rect, pente, tri = sections[0], sections[1], sections[2]
    W = m + pente["largeur_pi"] * k + rect["largeur_pi"] * k + m + 40 + 2 * (tri["largeur_pi"] * k + 24) + m
    Hs = m + max(rect["hauteur_pi"], pente["hauteur_pi"]) * k + 70
    sol = m + max(rect["hauteur_pi"], pente["hauteur_pi"]) * k
    x0 = m
    o = [f"<svg class='graphe' viewBox='0 0 {W:.0f} {Hs:.0f}' role='img' aria-label='Schéma de la pile vue de face'>",
         f"<line x1='0' y1='{sol}' x2='{W:.0f}' y2='{sol}' class='axe0'/>"]
    # pente (triangle rectangle : bas à gauche, haut contre le rectangle)
    pw, ph = pente["largeur_pi"] * k, pente["hauteur_pi"] * k
    o.append(f"<polygon points='{x0},{sol} {x0 + pw},{sol} {x0 + pw},{sol - ph}' class='pile pile-pente'/>")
    o.append(f"<text x='{x0 + pw * 0.62:.0f}' y='{sol - 8}' font-size='12' text-anchor='middle'>{pente['buches']}</text>")
    o.append(f"<text x='{x0 + pw / 2:.0f}' y='{sol + 16}' font-size='11' text-anchor='middle'>4 pi</text>")
    o.append(f"<text x='{x0 + pw * 0.35:.0f}' y='{sol - ph * 0.55:.0f}' font-size='11' text-anchor='middle' class='pile-note'>45°</text>")
    # rectangle
    rx, rw, rh = x0 + pw, rect["largeur_pi"] * k, rect["hauteur_pi"] * k
    o.append(f"<rect x='{rx}' y='{sol - rh}' width='{rw}' height='{rh}' class='pile pile-rect'/>")
    o.append(f"<text x='{rx + rw / 2:.0f}' y='{sol - rh / 2 + 5:.0f}' font-size='15' font-weight='700' text-anchor='middle'>Rectangle principal : {rect['buches']} bûches</text>")
    o.append(f"<text x='{rx + rw / 2:.0f}' y='{sol + 16}' font-size='11' text-anchor='middle'>22 pi</text>")
    o.append(f"<text x='{rx + rw + 6:.0f}' y='{sol - rh / 2:.0f}' font-size='11'>4 pi 8 po</text>")
    # deux triangles isocèles
    tx = rx + rw + 70
    for i in range(tri["nombre"]):
        bw, bh = tri["largeur_pi"] * k, tri["hauteur_pi"] * k
        o.append(f"<polygon points='{tx},{sol} {tx + bw},{sol} {tx + bw / 2},{sol - bh}' class='pile pile-tri'/>")
        o.append(f"<text x='{tx + bw / 2:.0f}' y='{sol - 10}' font-size='12' text-anchor='middle'>{round(tri['buches'] / tri['nombre'])}</text>")
        o.append(f"<text x='{tx + bw / 2:.0f}' y='{sol + 16}' font-size='11' text-anchor='middle'>6 pi</text>")
        o.append(f"<text x='{tx + bw / 2:.0f}' y='{sol - bh - 5:.0f}' font-size='11' text-anchor='middle'>3 pi 4 po</text>")
        tx += bw + 24
    o.append(f"<text x='{m}' y='{Hs - 14:.0f}' font-size='11' class='ax'>Vue de face, à l'échelle (1 pi = {k} px). Profondeur : une seule rangée de bûches de 16 po (confirmé). "
             "Triangles à 45° ; leur position est schématique.</text>")
    o.append("</svg>")
    return "".join(o)


def texte_inventaire(I, NB_ancien):
    p = I["param"]; S = I["sections"]
    f = lambda x, d=2: f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    L = ["# Inventaire de la pile de bois : estimation du 22 novembre 2026", "",
         "Source : mesures prises par Marc, son croquis (approximatif ; formes du bas = triangles à 45°) et sa séance de calcul (22 nov. 2026). Rédigé par le projet bois-chauffage.", "",
         "Croquis : rectangle de 22 pi (repères 12 pi + 10 pi), hauteur moyenne 4 pi 8 po, corde d'étalonnage à peu près au milieu ; à gauche 4 pi en pente à 45° ; en bas « x2 » : 6 pi de base, 3 pi 4 po au sommet.", "",
         "## Résultat", "",
         f"- Estimation centrale : **{I['buches']} bûches** (calcul exact {f(I['buches_exact'], 1)} ; la session arrondit à 875-880).",
         f"- Surface de face totale : {f(I['surface'])} pi².",
         f"- Fourchette retenue : {p['fourchette_retenue'][0]} à {p['fourchette_retenue'][1]} bûches. Une seule rangée en profondeur, confirmée par Marc ; la densité reste tirée d'un seul échantillon.",
         f"- En cordes : {f(I['cordes_face'], 1)} cordes de face (4 × 8 pi = 32 pi², bûches de 16 po) ; {f(I['cordes_232'], 1)} cordes au ratio du projet ({p['buches_par_corde']} bûches/corde).",
         f"- Remplace la 1re estimation du même jour : environ 1,5 corde, soit {NB_ancien} bûches.", "",
         "## Méthode", "",
         f"On mesure la face de la pile (largeur × hauteur), on la découpe en formes simples, puis on multiplie la surface par une densité de {f(p['densite'], 1)} bûches par pi² de face.",
         "La densité vient d'une corde d'étalonnage située à peu près au milieu du rectangle principal (croquis de Marc) : un seul échantillon, À CONFIRMER par d'autres comptages.", "",
         "## Détail des calculs", ""]
    for i, s in enumerate(S, 1):
        if s["forme"] == "rectangle":
            calc = f"{f(s['largeur_pi'], 0)} pi × {f(s['hauteur_pi'])} pi = {f(s['surface'])} pi²"
        else:
            calc = f"{f(s['largeur_pi'], 0)} pi × {f(s['hauteur_pi'])} pi ÷ 2 = {f(s['surface_unitaire'])} pi²" + (f" ; × {s['nombre']} = {f(s['surface'])} pi²" if s["nombre"] > 1 else "")
        L += [f"{i}. {s['section']} ({s['nombre']} × {s['forme']})", f"   - Hypothèse : {s['hypothese_forme']}.", f"   - Surface : {calc}.",
              f"   - Bûches : {f(s['surface'])} × {f(p['densite'], 1)} = {f(s['surface'] * p['densite'], 1)}, soit {s['buches']}.", ""]
    L += ["| Section | Surface (pi²) | Bûches |", "|---|---:|---:|"] + [f"| {s['section']} | {f(s['surface'])} | {s['buches']} |" for s in S] + \
         [f"| **Total** | **{f(I['surface'])}** | **{I['buches']}** |", "",
          f"Note : dans la session, un tableau intermédiaire affichait {f(I['intermediaire_surface'])} pi² et {I['intermediaire_buches']} bûches : c'était le total avant l'ajout des deux triangles.", "",
          "## Vérification de plausibilité (corde québécoise)", "",
          f"- Une corde de face (corde québécoise) mesure 4 pi × 8 pi de face = 32 pi², avec des bûches de 16 po (longueur CONFIRMÉE par Marc). C'est 1/3 d'une corde pleine (4 × 4 × 8 = 128 pi³).",
          f"- {f(I['surface'])} pi² ÷ 32 = {f(I['cordes_face'], 2)} cordes de face.",
          f"- {f(p['densite'], 1)} bûches/pi² × 32 = {f(I['buches_par_corde_implicite'], 0)} bûches par corde, contre {p['buches_par_corde']} dans le projet (2023-24).",
          f"- À {p['buches_par_corde']} bûches/corde : {p['buches_par_corde']} ÷ 32 = {f(I['densite_232'])} bûches/pi², soit {I['buches_selon_232']} bûches.",
          f"- Diamètre implicite : 144 po² ÷ {f(p['densite'], 1)} = {f(I['po2_par_buche'], 1)} po² de face par bûche, vides compris, soit un carré de ≈ {f(I['cote_po'], 1)} po de côté : plausible pour des bûches fendues.",
          "- Écart expliqué par Marc : 4,1 cordes, c'est presque l'achat complet de 2023-24 ; il avait arrêté le chauffage au bois pendant une longue période l'hiver dernier et brûlé en priorité le bois de ses propres arbres abattus.", "",
          "## Limites et incertitudes", "",
          "- Profondeur : UNE seule rangée de bûches de 16 po, confirmée par Marc (la structure triangulaire du bas existe bien en deux exemplaires).",
          "- Longueur des bûches : 16 po, confirmée par Marc le 22 nov. 2026.",
          "- Densité tirée d'un seul échantillon (corde d'étalonnage au milieu du rectangle) ; diamètre des bûches variable ; tassement et vides (bûches croisées aux extrémités, trous).",
          "- Formes simplifiées (croquis approximatif) : pente du début à 45° ; formes du bas = triangles à 45° (confirmé par Marc) ; la hauteur mesurée (3 pi 4 po) a été retenue, alors que des côtés à 45° exacts donneraient 3 pi "
          f"({I['triangle_45_buches']} bûches au lieu de {S[2]['buches']}).", "",
          "## Fourchettes", "",
          f"- Fourchette retenue (sensibilité à la densité) : 6,7 bûches/pi² → {I['buches']} ; 7,25 (ratio du projet, 232/corde) → {I['buches_selon_232']}.",
          f"- Tests plus larges (non retenus) : 6,0 → {I['buches_bas']} ; 7,4 → {I['buches_haut']} ; ±15 % → {I['moins15']} à {I['plus15']}.",
          f"- Fourchette retenue pour le protocole : {p['fourchette_retenue'][0]} à {p['fourchette_retenue'][1]} (central {I['buches']}) ; seule la densité reste incertaine.", ""]
    return "\n".join(L)


def page_inventaire(quand, P):
    from calculs import inventaire
    I = inventaire.calculer(); p = I["param"]; S = I["sections"]; H = P["hypotheses"]
    sous = f"<p class='sous'>Mesures de Marc du {dfr(p['date'])} 2026 · généré le {E(quand)} par <code>outils/generer_site.py</code> à partir de <code>data/inventaire_pile_2026-11.csv</code>.</p>"
    md = texte_inventaire(I, H["stock_ancien"])
    with open(os.path.join(OUT, "inventaire-pile-2026-11.md"), "w", encoding="utf-8") as fo:
        fo.write(md)
    f2 = lambda x: nb(x, 2)
    det = []
    for s in S:
        if s["forme"] == "rectangle":
            c = f"{nb(s['largeur_pi'])} × {f2(s['hauteur_pi'])} = {f2(s['surface'])} pi²"
        else:
            c = f"{nb(s['largeur_pi'])} × {f2(s['hauteur_pi'])} ÷ 2 = {f2(s['surface_unitaire'])} pi²" + (f" ; × {s['nombre']} = {f2(s['surface'])} pi²" if s["nombre"] > 1 else "")
        det.append(f"<tr><td><b>{E(s['section'])}</b></td><td>{E(s['hypothese_forme'])}</td><td>{c}</td><td class=n>{f2(s['surface'])} × {nb(p['densite'], 1)} = {nb(s['surface'] * p['densite'], 1)}</td><td class=n><b>{s['buches']}</b></td></tr>")
    sens = [("6,0 (test large, non retenu)", 6.0, I["buches_bas"]), ("<b>6,7 (étalonnage de Marc) : central</b>", 6.7, I["buches"]), ("<b>7,25 (232 bûches/corde du projet) : haut de fourchette</b>", 7.25, I["buches_selon_232"]), ("7,4 (test large, non retenu)", 7.4, I["buches_haut"])]
    h = ["<div class='info'><b>Hypothèses confirmées par Marc</b> : <b>une seule rangée</b> en profondeur, deux structures triangulaires au bas. Reste incertaine : la densité de 6,7 bûches/pi², tirée d'une seule corde d'étalonnage. "
         "Longueur des bûches : <b>16 po, confirmée</b> par Marc le 22 nov. 2026.</div>",
         "<div class='cartes'>", carte(f"≈ {I['buches']}", "bûches (central)", "prov", sous=f"fourchette {p['fourchette_retenue'][0]}–{p['fourchette_retenue'][1]}"),
         carte(f"{f2(I['surface'])} pi²", "surface de face", "neutre", sous="3 formes, 4 morceaux"),
         carte(nb(I["cordes_face"], 1), "cordes de face (4 × 8 pi)", "neutre", sous=f"{nb(I['cordes_232'], 1)} cordes à {p['buches_par_corde']} bûches/corde"),
         carte(f"{H['stock_ancien']} → {I['buches']}", "stock de départ du protocole", "ko", "protocole.html#revision", "révision du 22 nov. 2026"),
         carte(nb(p["densite"], 1), "bûches par pi² de face", "prov", sous="1 corde d'étalonnage, au milieu du rectangle"), "</div>",
         "<h2>Croquis de Marc</h2>" + ("<figure><img class='croquis' src='img/croquis-pile.png' alt='Croquis de la pile par Marc'>"
          "<figcaption class='petit'>Croquis approximatif ; formes du bas = triangles à 45° (confirmé par Marc). Rectangle de 22 pi (repères 12 pi + 10 pi), hauteur moyenne 4 pi 8 po ; "
          "corde d'étalonnage à peu près au milieu ; à gauche, 4 pi en pente à 45° ; en bas, « x2 » : 6 pi de base, 3 pi 4 po au sommet.</figcaption></figure>"
          if os.path.exists(os.path.join(OUT, "img", "croquis-pile.png")) else "<div class='alerte'>Croquis de Marc à ajouter : <code>rapports/img/croquis-pile.png</code> (croquis approximatif ; formes du bas = triangles à 45°).</div>"),
         "<h2>Schéma de la pile (vue de face, à l'échelle)</h2>", schema_svg(S),
         "<h2>Méthode</h2><p>On mesure la <b>face</b> de la pile (largeur × hauteur), on la découpe en formes simples (un rectangle, un triangle en pente, deux triangles isocèles), "
         f"puis on multiplie chaque surface par une <b>densité de face</b> de {nb(p['densite'], 1)} bûches par pi², étalonnée sur une corde de bois située à peu près au milieu du rectangle principal (croquis de Marc, séance de calcul). "
         "La pile ne compte qu'une seule rangée de bûches en profondeur (confirmé par Marc).</p>",
         "<h2>Mesures, hypothèses et calculs</h2><table><tr><th>Section</th><th>Mesures et hypothèse de forme</th><th>Surface</th><th>× densité</th><th>Bûches</th></tr>" + "".join(det) +
         f"<tr class=tot><td>Total</td><td></td><td class=n><b>{f2(I['surface'])} pi²</b></td><td class=n>{nb(I['buches_exact'], 1)}</td><td class=n><b>{I['buches']}</b></td></tr></table>"
         f"<p class='petit'>Le total {I['buches']} est la somme des sections arrondies, comme dans la session ; le calcul exact donne {nb(I['buches_exact'], 1)} (la session dit « 875 à 880 »). "
         f"Dans la session, un tableau intermédiaire affichait {f2(I['intermediaire_surface'])} pi² et {I['intermediaire_buches']} bûches : c'était le total <i>avant</i> l'ajout des deux triangles ; le total final est {f2(I['surface'])} pi². "
         f"Formes du bas : triangles à 45° (confirmé par Marc ; le croquis est approximatif). Avec des côtés à 45° exacts, une base de 6 pi donnerait 3 pi de haut ({I['triangle_45_buches']} bûches pour les deux au lieu de {S[2]['buches']}) ; c'est la hauteur mesurée, 3 pi 4 po, qui a été retenue. "
         "Pente du début : 45°, à la même hauteur que le rectangle sur le croquis ; on garde le triangle de 4 × 4 ÷ 2 = 8 pi² de la session (hypothèse prudente).</p>",
         "<h2 id='plausibilite'>Vérification de plausibilité (corde québécoise)</h2><table><tr><th>Contrôle</th><th>Calcul</th><th>Résultat</th></tr>"
         f"<tr><td>Corde de face (corde québécoise)</td><td>4 pi × 8 pi de face, bûches de 16 po ; 1/3 de la corde pleine (4 × 4 × 8 = {nb(p['corde_pleine_pi3'])} pi³)</td><td class=n>{nb(p['corde_face_pi2'])} pi² de face</td></tr>"
         f"<tr><td>Cordes dans la pile</td><td>{f2(I['surface'])} ÷ {nb(p['corde_face_pi2'])}</td><td class=n><b>{f2(I['cordes_face'])} cordes</b></td></tr>"
         f"<tr><td>Bûches par corde implicites</td><td>{nb(p['densite'], 1)} × {nb(p['corde_face_pi2'])}</td><td class=n>{nb(I['buches_par_corde_implicite'])} (projet : {p['buches_par_corde']})</td></tr>"
         f"<tr><td>Densité qui correspond à {p['buches_par_corde']} bûches/corde</td><td>{p['buches_par_corde']} ÷ {nb(p['corde_face_pi2'])}</td><td class=n>{f2(I['densite_232'])} bûches/pi² → {I['buches_selon_232']} bûches</td></tr>"
         f"<tr><td>Diamètre implicite d'une bûche</td><td>144 po² ÷ {nb(p['densite'], 1)} = {nb(I['po2_par_buche'], 1)} po² de face par bûche, vides compris</td><td class=n>≈ {nb(I['cote_po'], 1)} po (carré équivalent)</td></tr>"
         f"<tr><td>Volume apparent</td><td>{f2(I['surface'])} pi² × 16 po (1,33 pi)</td><td class=n>{nb(I['volume_pi3'])} pi³ ≈ {nb(I['volume_pi3'] / p['corde_pleine_pi3'], 2)} corde pleine</td></tr></table>"
         "<div class='info'><b>Verdict</b> : les calculs sont cohérents avec la définition d'une corde québécoise. 6,7 bûches/pi² donne 214 bûches par corde, un peu sous les 232 du projet ; "
         "un diamètre implicite d'environ 4,5 po (vides compris) est plausible pour des bûches fendues. L'hypothèse critique est <b>une seule rangée de bûches de 16 po</b> : "
         "la longueur et la rangée unique sont toutes deux confirmées par Marc. "
         "<b>Écart expliqué</b> : 4,1 cordes, c'est presque l'achat complet de 2023-24, alors qu'on supposait qu'il en restait environ 1,5. "
         "Marc l'explique : il avait arrêté le chauffage au bois pendant une longue période l'hiver dernier et brûlé en priorité le bois de ses propres arbres abattus. Point résolu.</div>",
         "<h2 id='fourchette'>Fourchette</h2><table><tr><th>Densité (bûches/pi²)</th><th>Calcul</th><th>Bûches</th><th>Cordes (232)</th></tr>" +
         "".join(f"<tr{' class=tot' if d == 6.7 else ''}><td>{lib}</td><td>{f2(I['surface'])} × {nb(d, 2)}</td><td class=n>{b}</td><td class=n>{nb(b / p['buches_par_corde'], 1)}</td></tr>" for lib, d, b in sens) +
         f"<tr><td>±15 % autour du central</td><td>{I['buches']} × 0,85 / × 1,15</td><td class=n>{I['moins15']} à {I['plus15']}</td><td class=n>{nb(I['moins15'] / 232, 1)} à {nb(I['plus15'] / 232, 1)}</td></tr></table>"
         f"<p><b>Retenu pour le protocole</b> : central <b>{I['buches']}</b>, fourchette <b>{p['fourchette_retenue'][0]} à {p['fourchette_retenue'][1]}</b> (densité de 6,7 à 7,25 bûches/pi² : de l'étalonnage de Marc à celle qui correspond aux 232 bûches/corde du projet), "
         f"seule la densité reste incertaine. La simulation teste aussi {I['buches_bas']} et {I['buches_haut']} : tous les événements restent couverts (<a href='protocole.html#revision'>détail</a>).</p>",
         "<h2>Limites</h2><ul>"
         "<li><b>Profondeur</b> : une seule rangée de bûches de 16 po, <b>confirmée par Marc</b>.</li>"
         "<li><b>Densité</b> : un seul échantillon (la corde d'étalonnage au milieu du rectangle) ; elle varie avec le diamètre des bûches et le soin de l'empilage d'un bout à l'autre de la pile.</li>"
         "<li><b>Tassement et vides</b> : extrémités croisées, trous, bûches tordues ; la face ne montre pas l'intérieur.</li>"
         "<li><b>Formes</b> (croquis approximatif) : pente du début à 45° ; formes du bas = triangles à 45° (confirmé par Marc), avec la hauteur mesurée (3 pi 4 po) plutôt que la géométrie à 45° exacts (3 pi).</li>"
         "<li><b>Énergie</b> : le nombre de bûches ne dit pas les kWh ; le projet utilise ≈ " + nb(P["kwh_par_buche"], 1) + " kWh évités par bûche (régression 2023-24).</li></ul>",
         "<h2>Pour affiner</h2><ol><li>Compter les bûches dans un carré de 2 pi × 2 pi à deux ou trois endroits de la face (densité réelle).</li>"
         "<li>Inscrire tout vrai recomptage dans la colonne <code>stock_compte</code> de la saisie ; l'inventaire reste le paramètre de départ daté.</li></ol>",
         "<h2>Fichiers</h2><ul><li>Texte téléchargeable : <a href='inventaire-pile-2026-11.md' download>inventaire-pile-2026-11.md</a> (document de calcul de l'inventaire).</li>"
         "<li>Données : <code>data/inventaire_pile_2026-11.csv</code> (mesures en pouces) ; calcul : <code>outils/calculs/inventaire.py</code>.</li></ul>"]
    page("inventaire.html", "Inventaire de la pile de bois (22 nov. 2026)", "".join(h), quand, sous=sous, contexte="Stratégie · saison 2026-2027")

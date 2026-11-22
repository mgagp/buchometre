#!/usr/bin/env python3
"""Pages « Protocole hiver 2026-2027 » (appelé par generer_site.py ; lit data/protocole*.csv/json et la saisie)."""
import csv, json, os, html, datetime as dt
import svg
from generer_site import page, carte, argent, nb, pct, RACINE, OUT, MOIS

E = html.escape
CENTRAL = "2024-2025"  # météo d'hiver « type » (degrés-jours médians des 3 hivers)
MOIS_FR = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
SOURCES = [
    ("Hydro-Québec, Tarifs d'électricité en vigueur le 1er avril 2026, sections 8 (crédit hivernal) et 9 (Flex D)", "https://www.hydroquebec.com/data/documents-donnees/pdf/tarifs-electricite.pdf"),
    ("Hydro-Québec, page Tarif Flex D", "https://www.hydroquebec.com/residentiel/espace-clients/tarifs/tarif-flex-d.html"),
    ("Hydro-Québec, Grille des tarifs 2026 (hausse au 1er avril 2026)", "https://www.hydroquebec.com/data/documents-donnees/pdf/grille-tarifaire.pdf"),
    ("Hydro-Québec, données ouvertes « Événements de pointe – saison hivernale » (TPC-DPC = Flex D, CPC-D = crédit hivernal)", "https://donnees.hydroquebec.com/explore/dataset/evenements-pointe/"),
    ("Hydro-Québec, Historique des résultats (bilan par hiver)", "https://www.hydroquebec.com/residentiel/mieux-consommer/pourquoi-mieux-consommer/bilan-efforts-collectifs/historique-resultats.html"),
    ("Open-Meteo, API d'archives historiques (réanalyse ERA5), point 45,40 N / −74,03 O (Vaudreuil-Dorion)", "https://open-meteo.com/en/docs/historical-weather-api"),
]
SOUSNAV = [("protocole.html", "1. Positionnement"), ("protocole-meteo.html", "2. Étude météo"), ("protocole-sim.html", "3. Simulation : sommaire"),
           ("protocole-sim-mensuel.html", "mensuel"), ("protocole-sim-jours.html", "jour par jour"), ("protocole-saisie.html", "4. Saisie et suivi")]


def lire(rel):
    with open(os.path.join(RACINE, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sousnav(nom):
    return ("<div class='info' style='padding:6px 10px'><b>Protocole hiver 2026-2027</b> : " +
            " · ".join(f"<a href='{u}'{' style=font-weight:700' if u == nom else ''}>{E(t)}</a>" for u, t in SOUSNAV) + "</div>")


def dfr(s):
    d = dt.date.fromisoformat(s) if isinstance(s, str) else s
    return f"{d.day} {MOIS_FR[d.month]}"


def main(quand):
    P = json.load(open(os.path.join(RACINE, "data/protocole.json"), encoding="utf-8"))
    H = P["hypotheses"]; F = H["flex_D_2026"]; TD = H["tarif_D_2026"]; kb = P["kwh_par_buche"]
    V = P["valeur_buche"]; SE = P["seuils"]; C = P["critique"]; SC = P["stats_creux"]; R = P["resume_sim"]
    MJ = lire("data/protocole_meteo_jours.csv"); CR = lire("data/protocole_creux.csv"); SIM = lire("data/protocole_simulation.csv")
    SA = lire("data/saisie_2026-2027_enrichie.csv")
    sous = (f"<p class='sous'>Généré le {E(quand)} par <code>outils/generer_site.py</code> (pages protocole : <code>outils/generer_protocole.py</code>). "
            f"Sources consultées le 2026-11-22 ; météo Open-Meteo jusqu'au {E(P['meteo_derniere_date'])}.</p>")
    complets = ["2023-2024", "2024-2025", "2025-2026"]
    n_creux = [SC[h]["n"] for h in complets]
    cible_val = [R[h]["strategies"]["cible"]["valeur"] for h in complets]
    quot_val = [R[h]["strategies"]["quotidien"]["valeur"] for h in complets]
    evh = P["evts_par_hiver"]

    def pg(nom, titre, corps):
        page(nom, titre, sousnav(nom) + corps, quand, sous=sous)

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
    bpe = SK["buches_par_evt_typ"]
    h = ["<div class='cartes'>",
         carte(f"≈ {NB}", "bûches en stock (≈ 1,5 corde)", "prov", "#bois", f"{H['cordes_restantes']} × {H['buches_par_corde']} bûches/corde (hypothèse fragile)"),
         carte(f"{min(r['jours_feu'] for r in rg):.0f}–{max(r['jours_feu'] for r in rg):.0f}", "jours de feu que le stock permet", "neutre", "protocole-sim.html", "selon la météo des 3 hivers"),
         carte(f"{argent(min(r['valeur'] for r in rg), 0)}–{argent(max(r['valeur'] for r in rg), 0)}", "valeur évitée cet hiver (règle)", "ok", "protocole-sim.html",
               f"optimum a posteriori {argent(min(r['valeur'] for r in op), 0)}–{argent(max(r['valeur'] for r in op), 0)} ; feu chaque jour {argent(min(r['valeur'] for r in qd), 0)}–{argent(max(r['valeur'] for r in qd), 0)}"),
         carte("100 %", "événements Flex D couverts", "ok", "protocole-sim.html", f"{min(r['evt'] for r in rg):.0f} à {max(r['evt'] for r in rg):.0f} événements selon l'hiver"),
         carte(f"{bpe[0]}–{bpe[-1]}", "bûches par événement", "neutre", "#regles", "allumer 30-60 min avant 6 h ou 16 h"),
         carte(f"+{argent(min(marg), 0)}", "valeur d'une corde de plus", "ko", "#appoint", f"pour ≈ {argent(H['prix_corde_remplacement'], 0)} : achat d'appoint non rentable"),
         "</div>"]
    h.append("<h2>En bref</h2><div class='info'><ol>"
             "<li><b>La situation</b> : tu es au <b>tarif Flex D</b> (confirmé le 22 nov. 2026) et tu n'as pas acheté de bois : il reste ≈ 1,5 corde, soit ≈ " + str(NB) + " bûches. "
             "Ce bois est déjà payé : la question n'est plus « le bois est-il rentable ? » mais <b>« où placer ces " + str(NB) + " bûches pour éviter le plus d'électricité possible cet hiver ? »</b></li>"
             f"<li><b>Pourquoi les événements d'abord</b> : hors événement, un kWh évité vaut {nb(F['p2_hiver'] * 100, 3)} ¢ ; pendant un événement (6 h–10 h ou 16 h–20 h, annoncé la veille), "
             f"il vaut {nb(F['pointe'] * 100, 3)} ¢, cinq fois plus. Une bûche brûlée un jour ordinaire vaut {argent(V['flex_hors_evt'])} ; sa chaleur livrée pendant un événement vaut jusqu'à {argent(V['flex_evt'])}.</li>"
             f"<li><b>Ensuite les jours cœur des creux froids</b> : le modèle 2023-24 (kWh = {nb(P['coef'][0], 1)} + {nb(P['coef'][1], 2)} × degrés-jours − {nb(kb, 2)} × bûches) "
             "donne le même gain par bûche quel que soit le froid. Viser les jours froids sert à être prêt pour les grappes d'événements (presque toujours par grand froid) "
             "et à brûler quand la maison peut absorber la chaleur (≈ 0,45 bûche par degré-jour au plus).</li>"
             f"<li><b>Résultat</b> : en suivant la règle de budget ci-dessous, le stock couvre <b>tous les événements</b> et ≈ {min(r['jours_feu'] for r in rg):.0f} à {max(r['jours_feu'] for r in rg):.0f} jours de feu, "
             f"pour ≈ {argent(min(r['valeur'] for r in rg), 0)} à {argent(max(r['valeur'] for r in rg), 0)} d'électricité évitée (taxes incl.), contre {argent(min(r['valeur'] for r in qd), 0)} à "
             f"{argent(max(r['valeur'] for r in qd), 0)} si on étalait le même bois sur chaque jour.</li></ol></div>")
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
             f"<p class='petit'>Valeur = {nb(kb, 2)} kWh/bûche × prix × 1,14975 (TPS+TVQ). Pendant un événement, on suppose qu'une bûche allumée juste avant livre {pct(H['part_buche_dans_fenetre'])} "
             f"de sa chaleur dans la fenêtre, et que le besoin de chauffage dans la fenêtre est plafonné (≈ {nb(H['facteur_pointe_horaire'], 2)} × la moyenne horaire du jour) : "
             f"d'où {bpe[0]} à {bpe[-1]} bûches par événement (−6 °C à −18 °C).</p>")
    h.append("<h2 id='bois'>Le stock de bois</h2><ul>"
             f"<li><b>Stock</b> : ≈ {H['cordes_restantes']} corde (estimation de Marc) × {H['buches_par_corde']} bûches/corde = <b>≈ {NB} bûches</b>.</li>"
             f"<li><b>D'où vient 232 bûches/corde</b> : 928 bûches projetées pour 2023-24 ÷ 4 cordes. C'est fragile : le 928 est lui-même une projection (649 bûches mesurées jusqu'au 16 févr.), "
             "les 4 cordes ne sont pas écrites dans le chiffrier, et la taille des bûches varie. Une erreur de ±25 % est plausible (≈ 260 à 435 bûches). "
             "<b>Le plus simple : compter le tas une fois</b> (ou une rangée) et corriger le stock dans la saisie.</li>"
             "<li><b>Coût</b> : déjà payé (coût irrécupérable) ; il n'entre pas dans la décision de brûler. "
             f"Repère secondaire : valeur de remplacement ≈ {argent(H['prix_corde_remplacement'])} la corde (425 $ ÷ 4 + 25 $), soit ≈ {argent(SK['valeur_remplacement'], 0)} pour le stock.</li></ul>")
    h.append("<h2 id='regles'>La règle de budget</h2><ol>"
             f"<li><b>Événement annoncé (avis la veille avant 15 h) : toujours.</b> Allumer 30 à 60 min avant 6 h ou 16 h et entretenir jusqu'à 10 h ou 20 h : "
             f"<b>{bpe[0]} bûches</b> par événement (5 sous −12 °C), le double si matin et soir. On peut puiser dans la réserve.</li>"
             f"<li><b>Réserve pour les événements</b> : garder {H['regle_buches_evt']} bûches par événement encore attendu "
             f"(≈ {H['evts_attendus']} par hiver, surtout en janvier). En pratique : ≈ {res_j['1er déc.']} bûches au 1er déc., ≈ {res_j['1er janv.']} au 1er janv., "
             f"≈ {res_j['1er févr.']} au 1er févr., ≈ {res_j['1er mars']} au 1er mars.</li>"
             f"<li><b>Jour cœur d'un creux froid</b> (prévision : T moyenne ≤ {nb(H['regle_seuil_coeur'])} °C et nettement sous la normale) : feu de soirée, jusqu'à <b>{H['regle_max_coeur']} bûches</b>, "
             "seulement si le stock après le feu reste au-dessus de la réserve.</li>"
             f"<li><b>À partir du 1er février</b> : le surplus au-dessus de la réserve peut aller à tout jour froid (≤ 0 °C), toujours {H['regle_max_coeur']} bûches au plus ; "
             "le stock qui reste en avril n'est pas perdu (il sert l'hiver suivant).</li>"
             "<li><b>Si le stock baisse plus vite que prévu</b> (plus de 50 bûches sous le jalon du mois, ou recomptage plus bas) : suspendre les feux de jours cœur, "
             "ne garder que les événements jusqu'à revenir sur la courbe. S'il baisse moins vite (hiver doux), ne pas « rattraper » avant février.</li>"
             "<li><b>Jour témoin</b> : environ un jour froid par mois sans feu (et sans événement), noté « témoin ».</li>"
             "<li><b>Saisie</b> chaque jour, même sans feu, dans <code>data/saisie_2026-2027.csv</code> ; la page Saisie suit le stock restant contre le plan.</li></ol>"
             "<table><tr><th>Jalon</th><th>Stock prévu (3 météos)</th><th>Réserve événements</th></tr>" +
             "".join(f"<tr><td>{lib}</td><td class=n>{' / '.join(str(x) for x in stk_j[lib])}</td><td class=n>{res_j[lib]}</td></tr>" for lib, _ in jalons) + "</table>"
             "<p class='petit'>Rythme médian simulé : nov. " + nb(rythme["11"]) + " · déc. " + nb(rythme["12"]) + " · janv. " + nb(rythme["01"]) + " · févr. " + nb(rythme["02"]) + " · mars " + nb(rythme["03"]) +
             " bûches (février reçoit le surplus libéré). Ordre des météos : 2023-24 / 2024-25 / 2025-26.</p>")
    h.append("<h2 id='appoint'>Un achat d'appoint vaut-il la peine ?</h2>"
             f"<p>Une corde de plus (≈ {H['buches_par_corde']} bûches) ajoute ≈ <b>{argent(min(marg), 0)}</b> de valeur évitée même placée au mieux "
             f"({' / '.join(argent(x, 0) for x in marg_r)} avec la règle selon la météo), pour un coût ≈ {argent(H['prix_corde_remplacement'], 0)}. "
             "Le stock actuel couvre déjà tous les événements : chaque bûche de plus irait à un jour ordinaire, à "
             f"{argent(V['flex_hors_evt'])} pièce, sous son coût de remplacement (≈ {argent(H['prix_corde_remplacement'] / H['buches_par_corde'])}). "
             "<b>Pas rentable</b>, sauf si le recomptage montre nettement moins de bûches (moins de ≈ 150 : la réserve d'événements serait menacée) "
             "ou si le prix de la corde baisse sous ≈ 110 $.</p>")
    h.append("<h2>Sources</h2><ul>" + "".join(f"<li><a href='{u}'>{E(t)}</a></li>" for t, u in SOURCES) +
             "</ul><p class='petit'>Consultées le 22 novembre 2026. Les données ouvertes d'Hydro-Québec sont « brutes, sans garantie » ; l'avis officiel par courriel a priorité.</p>")
    pg("protocole.html", "Protocole hiver 2026-2027 : positionnement", "".join(h))


    # ======================= 2. Étude météo =======================
    clim = P["climatologie"]
    labs = [dfr(c["date"]) for c in clim]
    i_c0 = next(i for i, c in enumerate(clim) if c["date"] == C["debut"]); i_c1 = next(i for i, c in enumerate(clim) if c["date"] == C["fin"])
    i_m0 = next(i for i, c in enumerate(clim) if c["date"].endswith("11-15")); i_m1 = next(i for i, c in enumerate(clim) if c["date"].endswith("03-15"))
    par_h = {}
    for j in MJ:
        par_h.setdefault(j["hiver"], {})[j["date"][5:]] = float(j["t_moy"])
    ser = [{"nom": f"T moy. {hv}", "valeurs": [par_h.get(hv, {}).get(c["date"][5:]) for c in clim], "couleur": col, "epaisseur": 1, "points": False}
           for hv, col in (("2023-2024", "#b0bec5"), ("2024-2025", "#90caf9"), ("2025-2026", "#ce93d8"))]
    ser.append({"nom": "Moyenne 3 hivers lissée (15 j)", "valeurs": [c["t_lisse"] for c in clim], "couleur": "#000", "epaisseur": 2.5, "points": False})
    if "2026-2027" in par_h:
        ser.append({"nom": "2026-2027 (à ce jour)", "valeurs": [par_h["2026-2027"].get(c["date"][5:]) for c in clim], "couleur": "#c62828", "epaisseur": 2, "points": False})
    g_clim = svg.series(labs, ser, titre_g="°C", h=320, zones=[(i_m0, i_m1, "fenêtre de Marc : 15 nov.–15 mars", "rgba(255,152,0,0.18)", False), (i_c0, i_c1, "période critique", "rgba(33,150,243,0.14)", True)])
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
                zones.append((i, k, f"creux {js[i]['creux']}", "#dbe9ff", False)); i = k + 1
            else:
                i += 1
        g = svg.series([dfr(j["date"]) for j in js], [
            {"nom": "Événements Flex D (axe droit)", "valeurs": [int(j["evenements_flexd"]) or None for j in js], "couleur": "#c62828", "type": "bar", "axe": "d", "opacite": 0.8},
            {"nom": "T moy. du jour", "valeurs": [float(j["t_moy"]) for j in js], "couleur": "#90a4ae", "epaisseur": 1, "points": False},
            {"nom": "T lissée 3 j", "valeurs": [float(j["t_lisse_3j"]) for j in js], "couleur": "#1565c0", "points": False},
            {"nom": "Normale récente (médiane 31 j)", "valeurs": [float(j["mediane_31j"]) for j in js], "couleur": "#000", "pointille": True, "epaisseur": 1.2, "points": False},
            {"nom": "Jours cœur", "valeurs": [float(j["t_moy"]) if j["coeur"] == "1" else None for j in js], "couleur": "#0d47a1", "type": "bar", "opacite": 0.35},
        ], titre_g="°C", titre_d="évts", zones=zones, h=280)
        h.append(f"<h3>Hiver {hv}{' (en cours)' if hv == '2026-2027' else ''}</h3>" + g)
    h.append("<details><summary>Liste de tous les creux</summary><table><tr><th>Creux</th><th>Du</th><th>Au</th><th>Jours</th><th>Jours cœur</th><th>Jour le plus froid</th><th>T moy. du creux</th><th>Degrés-jours</th><th>Événements Flex D</th><th>Période critique</th></tr>" +
             "".join(f"<tr><td>{c['id']}</td><td>{c['debut']}</td><td>{c['fin']}</td><td class=n>{c['jours']}</td><td class=n>{c['jours_coeur']}</td><td>{c['date_min']} ({nb(float(c['t_min_jour']), 1)} °C)</td>"
                     f"<td class=n>{nb(float(c['t_moy']), 1)} °C</td><td class=n>{nb(float(c['dj']))}</td><td class=n>{c['evt']}</td><td>{'oui' if c['dans_critique'] == 'True' else 'non'}</td></tr>" for c in CR) + "</table></details>")
    # événements
    pr = P["proba_evt"]
    g_p = svg.series([("≤ −15 °C" if p["de"] == -99 else (f"> {p['de']} °C" if p["a"] == 99 else f"{p['de']} à {p['a']} °C")) for p in pr], [
        {"nom": "Probabilité d'un événement Flex D ce jour-là (%)", "valeurs": [round(p["p"] * 100) for p in pr], "couleur": "#c62828", "type": "bar"}], titre_g="%", h=240, w=700)
    h.append("<h2 id='evenements'>(c) Quand tombent les événements de pointe ?</h2>"
             "<p>Historique publié par Hydro-Québec (données ouvertes, offre TPC-DPC = Flex D), croisé avec la température moyenne du jour à Vaudreuil-Dorion, hivers 2024-2025 et 2025-2026 (1er déc.–31 mars) :</p>" + g_p +
             "<table><tr><th>T moy. du jour</th><th>Jours</th><th>Jours avec événement</th><th>Probabilité</th></tr>" +
             "".join(f"<tr><td>{'≤ −15' if p['de'] == -99 else ('> ' + str(p['de'])) if p['a'] == 99 else str(p['de']) + ' à ' + str(p['a'])} °C</td><td class=n>{p['jours']}</td><td class=n>{p['jours_evt']}</td><td class=n>{pct(p['p'])}</td></tr>" for p in pr) + "</table>"
             "<p>Les événements suivent la demande de tout le Québec, pas seulement la température locale : sous −12 °C, un jour sur trois à un sur deux ; entre −12 et −9 °C, un sur quatre ; "
             "au-dessus de −6 °C, presque jamais. Ils arrivent en grappes pendant les coups de froid (souvent matin et soir). Le matin (6 h–10 h) domine. "
             "Pour 2023-2024 (avant les données ouvertes), la simulation suppose un événement les jours ≤ −12 °C.</p>")
    # gain
    I = P["interaction"]
    lignes = [{"nom": f"Météo {hv}", "couleur": col, "pts": P["courbes"][hv]} for hv, col in (("2023-2024", "#90a4ae"), ("2024-2025", "#1565c0"), ("2025-2026", "#8e24aa"))]
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
        {"nom": "Événements (axe droit)", "valeurs": [s["evenements"] * 3 or None for s in cen], "couleur": "#c62828", "type": "bar", "axe": "d", "opacite": 0.9, "sans_legende": True},
        {"nom": "T moy. (°C)", "valeurs": [s["t_moy"] for s in cen], "couleur": svg.COUL["temp"], "points": False, "epaisseur": 1.2},
    ], titre_g="°C", titre_d="bûches", liens=[f"protocole-sim-jours.html#s-{s['date_2026_2027']}" for s in cen], h=300)
    ser_stk = [{"nom": f"Stock restant, météo {hv}", "valeurs": [s["stock_restant"] for s in ss(hv)][:len(cen)], "couleur": col, "points": False, "epaisseur": 2.5 if hv == CENTRAL else 1.3}
               for hv, col in (("2023-2024", "#90a4ae"), ("2024-2025", "#1565c0"), ("2025-2026", "#8e24aa"))]
    ser_stk.append({"nom": "Réserve pour les événements", "valeurs": [s["reserve_evt"] for s in cen], "couleur": "#c62828", "pointille": True, "points": False})
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
    pg("protocole-sim.html", "Simulation 2026-2027 : sommaire (aperçu)", "".join(h))

    mois = {}
    for a in cen:
        m = mois.setdefault(a["date_2026_2027"][:7], {"n": 0, "feu": 0, "b": 0, "evt": 0, "kwh": 0, "val": 0, "prime": 0, "dj": 0, "t": [], "fin": 0})
        m["n"] += 1; m["feu"] += a["buches"] > 0; m["b"] += a["buches"]; m["evt"] += a["evenements"]; m["kwh"] += a["kwh_evites"]
        m["val"] += a["val"]; m["prime"] += a["valeur_pointe"]; m["dj"] += a["dj18"]; m["t"].append(a["t_moy"]); m["fin"] = a["stock_restant"]
    noms = {"2026-11": "novembre 2026", "2026-12": "décembre 2026", "2027-01": "janvier 2027", "2027-02": "février 2027", "2027-03": "mars 2027"}
    g_m = svg.series([noms[k] for k in mois], [
        {"nom": "Bûches brûlées", "valeurs": [round(m["b"]) for m in mois.values()], "couleur": svg.COUL["buche"], "type": "bar"},
        {"nom": "Stock en fin de mois", "valeurs": [round(m["fin"]) for m in mois.values()], "couleur": "#1565c0", "type": "bar"},
        {"nom": "Valeur ($, axe droit)", "valeurs": [round(m["val"]) for m in mois.values()], "couleur": svg.COUL["vert"], "axe": "d"}], titre_g="bûches", titre_d="$", h=280, w=900)
    tm = ("<table><tr><th>Mois</th><th>Jours</th><th>T moy.</th><th>Degrés-jours</th><th>Événements</th><th>Jours de feu</th><th>Bûches</th><th>Stock fin de mois</th><th>kWh évités</th><th>Valeur</th><th>dont prime</th></tr>" +
          "".join(f"<tr><td>{noms[k]}</td><td class=n>{m['n']}</td><td class=n>{nb(sum(m['t']) / len(m['t']), 1)} °C</td><td class=n>{nb(m['dj'])}</td><td class=n>{m['evt']}</td><td class=n>{m['feu']}</td>"
                  f"<td class=n>{nb(m['b'])}</td><td class=n>{nb(m['fin'])}</td><td class=n>{nb(m['kwh'])}</td><td class=n>{argent(m['val'])}</td><td class=n>{argent(m['prime'])}</td></tr>" for k, m in mois.items()) + "</table>")
    pg("protocole-sim-mensuel.html", "Simulation 2026-2027 : mensuel (aperçu)", "<p class='petit'>Météo " + CENTRAL + f" rejouée sur 2026-2027 (7 nov. → 31 mars), stock ≈ {NB} bûches, règle de budget.</p>" + g_m + tm)

    def coul(j, r):
        if j["evenements"]:
            return "#c62828"
        return "#cfd8dc" if not j["buches"] else f"rgba(239,108,0,{0.35 + 0.65 * r:.2f})"
    for s in cen:
        s["date"] = dt.date.fromisoformat(s["date_2026_2027"])
    cal = svg.calendrier(cen, lambda j: j["buches"], coul, lambda j: f"{j['date']} : {j['t_moy']} °C, {j['buches']:.0f} bûches, stock {j['stock_restant']:.0f}" + (f", {j['evenements']} événement(s)" if j["evenements"] else ""),
                         lambda j: f"#s-{j['date']}", vmax=10)
    rows = "".join(f"<tr id='s-{s['date']}'{' style=background:#fdecea' if s['evenements'] else ''}><td>{s['date']}</td><td class=n>{nb(s['t_moy'], 1)}</td><td class=n>{nb(s['dj18'])}</td><td>{E(s['creux'])}{' (cœur)' if s['coeur'] == '1' else ''}</td>"
                   f"<td class=n>{s['evenements'] or ''}</td><td class=n>{nb(s['buches'])} <span class='barre' style='width:{s['buches'] * 4:.0f}px'></span></td><td class=n>{nb(s['stock_restant'])}</td><td class=n>{nb(s['reserve_evt'])}</td>"
                   f"<td class=n>{nb(s['kwh_evites'])}</td><td class=n>{nb(s['kwh_evites_pointe'], 1)}</td><td class=n>{argent(s['val'])}</td></tr>" for s in cen)
    pg("protocole-sim-jours.html", "Simulation 2026-2027 : jour par jour (aperçu)",
       "<p>Calendrier : rouge = jour d'événement ; orange = feu prévu ; gris = pas de feu. Météo " + CENTRAL + " rejouée, stock ≈ " + str(NB) + " bûches.</p>" + cal +
       "<div class='defile'><table><tr><th>Jour</th><th>T moy.</th><th>DJ</th><th>Creux</th><th>Évts</th><th>Bûches</th><th>Stock restant</th><th>Réserve évts</th><th>kWh évités</th><th>dont en pointe</th><th>Valeur</th></tr>" + rows + "</table></div>")


    # ======================= 4. Saisie =======================
    plan = {s["date_2026_2027"]: s for s in cen}
    dates = [s["date_2026_2027"] for s in cen]
    sai = {r["date"]: r for r in SA}
    cb_p, cb_r, cv_p, cv_r, x1, x2, x3, x4 = 0, 0, 0, 0, [], [], [], []
    for d in dates:
        cb_p += plan[d]["buches"]; cv_p += plan[d]["val"]; x1.append(round(cb_p)); x3.append(round(cv_p, 1))
        if d in sai:
            cb_r += float(sai[d]["buches"] or 0); cv_r += float(sai[d]["valeur_base"] or 0); x2.append(round(cb_r)); x4.append(round(cv_r, 1))
        else:
            x2.append(None); x4.append(None)
    sr_reel = []
    for d in dates:
        sr_reel.append(float(sai[d]["stock_restant"]) if d in sai else None)
    g_b = svg.series([dfr(d) for d in dates], [
        {"nom": "Stock restant : plan (règle, météo " + CENTRAL + ")", "valeurs": [plan[d]["stock_restant"] for d in dates], "couleur": "#9e9e9e", "pointille": True, "points": False},
        {"nom": "Réserve pour les événements", "valeurs": [plan[d]["reserve_evt"] for d in dates], "couleur": "#c62828", "pointille": True, "points": False, "epaisseur": 1},
        {"nom": "Stock restant : réel", "valeurs": sr_reel, "couleur": svg.COUL["buche"], "points": False, "epaisseur": 3}], titre_g="bûches", h=260)
    g_v = svg.series([dfr(d) for d in dates], [
        {"nom": "Valeur cumulée : projection", "valeurs": x3, "couleur": "#9e9e9e", "pointille": True, "points": False},
        {"nom": "Valeur cumulée : réel (hors prime d'événement)", "valeurs": x4, "couleur": svg.COUL["vert"], "points": False, "epaisseur": 3}], titre_g="$", h=240)
    if SA:
        g_k = svg.series([r["date"] for r in SA], [
            {"nom": "kWh saisis", "valeurs": [float(r["kwh"]) if r["kwh"] else None for r in SA], "couleur": svg.COUL["reel"]},
            {"nom": "kWh attendus (modèle, avec tes bûches)", "valeurs": [float(r["kwh_attendu_modele"]) if r["kwh_attendu_modele"] else None for r in SA], "couleur": svg.COUL["sansfeu"], "pointille": True},
            {"nom": "Bûches (axe droit)", "valeurs": [float(r["buches"] or 0) for r in SA], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.4}], titre_g="kWh", titre_d="bûches", h=260)
        tab = ("<div class='defile'><table><tr><th>Date</th><th>Bûches</th><th>Stock restant</th><th>kWh</th><th>Événement (saisi / HQ)</th><th>Témoin</th><th>T moy.</th><th>kWh attendus</th><th>Écart</th><th>Valeur</th><th>Remarque</th></tr>" +
               "".join(f"<tr><td>{r['date']}</td><td class=n>{nb(float(r['buches'] or 0))}</td><td class=n>{r['stock_restant']}{' (compté)' if r['stock_compte'] else ''}</td><td class=n>{r['kwh']}</td><td>{'oui' if r['evenement_hq_saisi'] == '1' else 'non'} / {r['evenements_hq_donnees']}</td>"
                       f"<td>{'témoin' if r['jour_temoin'] == '1' else ''}</td><td class=n>{r['t_moy']}</td><td class=n>{r['kwh_attendu_modele']}</td><td class=n>{r['ecart_kwh']}</td>"
                       f"<td class=n>{argent(float(r['valeur_base'] or 0))}</td><td>{E(r['remarque'])}</td></tr>" for r in SA) + "</table></div>")
    else:
        g_k = ""
        tab = "<div class='alerte'>Aucune journée saisie pour l'instant : les courbes « réel » se rempliront au fil des saisies.</div>"
    ev26 = P["evts_par_hiver"]["2026-2027"]
    h = ["<div class='cartes'>", carte(str(len(SA)), "jours saisis", "neutre"), carte(nb(float(SA[-1]["stock_restant"]) if SA else NB), "bûches restantes (réel)", "neutre", sous=f"plan à ce jour : {nb(next((plan[d]['stock_restant'] for d in reversed(dates) if d <= dt.date.today().isoformat()), NB))} ; réserve : {nb(next((plan[d]['reserve_evt'] for d in reversed(dates) if d <= dt.date.today().isoformat()), 0))}"),
         carte(str(sum(1 for r in SA if r["jour_temoin"] == "1")), "jours témoins", "neutre"),
         carte(f"{ev26['evenements']}", "événements Flex D 2026-27 (données HQ)", "neutre", sous="mis à jour par --maj"), "</div>",
         "<h2>Comment saisir</h2><ol>"
         "<li>Ouvrir <code>data/saisie_2026-2027.csv</code> (Excel, LibreOffice ou un éditeur texte). Une ligne par jour, <b>même sans feu</b>.</li>"
         "<li>Colonnes : <code>date</code> (AAAA-MM-JJ) · <code>buches</code> (nombre) · <code>kwh</code> (consommation du jour, Espace client Hydro-Québec) · "
         "<code>evenement_hq</code> (oui/non) · <code>jour_temoin</code> (oui si jour froid volontairement sans feu) · <code>stock_compte</code> (facultatif : nombre de bûches comptées ce jour-là, remplace le stock calculé) · <code>remarque</code> (absence, feu de plaisir, invités…).</li>"
         "<li>Exemples : <code>2026-12-08,5,61,oui,non,,feu allumé 5 h 30 pour l'événement du matin</code> · <code>2026-12-01,0,72,non,non,330,tas recompté</code></li>"
         "<li>Régénérer : <code>py outils\\preparer_donnees.py --maj</code> (télécharge météo et événements HQ) puis <code>py outils\\generer_site.py</code>, puis F5.</li></ol>",
         "<h2>Stock restant : réel vs plan</h2>", g_b,
         "<p class='petit'>Si la courbe réelle passe plus de 50 bûches sous le plan, ou sous la réserve : ne garder que les événements (règle 5).</p>",
         "<h2>Valeur cumulée : réel vs projection</h2>", g_v, g_k, tab,
         "<p class='petit'>La projection est la simulation ciblée (météo " + CENTRAL + "). Les kWh attendus utilisent la météo réelle du jour et tes bûches. "
         "La valeur « réel » ne compte pas encore la prime d'événement (il faut les kWh horaires ; voir Propositions).</p>"]
    pg("protocole-saisie.html", "Saisie 2026-2027 et suivi réel vs projection", "".join(h))

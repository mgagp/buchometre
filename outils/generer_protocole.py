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
    rc = R[CENTRAL]["strategies"]
    h = ["<div class='cartes'>",
         carte(f"{dfr(C['debut'])} → {dfr(C['fin'])}", "période critique (T lissée ≤ 0 °C)", "neutre", "protocole-meteo.html#critique",
               f"{pct(C['part_dj'])} des degrés-jours, {pct(C['part_evt'])} des événements"),
         carte(f"{min(n_creux)} à {max(n_creux)}", "creux froids par hiver", "neutre", "protocole-meteo.html#cycles",
               f"un tous les ≈ {nb(min(SC[h]['cycle_med'] for h in complets))}–{nb(max(SC[h]['cycle_med'] for h in complets))} jours"),
         carte(f"{nb(min(SC[h]['coeur_med'] for h in complets))}–{nb(max(SC[h]['coeur_med'] for h in complets))} j", "jours « cœur » à viser par creux", "neutre", "protocole-meteo.html#cycles",
               f"creux de {nb(min(SC[h]['jours_med'] for h in complets))}–{nb(max(SC[h]['jours_med'] for h in complets))} jours (médiane)"),
         carte(argent(P["prix_ref"], 0), "coût de référence du bois", "prov", None, f"{H['cordes']} cordes × ({argent(P['prix_corde_2023'])} + 25 $) ; {argent(P['cout_buche'])}/bûche"),
         carte(f"{nb(SE['flex_hors_evt'])}", "bûches pour rentabiliser (Flex D hors événement)", "ko", None, f"tarif D 2026 : {nb(SE['tarif_D'])} ; disponibles ≈ {H['buches_saison']}"),
         carte(f"{argent(min(cible_val), 0)}–{argent(max(cible_val), 0)}", "valeur ciblée sur 3 météos", "ok" if min(cible_val) > P["prix_ref"] else "prov", "protocole-sim.html",
               f"vs {argent(min(quot_val), 0)}–{argent(max(quot_val), 0)} en chauffant chaque jour"),
         "</div>"]
    h.append("<h2>En bref</h2><div class='info'><ol>"
             "<li><b>Objectif de l'hiver</b> : ne plus chauffer au maximum chaque jour, mais placer le bois là où il rapporte le plus : "
             "<b>d'abord pendant les événements de pointe</b> d'Hydro-Québec, <b>ensuite dans les creux froids</b> des systèmes météo. Maximum raisonnable, pas dogmatique.</li>"
             f"<li><b>Pourquoi ça change avec Flex D</b> : hors événement, le kWh est moins cher qu'au tarif D ({nb(F['p2_hiver'] * 100, 3)} ¢ vs {nb(TD['p2'] * 100, 3)} ¢ en 2e tranche) ; "
             f"une bûche y vaut donc {argent(V['flex_hors_evt'])} au lieu de {argent(V['tarif_D'])}. Pendant un événement, le kWh coûte {nb(F['pointe'] * 100, 3)} ¢, "
             f"cinq fois plus : la chaleur d'une bûche livrée dans la fenêtre vaut jusqu'à {argent(V['flex_evt'])}.</li>"
             f"<li><b>Le bois coûte ≈ {argent(P['cout_buche'])} la bûche</b> ({argent(P['prix_ref'], 0)} pour ≈ {H['buches_saison']} bûches). Hors événement, il rapporte moins qu'il ne coûte "
             f"(seuil ≈ {nb(SE['flex_hors_evt'])} bûches) : c'est la captation des événements qui fait passer le bilan au-dessus de zéro.</li>"
             f"<li><b>Ce que dit le modèle 2023-24</b> : kWh du jour = {nb(P['coef'][0], 1)} + {nb(P['coef'][1], 2)} × degrés-jours − {nb(kb, 2)} × bûches. "
             "Le gain par bûche est donc <b>constant</b> (linéaire) ; un test d'interaction ne montre pas qu'une bûche rapporte plus par grand froid (voir l'étude). "
             "Viser le froid sert à trois choses : être là quand Hydro-Québec déclenche un événement (presque toujours par grand froid), "
             "brûler là où la maison peut absorber la chaleur (plafond raisonnable ≈ 0,45 bûche par degré-jour), et réserver un stock limité aux jours qui comptent.</li>"
             "</ol></div>")
    # tarif dynamique
    h.append("<h2 id='tarif'>Le tarif dynamique : quelle option ?</h2>"
             "<div class='alerte'><b>À confirmer avec Marc :</b> sa description (« tarif préférentiel, mais surcharge lors d'un événement ») correspond au <b>tarif Flex D</b>. "
             "L'autre offre dynamique au tarif D, l'<b>option de crédit hivernal</b>, n'est plus offerte aux nouveaux abonnements depuis le 31 mars 2026 "
             "(elle s'applique seulement aux abonnements qui l'avaient au 31 mars 2026). Les deux sont présentées ; les calculs utilisent Flex D.</div>"
             "<table><tr><th></th><th>Flex D (retenu)</th><th>Crédit hivernal (tarif D + crédit)</th></tr>"
             f"<tr><td>Hors événement, hiver (1er déc.–31 mars)</td><td>{nb(F['p1_hiver'] * 100, 3)} ¢/kWh jusqu'à 40 kWh × jours, puis {nb(F['p2_hiver'] * 100, 3)} ¢</td><td>Tarif D : {nb(TD['p1'] * 100, 3)} ¢ puis {nb(TD['p2'] * 100, 3)} ¢</td></tr>"
             f"<tr><td>Pendant un événement</td><td><b>{nb(F['pointe'] * 100, 3)} ¢/kWh</b> pour toute l'énergie consommée</td><td>Tarif D normal, <b>crédit de {nb(H['credit_hivernal_2026'] * 100, 3)} ¢ par kWh effacé</b> sous une consommation de référence</td></tr>"
             "<tr><td>Reste de l'année</td><td>Tarif D (7,065 ¢ / 11,142 ¢)</td><td>Tarif D</td></tr>"
             f"<tr><td>Frais d'accès au réseau</td><td colspan=2>{nb(F['acces'] * 100, 3)} ¢ par jour (inchangés)</td></tr>"
             "<tr><td>Plages horaires</td><td colspan=2>6 h–10 h et 16 h–20 h, tous les jours de la semaine ; sauf 24, 25, 26 et 31 déc., 1er et 2 janv., Vendredi saint et lundi de Pâques</td></tr>"
             "<tr><td>Règles des événements</td><td colspan=2>4 h par événement, au plus 2 par jour, au moins 6 h entre deux, <b>au plus 120 h par hiver</b> (soit au plus 30 événements de 4 h)</td></tr>"
             "<tr><td>Avis</td><td colspan=2>Avant 15 h la veille, par courriel ou notification ; aussi affiché sur hydroquebec.com</td></tr>"
             f"<tr><td>Historique Flex D (données ouvertes)</td><td colspan=2>2024-2025 : {evh['2024-2025']['evenements']} événements sur {evh['2024-2025']['jours']} jours ({nb(evh['2024-2025']['heures'])} h) · "
             f"2025-2026 : {evh['2025-2026']['evenements']} événements sur {evh['2025-2026']['jours']} jours ({nb(evh['2025-2026']['heures'])} h ; HQ annonce 20 dans son bilan) · "
             f"2026-2027 : {evh['2026-2027']['evenements']} à ce jour</td></tr></table>")
    h.append("<h2>Valeur d'une bûche selon le tarif et le moment</h2><table><tr><th>Situation</th><th>Prix du kWh évité</th><th>Valeur d'une bûche (taxes incl.)</th><th>Bûches pour payer " + argent(P["prix_ref"], 0) + "</th></tr>" +
             "".join(f"<tr><td>{E(a)}</td><td class=n>{nb(p * 100, 3)} ¢</td><td class=n>{argent(v)}</td><td class=n>{nb(s)}</td></tr>" for a, p, v, s in [
                 ("Tarif D 2023-24 (référence de l'étude)", 0.10041, V["tarif_D_2023"], SE["tarif_D_2023"]),
                 ("Tarif D 2026, 2e tranche", TD["p2"], V["tarif_D"], SE["tarif_D"]),
                 ("Flex D 2026, hiver hors événement", F["p2_hiver"], V["flex_hors_evt"], SE["flex_hors_evt"]),
                 ("Flex D 2026, pendant un événement (si toute la chaleur tombe dans la fenêtre)", F["pointe"], V["flex_evt"], SE["flex_evt"])]) + "</table>"
             f"<p class='petit'>Valeur = {nb(kb, 2)} kWh/bûche × prix × 1,14975 (TPS+TVQ). Pendant un événement, seule la chaleur livrée de 6 h à 10 h ou de 16 h à 20 h compte au prix fort ; "
             f"on suppose qu'une bûche allumée juste avant y livre {pct(H['part_buche_dans_fenetre'])} de sa chaleur, et que le besoin de chauffage dans la fenêtre est plafonné "
             f"(≈ {nb(H['facteur_pointe_horaire'], 2)} × la moyenne horaire du jour).</p>")
    h.append("<h2>Hypothèse sur le bois</h2><ul>"
             f"<li>Le chiffrier 2023-24 ne mentionne qu'un montant (425 $, colonne « Prix du bois ») ; <b>le nombre de cordes n'y figure pas</b>. On retient tes « 4 cordes habituelles » : "
             f"{argent(P['prix_corde_2023'])} la corde en 2023, + 25 $ = {argent(P['prix_corde_2023'] + 25)} aujourd'hui, soit <b>{argent(P['prix_ref'])}</b> tout inclus.</li>"
             f"<li>Si la saison 2023-24 a brûlé ces 4 cordes (≈ {H['buches_saison']} bûches projetées), une corde ≈ {nb(P['buches_par_corde'])} bûches : plausible pour une corde de foyer (16 po). "
             "À vérifier à la prochaine livraison (compter une corde).</li>"
             "<li>Si 425 $ couvrait 3 cordes, le prix de référence serait 3 × (141,67 + 25) = 500 $ ; les conclusions ne changent presque pas.</li></ul>")
    h.append("<h2 id='regles'>Le protocole en 5 règles</h2><ol>"
             "<li><b>Avis d'événement (veille, avant 15 h)</b> : prévoir le feu. Allumer 30 à 60 min avant 6 h ou 16 h, et entretenir jusqu'à 10 h ou 20 h "
             f"(≈ {nb(min(int(s['buches']) for s in SIM if s['evenements'] != '0' and s['strategie'] == 'cible' and float(s['buches']) > 0))} à "
             f"{nb(max(float(s['buches']) for s in SIM if s['evenements'] != '0' and s['strategie'] == 'cible'))} bûches ce jour-là). Priorité absolue.</li>"
             "<li><b>Creux froid annoncé</b> (prévisions : T moyenne ≥ 3 °C sous la normale récente, ou ≤ −8 °C) : faire du feu les <b>2 à 3 jours les plus froids</b> du creux, "
             "jusqu'à ≈ 0,45 bûche par degré-jour (≈ 9 bûches à −2 °C, 13 à −11 °C, 15 au plus).</li>"
             "<li><b>Redoux</b> (T moyenne au-dessus de 0 °C) : pas de feu « pour rentabiliser » ; un feu de plaisir reste un choix libre, noté comme tel.</li>"
             "<li><b>Jour témoin</b> : une fois par mois environ, un jour froid sans feu (et sans événement), noté « témoin ». C'est ce qui manque le plus pour affiner le modèle.</li>"
             "<li><b>Saisie</b> chaque jour (même sans feu) dans <code>data/saisie_2026-2027.csv</code> : date, bûches, kWh de la veille dans l'Espace client, événement oui/non, témoin, remarque.</li></ol>")
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

    # ======================= 3. Simulation =======================
    def simrows(hv, sn):
        return [s for s in SIM if s["hiver_meteo"] == hv and s["strategie"] == sn and s["date_2026_2027"]]
    cen = simrows(CENTRAL, "cible"); cq = simrows(CENTRAL, "quotidien")
    for s in cen + cq:
        for k in ("t_moy", "dj18", "buches", "kwh_evites", "kwh_evites_pointe", "kwh_sans_feu", "kwh_avec_feu", "valeur_base", "valeur_pointe"):
            s[k] = float(s[k])
        s["evenements"] = int(s["evenements"]); s["val"] = s["valeur_base"] + s["valeur_pointe"]
    labs = [dfr(s["date_2026_2027"]) for s in cen]
    cum, c1, cum_q, c2 = [], 0, [], 0
    for a, b in zip(cen, cq):
        c1 += a["val"]; c2 += b["val"]; cum.append(round(c1, 1)); cum_q.append(round(c2, 1))
    g_sim = svg.series(labs, [
        {"nom": "Bûches prévues (axe droit)", "valeurs": [s["buches"] or None for s in cen], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.45},
        {"nom": "Événements (axe droit)", "valeurs": [s["evenements"] * 3 or None for s in cen], "couleur": "#c62828", "type": "bar", "axe": "d", "opacite": 0.9, "sans_legende": True},
        {"nom": "kWh sans feu (modèle)", "valeurs": [s["kwh_sans_feu"] for s in cen], "couleur": svg.COUL["sansfeu"], "points": False},
        {"nom": "kWh avec le protocole", "valeurs": [s["kwh_avec_feu"] for s in cen], "couleur": svg.COUL["reel"], "points": False},
    ], titre_g="kWh / jour", titre_d="bûches", liens=[f"protocole-sim-jours.html#s-{s['date_2026_2027']}" for s in cen], h=320)
    g_cum = svg.series(labs, [
        {"nom": "Valeur cumulée, protocole", "valeurs": cum, "couleur": svg.COUL["vert"], "type": "area", "points": False},
        {"nom": "Valeur cumulée, feu chaque jour", "valeurs": cum_q, "couleur": "#8e24aa", "pointille": True, "points": False},
        {"nom": f"Coût du bois ({argent(P['prix_ref'], 0)})", "valeurs": [P["prix_ref"]] * len(cen), "couleur": "#000", "epaisseur": 1, "points": False}], titre_g="$", h=260)
    s_c = R[CENTRAL]["strategies"]["cible"]
    h = ["<div class='alerte'><b>Aperçu simulé</b>, pas des données réelles. Météo d'un hiver type rejouée sur le calendrier 2026-2027 : "
         f"<b>{CENTRAL}</b> (degrés-jours médians des 3 hivers ; ses événements Flex D réels). Hypothèses : {H['buches_saison']} bûches disponibles, bois {argent(P['prix_ref'], 0)}, "
         f"Flex D 2026, {nb(kb, 2)} kWh/bûche, modèle 2023-24. Les résultats des deux autres météos sont dans le tableau.</div>",
         "<div class='cartes'>", carte(nb(s_c["jours_feu"]), "jours de feu prévus", "neutre", sous="vs ≈ 145 en chauffant chaque jour"),
         carte(nb(s_c["buches"]), "bûches", "neutre", sous=f"reste {nb(s_c['reste'])}"),
         carte(f"{nb(s_c['evt_couverts'])}/{nb(s_c['evt'])}", "événements couverts", "ok"),
         carte(nb(s_c["kwh"]), "kWh évités", "neutre", sous=f"dont {nb(s_c['prime_kwh'])} pendant les événements"),
         carte(argent(s_c["valeur"], 0), "valeur, taxes incl.", "ok" if s_c["valeur"] > P["prix_ref"] else "ko", sous=f"{argent(s_c['base'], 0)} + prime {argent(s_c['prime'], 0)}"),
         carte(("+" if s_c["valeur"] >= P["prix_ref"] else "") + pct(s_c["valeur"] / P["prix_ref"] - 1), f"vs bois {argent(P['prix_ref'], 0)}", "ok" if s_c["valeur"] > P["prix_ref"] else "ko"),
         "</div><h2>La saison simulée</h2><p class='petit'>Barres rouges : jours d'événement. Cliquer une barre ouvre la journée.</p>", g_sim,
         "<h2>Valeur cumulée vs coût du bois</h2>", g_cum, "<h2>Sur les trois météos</h2>", "".join(t)]
    pg("protocole-sim.html", "Simulation 2026-2027 : sommaire (aperçu)", "".join(h))

    mois = {}
    for a, b in zip(cen, cq):
        m = mois.setdefault(a["date_2026_2027"][:7], {"n": 0, "feu": 0, "b": 0, "evt": 0, "kwh": 0, "val": 0, "valq": 0, "dj": 0, "t": []})
        m["n"] += 1; m["feu"] += a["buches"] > 0; m["b"] += a["buches"]; m["evt"] += a["evenements"]; m["kwh"] += a["kwh_evites"]
        m["val"] += a["val"]; m["valq"] += b["val"]; m["dj"] += a["dj18"]; m["t"].append(a["t_moy"])
    noms = {"2026-11": "novembre 2026", "2026-12": "décembre 2026", "2027-01": "janvier 2027", "2027-02": "février 2027", "2027-03": "mars 2027"}
    g_m = svg.series([noms[k] for k in mois], [
        {"nom": "Valeur protocole ($)", "valeurs": [round(m["val"]) for m in mois.values()], "couleur": svg.COUL["vert"], "type": "bar"},
        {"nom": "Valeur feu chaque jour ($)", "valeurs": [round(m["valq"]) for m in mois.values()], "couleur": "#8e24aa", "type": "bar"},
        {"nom": "Bûches (axe droit)", "valeurs": [round(m["b"]) for m in mois.values()], "couleur": svg.COUL["buche"], "axe": "d"}], titre_g="$", titre_d="bûches", h=280, w=900)
    tm = ("<table><tr><th>Mois</th><th>Jours</th><th>T moy.</th><th>Degrés-jours</th><th>Jours de feu</th><th>Bûches</th><th>Événements</th><th>kWh évités</th><th>Valeur protocole</th><th>Valeur feu chaque jour</th></tr>" +
          "".join(f"<tr><td>{noms[k]}</td><td class=n>{m['n']}</td><td class=n>{nb(sum(m['t']) / len(m['t']), 1)} °C</td><td class=n>{nb(m['dj'])}</td><td class=n>{m['feu']}</td><td class=n>{nb(m['b'])}</td>"
                  f"<td class=n>{m['evt']}</td><td class=n>{nb(m['kwh'])}</td><td class=n>{argent(m['val'])}</td><td class=n>{argent(m['valq'])}</td></tr>" for k, m in mois.items()) + "</table>")
    pg("protocole-sim-mensuel.html", "Simulation 2026-2027 : mensuel (aperçu)", "<p class='petit'>Météo " + CENTRAL + " rejouée sur 2026-2027 (7 nov. → 31 mars).</p>" + g_m + tm)

    def coul(j, r):
        if j["evenements"]:
            return "#c62828"
        return "#cfd8dc" if not j["buches"] else f"rgba(239,108,0,{0.25 + 0.75 * r:.2f})"
    for s in cen:
        s["date"] = dt.date.fromisoformat(s["date_2026_2027"])
    cal = svg.calendrier(cen, lambda j: j["buches"], coul, lambda j: f"{j['date']} : {j['t_moy']} °C, {j['buches']:.0f} bûches" + (f", {j['evenements']} événement(s)" if j["evenements"] else ""),
                         lambda j: f"#s-{j['date']}")
    rows = "".join(f"<tr id='s-{s['date']}'{' style=background:#fdecea' if s['evenements'] else ''}><td>{s['date']}</td><td class=n>{nb(s['t_moy'], 1)}</td><td class=n>{nb(s['dj18'])}</td><td>{E(s['creux'])}{' (cœur)' if s['coeur'] == '1' else ''}</td>"
                   f"<td class=n>{s['evenements'] or ''}</td><td class=n>{nb(s['buches'])} <span class='barre' style='width:{s['buches'] * 4:.0f}px'></span></td><td class=n>{nb(s['kwh_sans_feu'])}</td><td class=n>{nb(s['kwh_avec_feu'])}</td>"
                   f"<td class=n>{nb(s['kwh_evites_pointe'], 1)}</td><td class=n>{argent(s['val'])}</td></tr>" for s in cen)
    pg("protocole-sim-jours.html", "Simulation 2026-2027 : jour par jour (aperçu)",
       "<p>Calendrier : rouge = jour d'événement ; orange = feu prévu ; gris = pas de feu. Météo " + CENTRAL + " rejouée.</p>" + cal +
       "<div class='defile'><table><tr><th>Jour</th><th>T moy.</th><th>DJ</th><th>Creux</th><th>Évts</th><th>Bûches</th><th>kWh sans feu</th><th>kWh avec feu</th><th>kWh évités en pointe</th><th>Valeur</th></tr>" + rows + "</table></div>")

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
    g_b = svg.series([dfr(d) for d in dates], [
        {"nom": "Bûches cumulées : projection", "valeurs": x1, "couleur": "#9e9e9e", "pointille": True, "points": False},
        {"nom": "Bûches cumulées : réel", "valeurs": x2, "couleur": svg.COUL["buche"], "points": False, "epaisseur": 3}], titre_g="bûches", h=240)
    g_v = svg.series([dfr(d) for d in dates], [
        {"nom": "Valeur cumulée : projection", "valeurs": x3, "couleur": "#9e9e9e", "pointille": True, "points": False},
        {"nom": "Valeur cumulée : réel (hors prime d'événement)", "valeurs": x4, "couleur": svg.COUL["vert"], "points": False, "epaisseur": 3}], titre_g="$", h=240)
    if SA:
        g_k = svg.series([r["date"] for r in SA], [
            {"nom": "kWh saisis", "valeurs": [float(r["kwh"]) if r["kwh"] else None for r in SA], "couleur": svg.COUL["reel"]},
            {"nom": "kWh attendus (modèle, avec tes bûches)", "valeurs": [float(r["kwh_attendu_modele"]) if r["kwh_attendu_modele"] else None for r in SA], "couleur": svg.COUL["sansfeu"], "pointille": True},
            {"nom": "Bûches (axe droit)", "valeurs": [float(r["buches"] or 0) for r in SA], "couleur": svg.COUL["buche"], "type": "bar", "axe": "d", "opacite": 0.4}], titre_g="kWh", titre_d="bûches", h=260)
        tab = ("<div class='defile'><table><tr><th>Date</th><th>Bûches</th><th>kWh</th><th>Événement (saisi / HQ)</th><th>Témoin</th><th>T moy.</th><th>kWh attendus</th><th>Écart</th><th>Valeur</th><th>Remarque</th></tr>" +
               "".join(f"<tr><td>{r['date']}</td><td class=n>{nb(float(r['buches'] or 0))}</td><td class=n>{r['kwh']}</td><td>{'oui' if r['evenement_hq_saisi'] == '1' else 'non'} / {r['evenements_hq_donnees']}</td>"
                       f"<td>{'témoin' if r['jour_temoin'] == '1' else ''}</td><td class=n>{r['t_moy']}</td><td class=n>{r['kwh_attendu_modele']}</td><td class=n>{r['ecart_kwh']}</td>"
                       f"<td class=n>{argent(float(r['valeur_base'] or 0))}</td><td>{E(r['remarque'])}</td></tr>" for r in SA) + "</table></div>")
    else:
        g_k = ""
        tab = "<div class='alerte'>Aucune journée saisie pour l'instant : les courbes « réel » se rempliront au fil des saisies.</div>"
    ev26 = P["evts_par_hiver"]["2026-2027"]
    h = ["<div class='cartes'>", carte(str(len(SA)), "jours saisis", "neutre"), carte(nb(sum(float(r['buches'] or 0) for r in SA)), "bûches brûlées", "neutre", sous=f"projection à ce jour : {nb(sum(plan[d]['buches'] for d in dates if d <= dt.date.today().isoformat()))}"),
         carte(str(sum(1 for r in SA if r["jour_temoin"] == "1")), "jours témoins", "neutre"),
         carte(f"{ev26['evenements']}", "événements Flex D 2026-27 (données HQ)", "neutre", sous="mis à jour par --maj"), "</div>",
         "<h2>Comment saisir</h2><ol>"
         "<li>Ouvrir <code>data/saisie_2026-2027.csv</code> (Excel, LibreOffice ou un éditeur texte). Une ligne par jour, <b>même sans feu</b>.</li>"
         "<li>Colonnes : <code>date</code> (AAAA-MM-JJ) · <code>buches</code> (nombre) · <code>kwh</code> (consommation du jour, Espace client Hydro-Québec) · "
         "<code>evenement_hq</code> (oui/non) · <code>jour_temoin</code> (oui si jour froid volontairement sans feu) · <code>remarque</code> (absence, feu de plaisir, invités…).</li>"
         "<li>Exemple : <code>2026-12-08,9,61,oui,non,feu allumé 5 h 30 pour l'événement du matin</code></li>"
         "<li>Régénérer : <code>py outils\\preparer_donnees.py --maj</code> (télécharge météo et événements HQ) puis <code>py outils\\generer_site.py</code>, puis F5.</li></ol>",
         "<h2>Réel vs projection</h2>", g_b, g_v, g_k, tab,
         "<p class='petit'>La projection est la simulation ciblée (météo " + CENTRAL + "). Les kWh attendus utilisent la météo réelle du jour et tes bûches. "
         "La valeur « réel » ne compte pas encore la prime d'événement (il faut les kWh horaires ; voir Propositions).</p>"]
    pg("protocole-saisie.html", "Saisie 2026-2027 et suivi réel vs projection", "".join(h))

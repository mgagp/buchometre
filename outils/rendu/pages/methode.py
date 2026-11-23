"""Méthode : modèle et incertitudes (repris de l'analyse 2023-24), historique des décisions, fonctionnement du site.
Archives : index des saisons passées."""
import html
from rendu.gabarit import page, ARCH23, DEPOT

E = html.escape
MARQUE_A_FAIRE = "<h2>À décider ou à faire</h2>"
MARQUE_ITER = "<h2>Propositions de la première itération (pour mémoire)</h2>"


def separer_decisions(corps):
    """decisions.html (ancien) → (historique des décisions, encadré « à faire » pour Stratégie)."""
    avant, _, reste = corps.partition(MARQUE_A_FAIRE)
    a_faire, _, iter_ = reste.partition(MARQUE_ITER)
    hist = avant + (("<h3>Propositions de la première itération (pour mémoire)</h3>" + iter_) if iter_ else "")
    encadre = ("<h2 id='a-faire'>À faire ou à décider</h2><div class='info'>" + a_faire + "</div>") if a_faire else ""
    return hist.replace("<h2", "<h3").replace("</h2>", "</h3>"), encadre


def rendre(sortie, quand):
    hist, _ = separer_decisions(sortie.get("decisions.html", ""))
    site = ("<h2 id='site'>Comment le site est construit</h2><ul>"
            "<li><b>Données</b> : <code>data/</code> (saisie, inventaire, <code>saisons.json</code>, CSV et JSON dérivés) et <code>sources/</code> (copies en lecture seule : chiffrier, météo, événements Hydro-Québec).</li>"
            "<li><b>Calculs</b> : <code>outils/calculs/</code> (modèle 2023-24, protocole et simulation, état de la saison, recommandation du jour, validation de la saisie). Aucun HTML.</li>"
            "<li><b>Rendu</b> : <code>outils/rendu/</code> (gabarit, composants, graphiques SVG, une page par module). Aucune couleur.</li>"
            "<li><b>Thème</b> : <code>theme/site.css</code> (variables de couleur, typographie). Le relooking ne touche que ce dossier.</li>"
            "<li><b>Publication</b> : GitHub Actions reconstruit et publie le site à chaque push, et chaque matin vers 5 h 45 (heure de Toronto) avec la météo, la prévision "
            "et les événements Hydro-Québec du jour. Si un téléchargement échoue, le site est construit avec les données versionnées et l'accueil le signale.</li>"
            "<li><b>Météo observée</b> : une seule source, <code>outils/calculs/meteo.py</code> : Environnement Canada, station Ste-Anne-de-Bellevue 1 "
            "(repli Montréal-Trudeau, puis Open-Meteo marqué « estimation par modèle »), moyenne = (max + min) / 2. Elle sert au modèle, aux normales, à la simulation "
            "et à l'historique. Les 30 derniers jours sont retéléchargés chaque matin (révisions acceptées) et commités dans <code>data/meteo_observee_AAAA-AAAA.csv</code>.</li>"
            "<li><b>Recommandation du jour</b> : une seule source, <code>outils/calculs/recommandation.py</code> (règle de budget, détection des creux froids), "
            "appliquée à la prévision d'Environnement Canada pour Vaudreuil-Dorion (Open-Meteo en secours). Publiée dans "
            "<a href='data/recommandation.json'>data/recommandation.json</a> et conservée chaque matin, par un commit automatique, dans "
            "<code>data/recommandations_AAAA-AAAA.csv</code>.</li>"
            "<li><b>Moment du feu</b> : <code>plan_feu()</code> (même module) donne les heures d'allumage et de baisse ; il ne change ni la décision ni le nombre de bûches. "
            "L'heure du min vient de la prévision horaire d'EC (24 h), sinon d'Open-Meteo (« modèle ») ; pour les jours passés, des relevés horaires d'EC.</li>"
            "<li><b>Plan et projection</b> : le plan applique la règle de budget à la météo réelle depuis l'inventaire ; la projection part du dernier stock connu, "
            "suit la règle sur la prévision, puis la dépense moyenne des trois derniers hivers simulés sous la règle.</li>"
            "<li><b>Limite</b> : la prime d'événement réelle n'est pas mesurée (il faudrait les kWh horaires des jours d'événement) ; seule la valeur hors événement est suivie.</li>"
            "<li><b>Changement de saison</b> : une entrée dans <code>data/saisons.json</code> ; la saison précédente passe dans Archives.</li>"
            f"<li>Code et historique : <a href='{DEPOT}'>{DEPOT.replace('https://', '')}</a>.</li></ul>")
    boussole = (f"<p>Intention, principes de travail et décisions détaillées (contexte, options, pour et contre) : "
                f"<a href='{DEPOT}/tree/main/docs/boussole'>la boussole du projet</a>.</p>")
    corps = (sortie.get("methode.html", "") + "<h2 id='decisions'>Historique des décisions</h2>" + boussole + hist + site)
    page("methode.html", "Méthode, modèle et décisions", corps, quand,
         sous=f"<p class='sous'>Comment les chiffres sont calculés, avec leurs incertitudes. Généré le {E(quand)}.</p>", contexte="Méthode")


def archives(saisons, quand):
    items = []
    for s in saisons:
        lien = ARCH23 + "index.html" if s["type"] == "chiffrier" else f"archives/{s['id']}/index.html"
        items.append(f"<a class='carte carte-saison' href='{lien}'><div class='v'>{E(s['titre'])}</div><div class='l'>{E(s.get('resume', ''))}</div></a>")
    corps = ("<div class='cartes'>" + "".join(items) + "</div>"
             "<p class='petit'>La saison en cours est à l'accueil. À la fin d'une saison, il suffit de déclarer la suivante dans <code>data/saisons.json</code> : "
             "la saison terminée apparaît ici avec son tableau de bord figé (bilan réel contre plan).</p>")
    page("archives/index.html", "Archives", corps, quand, sous="<p class='sous'>Les saisons passées et leur analyse.</p>", contexte="Archives")

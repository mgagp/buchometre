"""Chemins du projet (partagés par les couches calculs et rendu)."""
import os
OUTILS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(OUTILS)
DATA = os.path.join(RACINE, "data")
SOURCES = os.path.join(RACINE, "sources")
THEME = os.path.join(RACINE, "theme")
OUT = os.path.join(RACINE, "rapports")

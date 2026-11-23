#!/usr/bin/env python3
"""Vérifie le site généré (rapports/) : liens internes et ancres valides, aucune couleur codée en dur dans le HTML.

Usage : python outils/verifier_site.py   (code de sortie 1 en cas de problème ; utilisé par GitHub Actions)
"""
import os, re, sys, posixpath
from urllib.parse import unquote
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chemins import OUT

RE_LIEN = re.compile(r"""\b(?:href|src)=(['"])([^'"]*)\1""")
RE_ID = re.compile(r"""\bid=(?:['"]([^'"]+)['"]|([^\s>]+))""")
RE_COUL = re.compile(r"""(?:fill|stroke|color|background(?:-color)?)\s*[:=]\s*['"]?\s*(?:#[0-9a-fA-F]{3,8}\b|rgba?\()""")


def main():
    pages = {}
    for d, _, fs in os.walk(OUT):
        for f in fs:
            if f.endswith(".html"):
                p = os.path.relpath(os.path.join(d, f), OUT).replace(os.sep, "/")
                pages[p] = open(os.path.join(d, f), encoding="utf-8").read()
    ids = {p: {a or b for a, b in RE_ID.findall(h)} for p, h in pages.items()}
    erreurs = []
    for p, h in pages.items():
        for _, v in RE_LIEN.findall(h):
            if not v or v.startswith(("http:", "https:", "mailto:", "data:", "javascript:", "//")):
                continue
            chemin, _, frag = v.partition("#")
            cible = posixpath.normpath(posixpath.join(posixpath.dirname(p), unquote(chemin))) if chemin else p
            if not os.path.exists(os.path.join(OUT, cible)):
                erreurs.append(f"{p} : lien brisé → {v}")
            elif frag and cible.endswith(".html") and frag not in ids.get(cible, set()):
                erreurs.append(f"{p} : ancre absente → {v}")
        if "<style" in h:
            erreurs.append(f"{p} : bloc <style> (le CSS vit dans theme/)")
        for m in RE_COUL.finditer(h):
            erreurs.append(f"{p} : couleur codée en dur « {m.group(0)} » (utiliser une variable du thème)")
    for e in erreurs[:60]:
        print(e)
    print(f"{len(pages)} pages vérifiées, {len(erreurs)} problème(s).")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())

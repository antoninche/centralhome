#!/usr/bin/env python3
"""Régénère les visuels de la marque à partir du nom inscrit dans site.json et des symboles SVG.

  python3 outils/visuels.py

À relancer après un changement de nom commercial ou de symbole, puis reconstruire le site.
Prérequis : pip install playwright fonttools brotli uharfbuzz ; Google Chrome installé ; sips (fourni avec macOS).

Sources (à modifier ici) :
  src/favicon.svg             le symbole, coins arrondis
  marque/symbole-carre.svg    le symbole plein cadre, pour LinkedIn et l'icône d'écran d'accueil
  outils/partage.html         mise en page de l'image de partage
  outils/banniere.html        mise en page de la bannière LinkedIn

Sorties pour le site :
  src/images/partage.jpg      image affichée quand on partage un lien (1200 x 630)
  src/images/icone-32.png     petite icône
  src/images/icone-180.png    icône d'écran d'accueil (iPhone, iPad)
Sorties pour la marque, dans marque/ :
  symbole.svg                         le symbole seul
  logo-horizontal.svg / .png          symbole et nom, pour les fonds clairs
  logo-horizontal-blanc.svg / .png    symbole et nom, pour les fonds foncés
  logo-linkedin-400.png               logo de la page entreprise LinkedIn (400 x 400)
  banniere-linkedin-1512x256.png      bannière de la page entreprise LinkedIn (1512 x 256)
"""
import io
import json
import math
import re
import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
OUTILS = RACINE / "outils"
IMAGES = RACINE / "src" / "images"
MARQUE = RACINE / "marque"
POLICE = RACINE / "src" / "polices" / "inter-latin.woff2"

# Le nom dans le logo, pour un symbole de 48 de haut : Inter 700, coupe Display (taille optique 32),
# ligne de base posée sur la ligne du sol du symbole (y = 33), hauteur d'x égale au mur du fond.
TAILLE = 33
GRAISSE = 700
OPTIQUE = 32
APPROCHE = -0.01  # em
X0 = 61
LIGNE_DE_BASE = 33

# Couleurs du nom : début et fin (« Central » et « Home »).
SUR_CLAIR = ("#0B1E2D", "#0369A1")
SUR_FONCE = ("#FFFFFF", "#4FC3F7")


def symbole():
    """Contenu du symbole (sans la balise <svg> englobante), viewBox 0 0 48 48."""
    svg = (RACINE / "src" / "favicon.svg").read_text(encoding="utf-8")
    return re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())


def couper_nom(nom):
    """Coupe le nom avant sa dernière capitale : CentralHome donne Central et Home."""
    coupe = re.search(r"^(.+?)([A-ZÀ-Ý][^A-ZÀ-Ý]*)$", nom)
    return (coupe.group(1), coupe.group(2)) if coupe else (nom, "")


def nombre(valeur):
    return ("%.2f" % valeur).rstrip("0").rstrip(".")


def nom_en_traces(nom, couleurs):
    """Le nom dessiné en tracés : le fichier SVG n'a besoin d'aucune police.

    Le placement des lettres vient de HarfBuzz, avec le crénage de la police et l'interlettrage,
    comme Chrome affiche le même texte. Renvoie les tracés et le bord droit de l'encre."""
    brut = TTFont(str(POLICE))
    brut.flavor = None
    tampon = io.BytesIO()
    brut.save(tampon)
    police_hb = hb.Font(hb.Face(tampon.getvalue()))
    police_hb.set_variations({"wght": GRAISSE, "opsz": OPTIQUE})
    texte = hb.Buffer()
    texte.add_str(nom)
    texte.guess_segment_properties()
    # Avec un interlettrage non nul, Chrome n'applique pas les ligatures facultatives.
    hb.shape(police_hb, texte, {"kern": True, "liga": False, "clig": False})

    instance = instancer.instantiateVariableFont(TTFont(str(POLICE)), {"wght": GRAISSE, "opsz": OPTIQUE})
    jeu = instance.getGlyphSet()
    ordre = instance.getGlyphOrder()
    echelle = TAILLE / instance["head"].unitsPerEm
    approche = APPROCHE * instance["head"].unitsPerEm
    debut = len(couper_nom(nom)[0])
    traces = ([], [])
    bornes = BoundsPen(jeu)
    x = 0.0
    for info, position in zip(texte.glyph_infos, texte.glyph_positions):
        glyphe = jeu[ordre[info.codepoint]]
        transformation = (echelle, 0, 0, -echelle,
                          X0 + (x + position.x_offset) * echelle, LIGNE_DE_BASE - position.y_offset * echelle)
        stylo = SVGPathPen(jeu, ntos=nombre)
        glyphe.draw(TransformPen(stylo, transformation))
        glyphe.draw(TransformPen(bornes, transformation))
        if stylo.getCommands():
            traces[0 if info.cluster < debut else 1].append(stylo.getCommands())
        x += position.x_advance + approche
    chemins = "".join('<path fill="{}" d="{}"/>'.format(couleur, " ".join(partie))
                      for couleur, partie in zip(couleurs, traces) if partie)
    return chemins, bornes.bounds[2]


def logo_horizontal(nom, couleurs):
    chemins, droite = nom_en_traces(nom, couleurs)
    largeur = math.ceil(droite)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 48" width="{w}" height="48" role="img" '
            'aria-label="{t}"><title>{t}</title>{s}{c}</svg>\n').format(w=largeur, t=nom, s=symbole(), c=chemins), largeur


def sans_profil_couleur(fichier):
    # Retire le profil de couleur ajouté par le navigateur (il porte le nom de son éditeur).
    if fichier.suffix != ".jpg":
        subprocess.run(["sips", "--deleteColorManagementProperties", str(fichier)], capture_output=True, check=True)
        return
    # JPEG : sips ne retire pas ce profil. On enlève les segments APP1 (Exif), APP2 (profil ICC)
    # et APP13 (Photoshop) sans recompresser l'image.
    donnees = fichier.read_bytes()
    sortie, i = bytearray(donnees[:2]), 2
    while i + 4 <= len(donnees) and donnees[i] == 0xFF and donnees[i + 1] != 0xDA:
        longueur = int.from_bytes(donnees[i + 2:i + 4], "big")
        if donnees[i + 1] not in (0xE1, 0xE2, 0xED):
            sortie += donnees[i:i + 2 + longueur]
        i += 2 + longueur
    fichier.write_bytes(bytes(sortie) + donnees[i:])


def main():
    config = json.loads((RACINE / "site.json").read_text(encoding="utf-8"))
    nom = config.get("site", {}).get("nom", "").strip()
    if not nom:
        raise SystemExit("Indiquer le nom commercial dans site.json (site.nom).")
    MARQUE.mkdir(exist_ok=True)

    (MARQUE / "symbole.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" role="img" aria-label="{t}"><title>{t}</title>{s}</svg>\n'
        .format(t=nom, s=symbole()), encoding="utf-8")
    logos = {}
    for base, couleurs in (("logo-horizontal", SUR_CLAIR), ("logo-horizontal-blanc", SUR_FONCE)):
        svg, largeur = logo_horizontal(nom, couleurs)
        (MARQUE / (base + ".svg")).write_text(svg, encoding="utf-8")
        logos[base] = (svg, largeur)
    carre = (MARQUE / "symbole-carre.svg").read_text(encoding="utf-8").strip()

    sorties = []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")

        def page(largeur, hauteur, echelle=1):
            return nav.new_page(viewport={"width": largeur, "height": hauteur}, device_scale_factor=echelle)

        def image_svg(svg, largeur, hauteur, fichier, echelle=1):
            pg = page(largeur, hauteur, echelle)
            tete = re.match(r"<svg[^>]*>", svg).group(0)
            nouvelle_tete = re.sub(r'\s(?:width|height)="[^"]*"', "", tete).replace(
                "<svg ", '<svg width="{}" height="{}" '.format(largeur, hauteur), 1)
            svg = nouvelle_tete + svg[len(tete):]
            pg.set_content('<!DOCTYPE html><html><body style="margin:0;background:transparent">' + svg + "</body></html>")
            pg.screenshot(path=str(fichier), omit_background=True, clip={"x": 0, "y": 0, "width": largeur, "height": hauteur})
            sorties.append(fichier)

        def gabarit(fichier_html, largeur, hauteur, sortie, **options):
            pg = page(largeur, hauteur)
            pg.goto((OUTILS / fichier_html).as_uri())
            pg.evaluate("s => { document.querySelector('[data-logo]').innerHTML = s; }", logos["logo-horizontal"][0])
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(sortie), **options)
            sorties.append(sortie)

        gabarit("partage.html", 1200, 630, IMAGES / "partage.jpg", type="jpeg", quality=88)
        gabarit("banniere.html", 1512, 256, MARQUE / "banniere-linkedin-1512x256.png")
        image_svg((MARQUE / "symbole.svg").read_text(encoding="utf-8"), 32, 32, IMAGES / "icone-32.png")
        # Icônes carrées plein cadre : l'appareil ou LinkedIn arrondit les coins lui-même.
        image_svg(carre, 180, 180, IMAGES / "icone-180.png")
        image_svg(carre, 400, 400, MARQUE / "logo-linkedin-400.png")
        # Logos horizontaux en PNG, fond transparent, quatre fois la taille du SVG.
        for base, (svg, largeur) in logos.items():
            image_svg(svg, largeur, 48, MARQUE / (base + ".png"), echelle=4)
        nav.close()

    for fichier in sorties:
        sans_profil_couleur(fichier)
    print("Visuels régénérés pour « {} » : src/images/ et marque/.".format(nom))


if __name__ == "__main__":
    main()

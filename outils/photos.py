#!/usr/bin/env python3
"""Prépare les photos du site : plusieurs largeurs, formats AVIF et WebP, sans métadonnées.

  python3 outils/photos.py

Lit photos-sources/photos.json (une entrée par photo : fichier, texte alternatif, crédits,
et au besoin un recadrage {"x", "y", "largeur", "hauteur"} en pixels de la photo d'origine)
et écrit dans src/images/ les fichiers nom-480.avif, nom-480.webp, etc. (480, 800, 1200 et 1600 px,
ou moins si l'original est plus petit), ainsi que
src/images/photos.json, que outils/construire.py utilise.

Outils nécessaires sur le Mac : sips (fourni avec macOS), cwebp et avifenc
(brew install webp libavif).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCES = RACINE / "photos-sources"
IMAGES = RACINE / "src" / "images"
LARGEURS = (480, 800, 1200, 1600)


def dimensions(chemin):
    sortie = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(chemin)],
                            capture_output=True, text=True, check=True).stdout
    valeurs = {}
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("pixelWidth:") or ligne.startswith("pixelHeight:"):
            cle, val = ligne.split(":")
            valeurs[cle] = int(val)
    return valeurs["pixelWidth"], valeurs["pixelHeight"]


def orientation_exif(chemin):
    """Orientation EXIF d'un JPEG (1 si absente)."""
    d = Path(chemin).read_bytes()[:131072]
    i = d.find(b"Exif\x00\x00")
    if i < 0:
        return 1
    t = i + 6
    ordre = "big" if d[t:t + 2] == b"MM" else "little"
    lire = lambda p, n: int.from_bytes(d[p:p + n], ordre)
    ifd = t + lire(t + 4, 4)
    for k in range(lire(ifd, 2)):
        e = ifd + 2 + 12 * k
        if lire(e, 2) == 0x0112:
            return lire(e + 8, 2)
    return 1


def main():
    for outil in ("sips", "cwebp", "avifenc"):
        if not shutil.which(outil):
            sys.exit("Outil absent : {} (brew install webp libavif)".format(outil))
    description = json.loads((SOURCES / "photos.json").read_text(encoding="utf-8"))
    manifeste = {}
    IMAGES.mkdir(parents=True, exist_ok=True)
    for ancien in IMAGES.glob("*-*.avif"):
        ancien.unlink()
    for ancien in IMAGES.glob("*-*.webp"):
        ancien.unlink()
    with tempfile.TemporaryDirectory() as temp:
        for nom, info in description.items():
            if nom.startswith("_"):
                continue
            source = SOURCES / info["fichier"]
            if info.get("variantes") is False:
                manifeste[nom] = {"largeurs": [], "alt": info.get("alt", ""), "sujet": info.get("sujet", nom),
                                  "auteur": info.get("auteur", ""), "source": info.get("source", ""),
                                  "licence": info.get("licence", ""), "page": info.get("page", "")}
                print("{:<18} crédits seulement".format(nom))
                continue
            if not source.exists():
                print("{:<18} ignorée : fichier absent ({})".format(nom, info["fichier"]))
                continue
            rotation = {3: 180, 6: 90, 8: 270}.get(orientation_exif(source))
            if rotation:
                tournee = Path(temp) / "{}-tournee.jpg".format(nom)
                subprocess.run(["sips", "-r", str(rotation), str(source), "--out", str(tournee)],
                               capture_output=True, check=True)
                source = tournee
            cadre = info.get("recadrage")
            if cadre:
                recadree = Path(temp) / "{}-recadree.jpg".format(nom)
                subprocess.run(["sips", "--cropToHeightWidth", str(cadre["hauteur"]), str(cadre["largeur"]),
                                "--cropOffset", str(cadre["y"]), str(cadre["x"]), str(source), "--out", str(recadree)],
                               capture_output=True, check=True)
                source = recadree
            largeur_orig, hauteur_orig = dimensions(source)
            largeurs = [l for l in LARGEURS if l <= largeur_orig] or [largeur_orig]
            if largeurs[-1] < largeur_orig < LARGEURS[-1]:
                largeurs.append(largeur_orig)
            for l in largeurs:
                intermediaire = Path(temp) / "{}-{}.jpg".format(nom, l)
                subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "95",
                                "--resampleWidth", str(l), str(source), "--out", str(intermediaire)],
                               capture_output=True, check=True)
                subprocess.run(["cwebp", "-quiet", "-q", "78", "-m", "6", "-metadata", "none",
                                str(intermediaire), "-o", str(IMAGES / "{}-{}.webp".format(nom, l))], check=True)
                subprocess.run(["avifenc", "-q", "58", "-s", "4", "--ignore-exif", "--ignore-xmp",
                                str(intermediaire), str(IMAGES / "{}-{}.avif".format(nom, l))],
                               capture_output=True, check=True)
            plus_grande = largeurs[-1]
            manifeste[nom] = {
                "largeurs": largeurs,
                "largeur": plus_grande,
                "hauteur": round(hauteur_orig * plus_grande / largeur_orig),
                "alt": info.get("alt", ""),
                "sujet": info.get("sujet", nom),
                "auteur": info.get("auteur", ""),
                "source": info.get("source", ""),
                "licence": info.get("licence", ""),
                "page": info.get("page", ""),
            }
            poids = sum((IMAGES / "{}-{}.{}".format(nom, l, f)).stat().st_size for l in largeurs for f in ("avif", "webp"))
            print("{:<18} {} largeurs, {:.0f} Ko au total".format(nom, len(largeurs), poids / 1024))
    (IMAGES / "photos.json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Manifeste écrit : src/images/photos.json")


if __name__ == "__main__":
    main()

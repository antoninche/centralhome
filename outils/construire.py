#!/usr/bin/env python3
"""Construit le site à partir de src/ et de site.json, dans le dossier docs/, que GitHub Pages publie.

  python3 outils/construire.py                 version de travail : non indexée, informations manquantes surlignées
  python3 outils/construire.py --publication   version à mettre en ligne : s'arrête s'il manque une information obligatoire

Le site est construit dans un dossier temporaire, qui ne remplace docs/ que si la construction réussit.
Aucune dépendance : Python 3.9 ou plus récent suffit.
"""
import argparse
import base64
import datetime
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "src"
SITE = RACINE / "docs"
TEMPORAIRE = RACINE / ".construction"
CONFIG = RACINE / "site.json"

# Informations sans lesquelles le site ne peut pas être publié.
OBLIGATOIRES = {
    "site.url": "adresse du site",
    "entreprise.siren": "numéro SIREN",
    "entreprise.adresse": "adresse de l’entreprise",
    "contact.telephone": "téléphone",
    "contact.email": "adresse e-mail",
    "mediateur.nom": "nom du médiateur",
    "mediateur.adresse": "adresse du médiateur",
    "mediateur.site": "site du médiateur",
    "hebergeur.nom": "nom de l’hébergeur",
    "hebergeur.adresse": "adresse de l’hébergeur",
    "hebergeur.telephone": "téléphone de l’hébergeur",
    "donnees.prestataires": "fournisseur de la messagerie",
}

RE_ENTETE_PAGE = re.compile(r"\A<!--page\s+(\{.*?\})\s*-->\s*", re.S)
RE_PARTIEL = re.compile(r"\{\{>\s*([\w-]+)\s*\}\}")
RE_SI = re.compile(r"\{\{#si ([\w.-]+)\}\}(.*?)\{\{/si \1\}\}", re.S)
RE_SINON = re.compile(r"\{\{#sinon ([\w.-]+)\}\}(.*?)\{\{/sinon \1\}\}", re.S)
RE_PHOTO = re.compile(r'\{\{photo ([\w-]+) "([^"]*)" "([^"]*)"( eager)?\}\}')
RE_BRUT = re.compile(r"\{\{\{([\w.-]+)\}\}\}")
RE_VALEUR = re.compile(r"\{\{([\w.-]+)(?:\|(\w+))?\}\}")
RE_SCRIPT_EN_LIGNE = re.compile(r"<script>(.*?)</script>", re.S)


def lire(chemin):
    return chemin.read_text(encoding="utf-8")


def obtenir(ctx, cle):
    valeur = ctx
    for morceau in cle.split("."):
        if isinstance(valeur, dict) and morceau in valeur:
            valeur = valeur[morceau]
        else:
            return None
    return valeur


def vrai(valeur):
    return bool(valeur) and valeur != "0"


def siren_valide(siren):
    chiffres = siren.replace(" ", "")
    if not re.fullmatch(r"\d{9}", chiffres):
        return False
    total = 0
    for rang, c in enumerate(reversed(chiffres)):
        n = int(c)
        if rang % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def tel_international(numero):
    chiffres = re.sub(r"[^\d+]", "", numero)
    if chiffres.startswith("+"):
        return chiffres
    if chiffres.startswith("0033"):
        return "+" + chiffres[2:]
    if chiffres.startswith("0") and len(chiffres) == 10:
        return "+33" + chiffres[1:]
    return chiffres


def euros(valeur):
    try:
        n = float(valeur)
    except (TypeError, ValueError):
        return html.escape(str(valeur))
    if n == int(n):
        texte = "{:,}".format(int(n)).replace(",", " ")
    else:
        texte = "{:,.2f}".format(n).replace(",", " ").replace(".", ",").replace(" ", " ")
    return texte + "&nbsp;€"


def minifier_css(texte):
    # Chaînes et commentaires repérés en une seule passe : une apostrophe dans un commentaire n'ouvre pas de chaîne.
    morceaux = re.split(r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|/\*.*?\*/)", texte, flags=re.S)
    sortie = []
    for i, m in enumerate(morceaux):
        if i % 2 == 1:
            if not m.startswith("/*"):
                sortie.append(m)
            continue
        m = re.sub(r"\s+", " ", m)
        m = re.sub(r"\s*([{};,>])\s*", r"\1", m)
        m = re.sub(r":\s+", ":", m)
        m = m.replace(";}", "}")
        sortie.append(m)
    return "".join(sortie).strip() + "\n"


def empreinte(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()[:10]


def charger_photos():
    manifeste = SRC / "images" / "photos.json"
    if not manifeste.exists():
        return {}
    photos = json.loads(lire(manifeste))
    return {nom: info for nom, info in photos.items() if not nom.startswith("_")}


def contexte(config, actifs, photos):
    ctx = json.loads(json.dumps(config))
    ctx["annee"] = str(datetime.date.today().year)
    contact = ctx.setdefault("contact", {})
    contact["tel_lien"] = tel_international(contact.get("telephone", "")) if contact.get("telephone") else ""
    contact["email_lien"] = contact.get("email", "")
    contact["email_code"] = masquer(contact["email_lien"]) if contact["email_lien"] else ""
    contact.setdefault("delai_reponse", "2 jours ouvrés")
    mediateur = ctx.setdefault("mediateur", {})
    site_mediateur = mediateur.get("site", "")
    if site_mediateur:
        mediateur["site_lien"] = site_mediateur if site_mediateur.startswith("http") else "https://" + site_mediateur
    else:
        mediateur["site_lien"] = "#"
    prix = ctx.setdefault("prix", {})
    if "mise_en_service" in prix:
        # Exemple de budget de la page Tarifs : diagnostic, installation, appareils en plus et matériel de base.
        en_plus = max(0, prix.get("exemple_appareils", 0) - prix.get("appareils_inclus", 0))
        prix["exemple_en_plus"] = en_plus
        prix["exemple_sup"] = en_plus * prix.get("appareil_sup", 0)
        prix["exemple_total"] = (prix.get("diagnostic", 0) + prix["mise_en_service"] + prix["exemple_sup"]
                                 + prix.get("boitier", 0) + prix.get("cle_radio", 0))
    entreprise = ctx.setdefault("entreprise", {})
    entreprise["initiales"] = (entreprise.get("prenom", "")[:1] + entreprise.get("nom", "")[:1]).upper()
    # Le nom en deux couleurs dans l'en-tête et le pied de page, coupé avant sa dernière capitale :
    # CentralHome donne Central et Home, comme dans le logo (outils/visuels.py).
    site = ctx.setdefault("site", {})
    coupe = re.search(r"^(.+?)([A-ZÀ-Ý][^A-ZÀ-Ý]*)$", site.get("nom", ""))
    site["nom_debut"], site["nom_fin"] = (coupe.group(1), coupe.group(2)) if coupe else (site.get("nom", ""), "")
    ctx["actifs"] = actifs
    ctx["photos"] = {nom: True for nom, info in photos.items() if info.get("largeurs")}
    ctx["photos"]["usages"] = all(n in photos for n in ("usage-lumiere", "usage-chauffage", "usage-capteur"))
    return ctx


class Rendu:
    def __init__(self, ctx, photos):
        self.ctx = ctx
        self.photos = photos
        self.manquants = set()

    def partiels(self, texte, profondeur=0):
        if profondeur > 6:
            raise SystemExit("Partiels imbriqués trop profondément.")

        def remplacer(m):
            chemin = SRC / "partiels" / (m.group(1) + ".html")
            if not chemin.exists():
                raise SystemExit("Partiel introuvable : " + str(chemin))
            return self.partiels(lire(chemin).rstrip("\n"), profondeur + 1)

        return RE_PARTIEL.sub(remplacer, texte)

    def blocs(self, texte):
        avant = None
        while avant != texte:
            avant = texte
            texte = RE_SI.sub(lambda m: m.group(2) if vrai(obtenir(self.ctx, m.group(1))) else "", texte)
            texte = RE_SINON.sub(lambda m: "" if vrai(obtenir(self.ctx, m.group(1))) else m.group(2), texte)
        return texte

    def photo(self, m):
        nom, alt, tailles, prioritaire = m.group(1), m.group(2), m.group(3), bool(m.group(4))
        info = self.photos.get(nom)
        if not info or not info.get("largeurs"):
            self.manquants.add("photo « " + nom + " »")
            return '<span class="photo-absente" aria-hidden="true"></span>'
        if alt == "-":
            alt = ""
        elif not alt:
            alt = info.get("alt", "")
        largeurs = info["largeurs"]

        def jeu(fmt):
            return ", ".join("images/{}-{}.{} {}w".format(nom, l, fmt, l) for l in largeurs)

        defaut = largeurs[min(1, len(largeurs) - 1)]
        chargement = 'fetchpriority="high" decoding="async"' if prioritaire else 'loading="lazy" decoding="async"'
        return (
            '<picture><source type="image/avif" srcset="{a}" sizes="{s}">'
            '<source type="image/webp" srcset="{w}" sizes="{s}">'
            '<img src="images/{n}-{d}.webp" width="{lg}" height="{ht}" alt="{alt}" {c}></picture>'
        ).format(a=jeu("avif"), w=jeu("webp"), s=tailles, n=nom, d=defaut, lg=info["largeur"],
                 ht=info["hauteur"], alt=html.escape(alt, quote=True), c=chargement)

    def valeur(self, cle, filtre=None, brut=False):
        v = obtenir(self.ctx, cle)
        if v is None and cle not in OBLIGATOIRES:
            raise SystemExit("Balise inconnue dans les gabarits : {{" + cle + "}}")
        if v is None or v == "":
            if cle in OBLIGATOIRES:
                self.manquants.add(OBLIGATOIRES[cle])
                return '<em class="a-completer">' + html.escape(OBLIGATOIRES[cle]) + "</em>"
            return ""
        if filtre == "euros":
            return euros(v)
        if filtre:
            raise SystemExit("Filtre inconnu : " + filtre)
        if brut:
            return str(v)
        return html.escape(str(v), quote=True)

    def texte(self, gabarit):
        texte = self.partiels(gabarit)
        texte = self.blocs(texte)
        texte = RE_PHOTO.sub(self.photo, texte)
        texte = RE_BRUT.sub(lambda m: self.valeur(m.group(1), brut=True), texte)
        texte = RE_VALEUR.sub(lambda m: self.valeur(m.group(1), m.group(2)), texte)
        return texte


def masquer(valeur):
    """Encode une coordonnée (texte inversé, puis base64) ; site.js la décode à l’affichage."""
    return base64.b64encode(valeur[::-1].encode("utf-8")).decode("ascii")


def proteger_contacts(texte, contact):
    """Retire le numéro et l’adresse e-mail du code HTML, pour les robots qui les y cherchent.

    Les liens tel: et mailto: sont encodés dans data-lien et rétablis par site.js. Dans le texte,
    la coordonnée est coupée en deux attributs que la feuille de styles affiche (::before et ::after),
    même sans JavaScript ; site.js remet ensuite le texte réel, pour le copier-coller et les lecteurs d’écran.
    """
    tel, tel_lien, email = contact.get("telephone", ""), contact.get("tel_lien", ""), contact.get("email", "")
    for schema, cible in (("tel:", tel_lien), ("mailto:", email)):
        if cible:
            texte = texte.replace('href="{}{}"'.format(schema, html.escape(cible, quote=True)),
                                  'href="devis.html" data-lien="{}"'.format(masquer(schema + cible)))
    remplacements = []
    if email and "@" in email:
        local, _, domaine = email.partition("@")
        remplacements.append((html.escape(email, quote=True),
                              '<span class="cm cm-arobase" data-a="{}" data-b="{}"></span>'.format(
                                  html.escape(local, quote=True), html.escape(domaine, quote=True))))
    if tel:
        milieu = len(tel) // 2
        remplacements.append((html.escape(tel, quote=True),
                              '<span class="cm" data-a="{}" data-b="{}"></span>'.format(
                                  html.escape(tel[:milieu], quote=True), html.escape(tel[milieu:], quote=True))))
    if not remplacements:
        return texte
    # Seulement dans le texte : ni dans les balises (attributs), ni dans les scripts.
    morceaux = re.split(r"(<[^>]+>)", texte)
    dans_script = False
    for i, morceau in enumerate(morceaux):
        if morceau.startswith("<"):
            nom = morceau[1:].split(None, 1)[0].lower() if len(morceau) > 2 else ""
            if nom.startswith("script"):
                dans_script = True
            elif nom.startswith("/script"):
                dans_script = False
            continue
        if not dans_script:
            for ancien, nouveau in remplacements:
                morceau = morceau.replace(ancien, nouveau)
            morceaux[i] = morceau
    return "".join(morceaux)


def jsonld(ctx):
    e, p, s = ctx["entreprise"], ctx["prix"], ctx["site"]
    url = s["url"].rstrip("/")
    offres = [
        ("Diagnostic à domicile", p["diagnostic"], False),
        ("Installation complète", p["mise_en_service"], True),
        ("Suivi annuel", p["suivi"], False),
    ]
    donnees = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": url + "/#entreprise",
        "name": s["nom"],
        "legalName": e["nom_legal"],
        "description": "Installation et suivi de domotique locale basée sur Home Assistant, chez des particuliers, à Marseille.",
        "url": url + "/",
        "image": url + "/images/partage.jpg",
        "areaServed": {"@type": "City", "name": "Marseille"},
        "address": {"@type": "PostalAddress", "addressLocality": e.get("ville", "Marseille"), "addressCountry": "FR"},
        "makesOffer": [
            {"@type": "Offer", "name": nom, "priceCurrency": "EUR",
             "itemOffered": {"@type": "Service", "name": nom},
             **({"priceSpecification": {"@type": "PriceSpecification", "minPrice": str(prix), "priceCurrency": "EUR"}}
                if a_partir_de else {"price": str(prix)})}
            for nom, prix, a_partir_de in offres
        ],
    }
    texte = json.dumps(donnees, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + texte + "\n</script>"


def credits_photos(photos):
    lignes = []
    for nom, info in sorted(photos.items()):
        if not info.get("auteur"):
            continue
        lignes.append(
            '<li>{sujet}&nbsp;: photo de {auteur}, {source}, sous {licence} (<a href="{page}">page d’origine</a>).</li>'.format(
                sujet=html.escape(info.get("sujet", nom)), auteur=html.escape(info["auteur"]),
                source=html.escape(info.get("source", "")), licence=html.escape(info.get("licence", "")),
                page=html.escape(info.get("page", ""), quote=True)))
    if not lignes:
        return ""
    return ("<p>Les photos viennent de banques d’images dont la licence permet un usage commercial&nbsp;:</p>\n<ul>\n"
            + "\n".join(lignes) + "\n</ul>")


def politique_securite(empreintes):
    # Déclarée dans chaque page (balise meta) : GitHub Pages n'envoie pas d'en-têtes HTTP personnalisés.
    # frame-ancestors est sans effet dans une balise meta, il n'y figure donc pas.
    return "; ".join([
        "default-src 'self'",
        "script-src 'self' " + " ".join("'sha256-" + e + "'" for e in sorted(empreintes)),
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "form-action 'self' mailto:",
        "base-uri 'self'",
        "object-src 'none'",
    ])


def verifier_liens(dossier, racine="/"):
    """Vérifie que chaque lien interne mène à un fichier et à un identifiant qui existent.

    racine est le chemin du site dans son adresse (/centralhome/ sur GitHub Pages) : la page 404
    emploie des liens absolus qui commencent par ce chemin."""
    erreurs = []
    pages = {p.name: lire(p) for p in dossier.glob("*.html")}
    ids = {nom: set(re.findall(r'\sid="([^"]+)"', contenu)) for nom, contenu in pages.items()}
    # Noms exacts, majuscules comprises : GitHub Pages les distingue, le disque du Mac non.
    existants = {p.relative_to(dossier).as_posix() for p in dossier.rglob("*")}
    for nom, contenu in pages.items():
        cibles = re.findall(r'\s(?:href|src)="([^"]+)"', contenu)
        for ensemble in re.findall(r'\ssrcset="([^"]+)"', contenu):
            cibles += [morceau.strip().split(" ")[0] for morceau in ensemble.split(",")]
        for cible in cibles:
            if re.match(r"^(?:[a-z]+:|//)", cible):
                continue
            chemin, _, fragment = cible.partition("#")
            chemin = chemin.split("?")[0]
            if chemin.startswith("/") and not chemin.startswith(racine):
                erreurs.append("{} : lien hors du chemin du site « {} »".format(nom, cible))
                continue
            chemin = chemin[len(racine):] if chemin.startswith(racine) else chemin
            fichier = chemin or nom
            if chemin and chemin not in existants:
                erreurs.append("{} : fichier introuvable « {} »".format(nom, cible))
            elif fragment and fichier.endswith(".html") and fragment not in ids.get(fichier, set()):
                erreurs.append("{} : ancre introuvable « {} »".format(nom, cible))
    return erreurs


def construire(publication):
    config = json.loads(lire(CONFIG))
    photos = charger_photos()

    cible = TEMPORAIRE
    cible.mkdir()
    for dossier in ("js", "polices"):
        shutil.copytree(SRC / dossier, cible / dossier)
    (cible / "css").mkdir()
    (cible / "css" / "site.css").write_text(minifier_css(lire(SRC / "css" / "site.css")), encoding="utf-8")
    (cible / "images").mkdir()
    for fichier in (SRC / "images").iterdir():
        if fichier.is_file() and fichier.suffix in (".avif", ".webp", ".png", ".svg", ".jpg"):
            shutil.copy2(fichier, cible / "images" / fichier.name)
    shutil.copy2(SRC / "favicon.svg", cible / "favicon.svg")

    actifs = {
        "css": "css/site.css?v=" + empreinte(SRC / "css" / "site.css"),
        "js": "js/site.js?v=" + empreinte(SRC / "js" / "site.js"),
        "devis": "js/devis.js?v=" + empreinte(SRC / "js" / "devis.js"),
    }
    ctx = contexte(config, actifs, photos)
    ctx["credits_photos"] = credits_photos(photos)
    ctx["pages"] = {"cgv": (SRC / "pages" / "cgv.html").exists()}
    ctx["date_maj"] = config.get("date_maj_textes", "")

    tous_manquants = set()
    pages_plan = []
    for source in sorted((SRC / "pages").glob("*.html")):
        brut = lire(source)
        m = RE_ENTETE_PAGE.match(brut)
        if not m:
            raise SystemExit("En-tête <!--page {...} --> absent : " + source.name)
        page = json.loads(m.group(1))
        gabarit = brut[m.end():]
        rendu_page = Rendu(ctx, photos)
        for cle in ("titre", "description"):
            page[cle] = html.unescape(rendu_page.texte(page.get(cle, "")))
        extra = []
        if page.get("jsonld") and publication:
            extra.append(jsonld(ctx))
        if page.get("script") == "devis":
            extra.append('<script src="{}" defer></script>'.format(actifs["devis"]))
        page["tete_extra"] = "\n".join(extra)
        page.setdefault("classe_corps", "")
        ctx["page"] = page
        ctx["robots"] = page.get("robots") or ("" if publication else "noindex, nofollow")
        rendu = Rendu(ctx, photos)
        sortie = rendu.texte(gabarit)
        if "{{" in sortie or "}}" in sortie:
            reste = re.findall(r"\{\{[^}]*\}\}", sortie)[:5]
            raise SystemExit("Balises non remplacées dans {} : {}".format(source.name, reste))
        if page.get("chemin"):
            debut_nav = sortie.find('<nav class="nav"')
            fin_nav = sortie.find("</nav>", debut_nav)
            if debut_nav != -1:
                nav = sortie[debut_nav:fin_nav].replace('<a href="{}">'.format(page["chemin"]),
                                                        '<a href="{}" aria-current="page">'.format(page["chemin"]))
                sortie = sortie[:debut_nav] + nav + sortie[fin_nav:]
        if page.get("robots") != "noindex":
            pages_plan.append(source.name)
        sortie = proteger_contacts(sortie, ctx["contact"])
        if source.name == "404.html":
            # Servie à n'importe quelle adresse (/devis/, /a/b) : liens et fichiers depuis la racine du site.
            racine = urlsplit(config.get("site", {}).get("url", "")).path.rstrip("/") + "/"
            sortie = re.sub(r'(\s(?:href|src|srcset)=")(?![a-z]+:|/|#)', lambda m: m.group(1) + racine, sortie)
            sortie = re.sub(r'(, )(images/)', lambda m: m.group(1) + racine + m.group(2), sortie)
        empreintes = {base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
                      for script in RE_SCRIPT_EN_LIGNE.findall(sortie)}
        if '<meta charset="utf-8">' not in sortie:
            raise SystemExit("Balise <meta charset=\"utf-8\"> absente : " + source.name)
        csp = '<meta http-equiv="Content-Security-Policy" content="{}">'.format(politique_securite(empreintes))
        sortie = sortie.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + csp, 1)
        (cible / source.name).write_text(sortie, encoding="utf-8")
        tous_manquants |= rendu.manquants | rendu_page.manquants

    url = config.get("site", {}).get("url", "").rstrip("/")
    if publication:
        (cible / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n".format(url), encoding="utf-8")
        entrees = "\n".join(
            "  <url><loc>{}/{}</loc></url>".format(url, "" if p == "index.html" else p)
            for p in sorted(pages_plan, key=lambda n: (n != "index.html", n)))
        (cible / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + entrees + "\n</urlset>\n", encoding="utf-8")
    else:
        (cible / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    # GitHub Pages sert les fichiers tels quels, sans les passer par Jekyll.
    (cible / ".nojekyll").write_text("", encoding="utf-8")

    erreurs = verifier_liens(cible, urlsplit(url).path.rstrip("/") + "/")
    if publication:
        siren = config.get("entreprise", {}).get("siren", "")
        if siren and not siren_valide(siren):
            erreurs.append("Le numéro SIREN « {} » n’est pas valide.".format(siren))
        if url and not url.startswith("https://"):
            erreurs.append("L’adresse du site doit commencer par https://")
        # Chaque information obligatoire est exigée, même si un gabarit ne l'affiche que lorsqu'elle existe.
        for cle, libelle in OBLIGATOIRES.items():
            if not obtenir(config, cle):
                tous_manquants.add(libelle)
        erreurs += ["Information manquante : " + m for m in sorted(tous_manquants)]
        ent = config.get("entreprise", {})
        if not re.search(r"\bEI\b|entrepreneur individuel", ent.get("nom_legal", "")):
            erreurs.append("entreprise.nom_legal doit contenir « EI » ou « entrepreneur individuel » après le nom, comme sur l’extrait d’immatriculation (code de commerce, R526-27).")
        if ent.get("activite") not in ("commerciale", "artisanale", "libérale"):
            erreurs.append("Indiquer entreprise.activite (commerciale, artisanale ou libérale), comme sur l’extrait d’immatriculation.")
        elif ent["activite"] == "commerciale" and not ent.get("rcs"):
            erreurs.append("Activité commerciale : entreprise.rcs (« RCS » suivi de la ville du greffe) doit figurer sur le site (code de commerce, art. R123-237).")
        if not ctx["pages"]["cgv"]:
            erreurs.append("Conditions générales de vente absentes : écrire src/pages/cgv.html (obligatoires pour des devis acceptés à distance).")
    return erreurs, sorted(tous_manquants)


def main():
    parser = argparse.ArgumentParser(description="Construit le site dans docs/.")
    parser.add_argument("--publication", action="store_true", help="version à mettre en ligne (contrôles stricts)")
    args = parser.parse_args()
    if TEMPORAIRE.exists():
        shutil.rmtree(TEMPORAIRE)
    try:
        erreurs, manquants = construire(args.publication)
    except BaseException:
        shutil.rmtree(TEMPORAIRE, ignore_errors=True)
        raise
    if erreurs:
        shutil.rmtree(TEMPORAIRE)
        print("Problèmes trouvés :")
        for e in erreurs:
            print("  - " + e)
        print("\nCorriger ces points puis relancer. Le site de docs/ n’a pas été modifié.")
        sys.exit(1)
    if SITE.exists():
        shutil.rmtree(SITE)
    TEMPORAIRE.rename(SITE)
    pages = sorted(p.name for p in SITE.glob("*.html"))
    print("Site construit dans docs/ ({} pages : {}).".format(len(pages), ", ".join(pages)))
    if args.publication:
        print("Version de publication : prête à être publiée.")
    else:
        print("Version de travail : non indexée par les moteurs de recherche.")
        if manquants:
            print("À compléter dans site.json avant publication : " + ", ".join(manquants) + ".")


if __name__ == "__main__":
    main()

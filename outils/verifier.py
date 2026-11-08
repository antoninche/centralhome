#!/usr/bin/env python3
"""Vérifie le site construit dans un vrai navigateur (Chrome piloté par Playwright).

  python3 outils/verifier.py /chemin/vers/axe.min.js

Étapes :
  1. sert docs/ en local comme GitHub Pages : sous le chemin de site.url (/centralhome/),
     avec la page 404 pour toute adresse inconnue ;
  2. lance axe-core (WCAG 2.0, 2.1 et 2.2, niveaux A et AA) sur chaque page,
     en thème clair et sombre, sur ordinateur (1440 px) et sur mobile (390 px) ;
  3. relève les erreurs de la console et les débordements horizontaux ;
  4. remplit le formulaire de demande comme un visiteur et vérifie le message préparé ;
  5. vérifie la navigation au clavier : lien d'évitement, menu mobile ;
  6. ouvre une adresse inconnue et vérifie la page 404 servie à sa place.

Prérequis : pip install playwright ; Google Chrome installé ; axe-core
(npm install axe-core@4 dans un dossier à part, puis donner le chemin de axe.min.js).
Sortie : outils/verification/resultats.json et un résumé à l'écran.
"""
import functools
import http.server
import io
import json
import socketserver
import sys
import threading
import urllib.parse
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
SITE = RACINE / "docs"
SORTIE = RACINE / "outils" / "verification"
ETIQUETTES = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def chemin_du_site():
    """Chemin du site dans son adresse : /centralhome/ pour https://antoninche.github.io/centralhome."""
    config = json.loads((RACINE / "site.json").read_text(encoding="utf-8"))
    return urllib.parse.urlsplit(config.get("site", {}).get("url", "")).path.rstrip("/") + "/"


class CommeGitHubPages(http.server.SimpleHTTPRequestHandler):
    """Sert docs/ sous le chemin du site, et 404.html avec le code 404 pour une adresse inconnue."""
    chemin = "/"

    def log_message(self, *args):
        pass

    def send_head(self):
        adresse = urllib.parse.urlsplit(self.path).path
        if not adresse.startswith(self.chemin):
            return self.introuvable()
        self.path = "/" + self.path[len(self.chemin):]
        fichier = Path(self.translate_path(self.path))
        if not (fichier / "index.html" if fichier.is_dir() else fichier).is_file():
            return self.introuvable()
        return super().send_head()

    def introuvable(self):
        contenu = (SITE / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(contenu)))
        self.end_headers()
        return io.BytesIO(contenu)


def serveur():
    chemin = chemin_du_site()
    gestion = functools.partial(type("Gestion", (CommeGitHubPages,), {"chemin": chemin}), directory=str(SITE))
    srv = socketserver.TCPServer(("127.0.0.1", 0), gestion)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:{}{}".format(srv.server_address[1], chemin)


def axe(page):
    # axe-core est chargé par add_init_script : la politique de sécurité des pages bloquerait un script ajouté.
    return page.evaluate(
        """async (etiquettes) => {
            const r = await axe.run(document, { runOnly: { type: 'tag', values: etiquettes } });
            return r.violations.map(v => ({ regle: v.id, impact: v.impact, aide: v.help,
                elements: v.nodes.slice(0, 5).map(n => n.target.join(' ')) }));
        }""", ETIQUETTES)


def tester_formulaire(page, base):
    page.goto(base + "devis.html?demande=question", wait_until="networkidle")
    resultat = {}
    resultat["demande_preselectionnee"] = page.locator('input[name="demande"]:checked').get_attribute("value")
    page.goto(base + "devis.html?demande=diagnostic", wait_until="networkidle")
    # Envoi à vide : les erreurs doivent apparaître et le focus aller au premier champ en erreur.
    page.get_by_role("button", name="Envoyer ma demande").click()
    resultat["erreurs_affichees"] = page.locator(".message-erreur:not(:empty)").all_inner_texts()
    resultat["focus_apres_erreur"] = page.evaluate("document.activeElement && document.activeElement.id")
    page.get_by_label("Votre prénom").fill("Camille")
    page.get_by_label("Commune ou arrondissement").fill("Marseille 7e")
    page.get_by_label("Votre adresse e-mail").fill("camille@example.com")
    page.get_by_text("Préciser votre logement").click()
    page.get_by_label("Maison", exact=True).check()
    page.get_by_label("Ampoules ou prises connectées").check()
    page.get_by_label("Chauffage").check()
    page.get_by_role("button", name="Envoyer ma demande").click()
    page.wait_for_timeout(300)
    lien = page.locator('.boite-envoi a[href^="mailto:"]').first.get_attribute("href") or ""
    requete = urllib.parse.parse_qs(urllib.parse.urlsplit(lien).query)
    corps = requete.get("body", [""])[0]
    resultat["objet"] = requete.get("subject", [""])[0]
    resultat["message_prepare"] = corps
    nb = "\u00a0"
    attendus = ["Je souhaite un diagnostic à domicile.", "Commune" + nb + ": Marseille 7e", "Logement" + nb + ": maison",
                "ampoules ou prises connectées", "chauffage pièce par pièce", "Prénom" + nb + ": Camille",
                "Mon adresse e-mail" + nb + ": camille@example.com"]
    resultat["manquants_dans_message"] = [a for a in attendus if a not in corps]
    return resultat


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage : python3 outils/verifier.py /chemin/vers/axe.min.js")
    script_axe = Path(sys.argv[1]).read_text(encoding="utf-8")
    SORTIE.mkdir(parents=True, exist_ok=True)
    pages = sorted(p.name for p in SITE.glob("*.html"))
    srv, base = serveur()
    resultats = {"pages": {}, "formulaire": None, "clavier": {}, "page_404": {}}
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        for theme in ("light", "dark"):
            for largeur in (1440, 390):
                ctx = nav.new_context(viewport={"width": largeur, "height": 900}, color_scheme=theme)
                ctx.add_init_script(script=script_axe)
                page = ctx.new_page()
                erreurs = []
                page.on("console", lambda m: erreurs.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: erreurs.append(str(e)))
                for nom in pages:
                    page.goto(base + nom, wait_until="networkidle")
                    deborde = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                    cle = "{} {} {}".format(nom, theme, largeur)
                    resultats["pages"][cle] = {"axe": axe(page), "console": list(erreurs),
                                               "debordement_horizontal": deborde}
                    erreurs.clear()
                ctx.close()
        ctx = nav.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        resultats["formulaire"] = tester_formulaire(page, base)
        page.goto(base + "index.html", wait_until="networkidle")
        page.keyboard.press("Tab")
        resultats["clavier"]["premier_element"] = page.evaluate("document.activeElement.textContent.trim()")
        page.get_by_role("button", name="Menu").click()
        resultats["clavier"]["menu_ouvert"] = page.get_by_role("button", name="Menu").get_attribute("aria-expanded")
        page.keyboard.press("Escape")
        resultats["clavier"]["menu_ferme_par_echap"] = page.get_by_role("button", name="Menu").get_attribute("aria-expanded")
        ctx.close()
        # Adresse inconnue, deux niveaux sous le site : la page 404 doit s'afficher avec ses styles et ses images.
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        erreurs = []
        page.on("console", lambda m: erreurs.append((m.text, m.location.get("url", ""))) if m.type == "error" else None)
        inconnue = base + "dossier/inconnu/"
        reponse = page.goto(inconnue, wait_until="networkidle")
        resultats["page_404"] = {
            "code": reponse.status if reponse else None,
            "styles": page.evaluate("getComputedStyle(document.body).fontFamily.includes('Inter')"),
            # Le code 404 du document lui-même est attendu ; toute autre erreur signale un fichier introuvable.
            "erreurs_console": [texte for texte, url in erreurs if url != inconnue],
        }
        ctx.close()
        nav.close()
    srv.shutdown()
    (SORTIE / "resultats.json").write_text(json.dumps(resultats, ensure_ascii=False, indent=2), encoding="utf-8")

    violations = {c: r["axe"] for c, r in resultats["pages"].items() if r["axe"]}
    consoles = {c: r["console"] for c, r in resultats["pages"].items() if r["console"]}
    debords = [c for c, r in resultats["pages"].items() if r["debordement_horizontal"]]
    print("Pages contrôlées : {} combinaisons".format(len(resultats["pages"])))
    print("Violations axe-core : {}".format(sum(len(v) for v in violations.values())))
    for c, v in violations.items():
        for x in v:
            print("  - {} : {} ({}) {}".format(c, x["regle"], x["impact"], x["elements"][:2]))
    print("Erreurs de console : {}".format(sum(len(v) for v in consoles.values())))
    for c, v in consoles.items():
        print("  - {} : {}".format(c, v[:2]))
    print("Débordements horizontaux : {}".format(debords or "aucun"))
    f = resultats["formulaire"]
    print("Formulaire : demande présélectionnée = {}, erreurs affichées = {}, focus = {}, objet = {}, éléments manquants dans le message = {}".format(
        f["demande_preselectionnee"], len(f["erreurs_affichees"]), f["focus_apres_erreur"],
        f["objet"], f["manquants_dans_message"] or "aucun"))
    print("Clavier : {}".format(resultats["clavier"]))
    print("Page 404 : {}".format(resultats["page_404"]))


if __name__ == "__main__":
    main()

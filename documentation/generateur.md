# Générateur du site

[`outils/construire.py`](../outils/construire.py) assemble le site dans `docs/`, que GitHub Pages publie, à partir de `src/` et de `site.json`. Il n'utilise que la bibliothèque standard de Python, version 3.9 ou plus récente.

```sh
python3 outils/construire.py                 # version de travail
python3 outils/construire.py --publication   # version publiée
```

## Étapes

1. Prépare le site dans un dossier temporaire, `.construction/` : copie les scripts, la police, les images et le favicon, et minifie la feuille de styles.
2. Ajoute à l'adresse de la feuille de styles et des scripts une empreinte de leur contenu (`css/site.css?v=…`), pour qu'aucun cache ne serve une ancienne version après une mise à jour.
3. Pour chaque page de `src/pages/`, lit l'en-tête de la page, insère les partiels, évalue les conditions, puis remplace les photos et les valeurs de `site.json`. Une balise inconnue, ou restée non remplacée dans la page, arrête la construction.
4. Marque le lien de la page courante dans le menu (`aria-current="page"`).
5. Retire l'adresse e-mail et le numéro du code HTML (voir [Configuration](configuration.md#numéro-et-adresse-e-mail-protégés)).
6. Réécrit les liens de la page 404 depuis le chemin du site (`/centralhome/`), puisque GitHub Pages la sert à la place de toute adresse inconnue, à n'importe quelle profondeur.
7. Déclare dans chaque page sa politique de sécurité du contenu, avec l'empreinte SHA-256 de ses scripts en ligne.
8. Écrit `robots.txt`, le plan du site (`sitemap.xml`, version publiée seulement) et `.nojekyll`.
9. Vérifie que chaque lien interne mène à un fichier, et chaque ancre à un identifiant, qui existent.
10. Si tout est correct, remplace `docs/` par le nouveau site. Sinon, supprime le dossier temporaire et laisse `docs/` intact.

## En-tête de page

Chaque fichier de `src/pages/` commence par un objet JSON dans un commentaire HTML :

```html
<!--page {
  "titre": "Tarifs : diagnostic et installation domotique à Marseille | {{site.nom}}",
  "description": "Diagnostic à domicile {{prix.diagnostic|euros}}, puis installation à prix fixe…",
  "chemin": "tarifs.html",
  "classe_corps": "a-barre-mobile"
} -->
{{> tete}}
{{> entete}}
```

| Clé | Rôle |
|---|---|
| `titre`, `description` | balise `<title>`, description et Open Graph ; elles acceptent les balises `{{…}}` |
| `chemin` | adresse de la page dans le site, pour l'URL canonique, Open Graph et le lien actif du menu : le nom du fichier (`tarifs.html`), vide pour l'accueil, dont l'URL canonique est la racine du site. Le fichier publié garde le nom du fichier source |
| `classe_corps` | classe ajoutée à `<body>` |
| `script` | `"devis"` charge `js/devis.js` sur la page |
| `jsonld` | ajoute les données structurées schema.org `LocalBusiness` dans la version publiée |
| `robots` | `"noindex"` exclut la page des moteurs de recherche et du plan du site (page 404) |

## Syntaxe des gabarits

| Syntaxe | Effet |
|---|---|
| `{{cle}}` | valeur de `site.json` ou calculée par le générateur, échappée pour le HTML |
| `{{cle\|euros}}` | montant écrit à la française, avec espace insécable : `1 250 €` |
| `{{{cle}}}` | valeur insérée sans échappement, réservée au HTML produit par le générateur |
| `{{> nom}}` | contenu de `src/partiels/nom.html`, avec ses propres partiels |
| `{{#si cle}}…{{/si cle}}` | bloc gardé si la valeur est renseignée (ni vide, ni `0`, ni `"0"`) |
| `{{#sinon cle}}…{{/sinon cle}}` | bloc gardé dans le cas contraire |
| `{{photo nom "alt" "sizes"}}` | élément `<picture>` en AVIF et WebP aux largeurs de `src/images/photos.json` ; `eager` à la fin pour une image prioritaire, `"-"` comme texte alternatif pour une image décorative, `""` pour reprendre celui de `photos.json` |

Une clé inconnue dans `{{cle}}` ou `{{{cle}}}` arrête la construction ; une valeur vide donne un texte vide. Dans `{{#si}}` et `{{#sinon}}`, une clé inconnue compte comme vide, sans message : l'orthographe des conditions est à vérifier, surtout celles qui cachent des mentions légales. Une photo absente de `src/images/photos.json` laisse un emplacement vide et figure dans la liste de fin ; la version publiée la refuse. Les informations obligatoires à la publication, vides, sont remplacées par un texte surligné et listées à la fin.

## Version de travail et version publiée

| | Version de travail | Version publiée |
|---|---|---|
| Moteurs de recherche | `noindex` sur chaque page, `robots.txt` qui interdit tout | pages indexables, `robots.txt` qui renvoie au `sitemap.xml` |
| Information obligatoire absente | surlignée dans la page et listée | construction refusée, `docs/` inchangé |
| Données structurées | aucune | `LocalBusiness` sur l'accueil |

La version publiée contrôle aussi la clé du SIREN, l'adresse du site en https, la mention « EI » dans le nom légal, le type d'activité (et le RCS si elle est commerciale) et la présence des conditions générales de vente.

Sur une adresse github.io de projet, `robots.txt` n'est pas à la racine du domaine : les moteurs l'ignorent, et le plan du site se déclare dans leurs outils pour webmestres. L'exclusion des pages passe par leur balise `noindex`.

## Sécurité

GitHub Pages n'accepte pas d'en-têtes HTTP personnalisés. La politique de sécurité du contenu est donc déclarée dans chaque page, juste après `<meta charset>` :

```
default-src 'self'; script-src 'self' 'sha256-…'; style-src 'self'; img-src 'self' data:;
font-src 'self'; form-action 'self' mailto:; base-uri 'self'; object-src 'none'
```

Aucun style en ligne n'est permis ; `data:` sert aux icônes de la feuille de styles, `mailto:` au formulaire. `frame-ancestors` n'a pas d'effet dans une balise `<meta>` et n'y figure donc pas. GitHub Pages sert le site en HTTPS.

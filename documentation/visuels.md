# Visuels et photos

## Logo, icônes, image de partage et bannière LinkedIn

```sh
python3 outils/visuels.py
python3 outils/construire.py
```

[`outils/visuels.py`](../outils/visuels.py) reprend le nom de `site.json`, le symbole de `src/favicon.svg` et sa version plein cadre `marque/symbole-carre.svg`, et refait :

- dans `src/images/` : `partage.jpg` (1200 × 630), l'image affichée quand on partage le lien, et les icônes `icone-32.png` et `icone-180.png` ;
- dans `marque/` : `logo-linkedin-400.png` (logo de la page entreprise, 400 × 400), `banniere-linkedin-1512x256.png` (bannière, 1512 × 256), `logo-horizontal.svg` et `.png` (pour les fonds clairs), `logo-horizontal-blanc.svg` et `.png` (pour les fonds foncés), et `symbole.svg`.

La mise en page de l'image de partage et de la bannière est dans `outils/partage.html` et `outils/banniere.html`. Le nom des logos SVG est dessiné en tracés, avec le crénage d'Inter appliqué par HarfBuzz : les logos n'ont besoin d'aucune police. Les déclinaisons `symbole-sur-bleu.svg` (liseré blanc, pour les fonds bleus) et `symbole-une-couleur.svg` (tampon, gravure, broderie) sont dessinées à la main dans `marque/`.

L'illustration de la page d'accueil est `src/images/illustration.svg` : un seul fichier pour le mode clair et le mode sombre, sans balise `<style>`, compatible avec la politique de sécurité du site. Les règles d'usage sont dans [la charte graphique](../marque/charte-graphique.md).

Le script demande Playwright, Google Chrome, fontTools, brotli et uharfbuzz (`pip install playwright fonttools brotli uharfbuzz`), et `sips`, fourni avec macOS.

`marque/planche-identite.png` et les images de `documentation/images/` ne sont produites par aucun script du dépôt : les refaire à la main après un changement de nom, de couleur ou de symbole.

## Photos

Pour ajouter ou remplacer une photo : la mettre dans `photos-sources/`, ajouter ou modifier son entrée dans `photos-sources/photos.json` (fichier, texte alternatif, sujet repris dans les crédits, auteur, source, licence, page d'origine ; au besoin un `recadrage` `{"x", "y", "largeur", "hauteur"}` en pixels de la photo d'origine, ou `"variantes": false` pour ne garder que les crédits), puis :

```sh
python3 outils/photos.py
python3 outils/construire.py
```

[`outils/photos.py`](../outils/photos.py) recadre chaque photo si `photos.json` le demande, la décline en AVIF et en WebP à plusieurs largeurs, de 480 à 1600 px, sans métadonnées, et écrit `src/images/photos.json`, que le générateur lit. Les crédits sont repris dans les mentions légales. Il faut `sips` (fourni avec macOS), `cwebp` et `avifenc` (`brew install webp libavif`).

La capture `tableau-de-bord` reprend `captures/home-assistant.png` de mon dépôt [homelab](https://github.com/antoninche/homelab). Avant d'ajouter une photo trouvée en ligne : vérifier la licence, et refuser les visages reconnaissables, les logos et les marques.

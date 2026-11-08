# Configuration

Les informations qui changent (nom, coordonnées, immatriculation, médiateur, hébergeur, prix) sont toutes dans [`site.json`](../site.json). Les textes sont dans [`src/pages/`](../src/pages/).

Les lignes de statut, de SIREN et de TVA n'apparaissent que lorsque `entreprise.siren` est rempli. Dans la version de travail, les informations obligatoires absentes sont surlignées en hachuré là où elles s'affichent (mentions légales, conditions générales, données personnelles) et listées à la fin de la construction. `entreprise.siren` et `site.url` ne s'affichent que remplis : ils n'apparaissent pas dans cette liste. Seule la construction avec `--publication` donne la liste complète, avec les contrôles de la mention « EI » et de l'activité.

## L'offre affichée

- Diagnostic à domicile, environ une heure : une page de compte rendu et une proposition d'installation chiffrée.
- Installation complète, sur devis : mise en service jusqu'à `prix.appareils_inclus` appareils, puis `prix.appareil_sup` par appareil en plus, et chaque fonction en plus à partir de `prix.fonction_sup`.
- Suivi annuel, sans reconduction : deux mises à jour, le contrôle des sauvegardes et une réponse par e-mail ; l'aide se paie à part.
- Une ligne pour l'aide ponctuelle (à distance, ou à l'heure à domicile).

Le premier contact se fait par e-mail : aucun numéro de téléphone dans les boutons ni dans l'en-tête. La loi impose quand même un numéro dans les mentions légales et les conditions générales : il y figure.

## Où modifier quoi

| Fichier ou dossier | Contenu |
|---|---|
| `site.json` | nom commercial, identité légale, coordonnées, médiateur, hébergeur, prix, abonnement d'accès à distance |
| `src/pages/` | le texte de chaque page (index, usages, tarifs, deroulement, qui-je-suis, questions, devis, cgv, mentions-legales, confidentialite, 404) |
| `src/partiels/` | les parties communes : tête du document (`tete.html` : meta, Open Graph, script en ligne), en-tête, pied de page, appel final, barre d'action mobile, icônes et logo, texte du paiement (`paiement.html`, repris sur les pages Tarifs, Déroulement et Questions ; les CGV ont leur propre article sur le paiement, à modifier en même temps) |
| `src/css/site.css` | mise en page, couleurs, typographie |
| `src/js/site.js` | coordonnées protégées, menu mobile, en-tête, barre d'action mobile |
| `src/js/devis.js` | formulaire de demande |
| `src/favicon.svg` | le symbole du logo, repris partout ; même dessin que le logo de `src/partiels/icones.html` |
| `photos-sources/` | photos d'origine et leurs crédits (`photos.json`) |
| `marque/` | identité visuelle : charte, planche, logos, déclinaisons du symbole, bannière LinkedIn, textes de présentation |
| `outils/` | construction, photos, visuels, vérifications, gabarits de l'image de partage et de la bannière |
| `docs/` | le site construit, publié par GitHub Pages ; refait à chaque construction, à ne pas modifier à la main |

## Les champs de site.json

| Champ | Rôle |
|---|---|
| `site.nom`, `site.accroche` | nom commercial et sous-titre affichés à côté du logo |
| `site.url` | adresse du site, en https et sans barre finale : `https://antoninche.github.io/centralhome`. Son chemin, `/centralhome/`, sert aux liens de la page 404 |
| `entreprise.nom_legal` | mon nom, suivi de « EI » comme sur l'extrait d'immatriculation (« Antonin Chenavaz EI ») : la publication l'exige |
| `entreprise.prenom`, `entreprise.nom` | mon prénom et mon nom : directeur de la publication, signature du pied de page, pages Accueil et Qui je suis (avec les initiales du monogramme), formule d'appel du message préparé par le formulaire |
| `entreprise.ville` | ville de l'adresse dans les données structurées `LocalBusiness` de la version publiée |
| `entreprise.siren` | numéro SIREN à 9 chiffres (le script vérifie sa clé) ; vide, les lignes d'immatriculation et de TVA restent cachées |
| `entreprise.tva_intracom` | seulement si un numéro de TVA intracommunautaire a été attribué |
| `entreprise.activite` | « commerciale », « artisanale » ou « libérale », comme sur l'extrait d'immatriculation ; si elle est commerciale, `entreprise.rcs` devient obligatoire |
| `entreprise.registre`, `entreprise.rcs` | registre d'immatriculation ; si l'activité est commerciale, `rcs` vaut par exemple « RCS Marseille » |
| `entreprise.adresse` | adresse de l'entreprise, ou de sa domiciliation |
| `assurance.*` | assureur et couverture de la RC Pro ; vide, rien ne s'affiche |
| `contact.telephone`, `contact.email` | coordonnées professionnelles ; le numéro n'apparaît que dans les mentions légales et les CGV |
| `contact.delai_reponse` | délai de réponse affiché partout |
| `mediateur.*` | nom, adresse postale et site du médiateur de la consommation |
| `hebergeur.*` | nom, adresse et téléphone de l'hébergeur, GitHub, Inc. |
| `donnees.prestataires` | fournisseur de ma messagerie, cité dans la page sur les données et à l'article 11 des CGV |
| `liens.*` | GitHub, site personnel, LinkedIn ; un champ vide fait disparaître son lien |
| `prix.diagnostic`, `prix.mise_en_service`, `prix.appareils_inclus`, `prix.appareil_sup`, `prix.fonction_sup`, `prix.automatismes_inclus` | l'offre principale |
| `prix.suivi`, `prix.aide_distance`, `prix.heure_domicile_premiere`, `prix.heure_domicile_suivante` | suivi et aide ponctuelle |
| `prix.boitier`, `prix.cle_radio`, `prix.materiel_date` | prix publics du matériel et date du relevé |
| `prix.exemple_appareils` | nombre d'appareils de l'exemple de budget de la page Tarifs, dont le total est calculé |
| `tiers.*` | nom et prix de l'abonnement d'accès à distance de Nabu Casa |
| `annonce` | bandeau facultatif en haut des pages, par exemple « Période d'examens : je réponds sous 7 jours. » |
| `date_maj_textes` | date de dernière mise à jour, affichée en haut des mentions légales, des CGV et de la page sur les données |

## Le formulaire de demande

Le visiteur donne son prénom, sa commune et son adresse e-mail, choisit entre un diagnostic, une question ou le suivi, et peut décrire son logement. GitHub Pages ne fait tourner aucun script serveur : le formulaire n'envoie rien lui-même. `src/js/devis.js` vérifie les champs, rédige la demande et ouvre la messagerie du visiteur avec l'objet et le message déjà remplis. La demande reste affichée sous le formulaire, avec un bouton pour la copier et l'adresse à laquelle l'envoyer, au cas où aucune messagerie ne s'ouvre. Je réponds par e-mail.

Une demande peut être présélectionnée depuis une autre page : `devis.html?demande=diagnostic`, `question` ou `suivi`.

## Numéro et adresse e-mail protégés

Le script de construction retire le numéro et l'adresse e-mail du code HTML, pour les robots qui les y cherchent. Dans le texte, la coordonnée est coupée en deux attributs que la feuille de styles affiche, même sans JavaScript ; `src/js/site.js` remet ensuite le texte réel, pour le copier-coller et les lecteurs d'écran. Les liens `tel:` et `mailto:` sont encodés dans un attribut `data-lien` et rétablis par le même script ; sans JavaScript, ils mènent à la page de demande. Le formulaire lit l'adresse encodée dans son attribut `data-courriel`.

L'adresse reste lisible dans l'attribut `action` du formulaire (`mailto:`), pour que la demande parte aussi sans JavaScript. Une personne ou un outil qui lit la page affichée voit quand même ces coordonnées : le numéro publié est donc celui d'une ligne professionnelle.

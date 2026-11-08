# Charte graphique CentralHome

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo-horizontal-blanc.svg">
  <img src="logo-horizontal.svg" alt="CentralHome" width="260">
</picture>

Vue d'ensemble : [planche d'identité](planche-identite.png).

## Le symbole

Une pièce vue depuis l'entrée : le plafond, les murs et le sol mènent au mur du fond, blanc, au centre exact. Tout ce qui est dans la pièce mène au même point, comme chaque appareil mène au boîtier. Le sol en terre cuite rappelle la tomette des appartements marseillais.

## Les fichiers

| Fichier | Usage |
|---|---|
| [`symbole.svg`](symbole.svg) | le symbole seul, coins arrondis |
| [`symbole-carre.svg`](symbole-carre.svg), [`logo-linkedin-400.png`](logo-linkedin-400.png) | plein cadre, pour LinkedIn et l'icône d'écran d'accueil : la plateforme arrondit les coins elle-même |
| [`symbole-sur-bleu.svg`](symbole-sur-bleu.svg) | sur un fond bleu, avec un liseré blanc |
| [`symbole-une-couleur.svg`](symbole-une-couleur.svg) | tampon, gravure, broderie |
| [`logo-horizontal.svg`](logo-horizontal.svg), [`.png`](logo-horizontal.png) | symbole et nom, sur fond clair |
| [`logo-horizontal-blanc.svg`](logo-horizontal-blanc.svg), [`.png`](logo-horizontal-blanc.png) | symbole et nom, sur fond foncé |
| [`banniere-linkedin-1512x256.png`](banniere-linkedin-1512x256.png) | image de couverture de la page LinkedIn |

Dans les logos `.svg`, le nom est dessiné en tracés : ils s'affichent partout, sans la police.

## Les couleurs

| Couleur | Code | Usage |
|---|---|---|
| Bleu texte | `#0369A1` | murs du symbole, « Home », surtitres, liens |
| Bleu plafond | `#0288D1` | plafond du symbole, pointillés de l'illustration ; jamais pour du texte |
| Bleu boutons | `#0277BD` | boutons, pastilles d'appareils |
| Terre cuite | `#C0603C` | sol du symbole et de l'illustration ; jamais pour du texte ni un bouton |
| Mur du fond | `#FFFFFF` | centre du symbole, boîtier, cartes ; toujours le plus clair |
| Marine | `#0B1E2D` | « Central », titres |
| Texte | `#23384A` | texte courant |
| Fond | `#F5F8FB` | fond des pages |
| Fond sombre | `#0B131B` | fond du mode sombre |
| Bleu sombre | `#4FC3F7` | « Home », boutons et surtitres du mode sombre ; jamais sur fond clair |
| Liens sombre | `#7DD3FC` | liens du mode sombre |
| Bleu vif | `#03A9F4` | halo et décor seulement |

## La typographie

Inter, seule police, celle du site. Le nom s'écrit en un seul mot, en graisse 700 : « Central » en marine et « Home » en bleu texte, ou en blanc et bleu sombre sur fond foncé.

## Les règles

| Règle | Valeur |
|---|---|
| Espace libre | autour du logo, au moins la largeur du mur du fond, soit 18 px pour un logo de 48 px de haut |
| Taille minimale du symbole | 16 px à l'écran, 6 mm imprimé |
| Taille minimale du logo avec le nom | 28 px de haut, 10 mm imprimé ; en dessous, le symbole seul |
| Fond blanc ou clair | `logo-horizontal` |
| Fond foncé | `logo-horizontal-blanc` |
| Fond bleu | `symbole-sur-bleu`, avec le nom en blanc |

À éviter :

- changer ou échanger les couleurs des pans ;
- ajouter un dégradé, une ombre ou du relief ;
- mettre quoi que ce soit dans le mur du fond, comme un œil, un objectif ou une ampoule, qui évoquerait la surveillance ;
- écrire « Central Home » en deux mots ;
- déformer, pivoter ou recadrer le symbole ;
- poser le logo sur une photo chargée.

## La trame et l'illustration

La trame est faite de petits carrés de 2,8 px tous les 22 px, comme le mur du fond, en `#0277BD` à 34 % (en blanc à 20 % sur un fond bleu). Elle habille le haut des pages, l'appel final, la bannière et l'image de partage.

L'illustration, `src/images/illustration.svg`, reprend la pièce du symbole en grand, avec le boîtier au centre, relié à la lumière, au chauffage, à la consommation électrique et à un détecteur de fuite. Un seul fichier sert pour le mode clair et le mode sombre.

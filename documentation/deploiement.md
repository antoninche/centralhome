# Vérifications et déploiement

## Vérifier le site

```sh
python3 outils/construire.py
python3 outils/verifier.py /chemin/vers/axe.min.js
```

[`outils/verifier.py`](../outils/verifier.py) sert `docs/` en local comme GitHub Pages : sous le chemin du site (`/centralhome/`), avec la page 404 pour toute adresse inconnue. Il ouvre chaque page dans Google Chrome, piloté par Playwright, et lance axe-core (WCAG 2.0, 2.1 et 2.2, niveaux A et AA) en thème clair et sombre, sur ordinateur (1440 px) et sur mobile (390 px), soit 44 combinaisons. Comme la politique de sécurité est déclarée dans les pages, elle s'applique aussi pendant la vérification : une violation apparaît parmi les erreurs de console.

Il relève aussi les débordements horizontaux, remplit le formulaire comme un visiteur et vérifie le message préparé, contrôle le lien d'évitement au clavier, l'ouverture du menu mobile et sa fermeture par Échap, puis ouvre une adresse inconnue pour vérifier la page 404 et ses styles. Le résumé s'affiche à l'écran et le détail est écrit dans `outils/verification/resultats.json`, qui n'est pas suivi par Git ; le script se termine avec le code 0 même quand il relève des problèmes.

Il demande Playwright, Google Chrome et axe-core (`npm install axe-core@4` dans un dossier à part). Il complète les essais faits à la main avec VoiceOver et sur un vrai téléphone.

## Déployer

GitHub Pages publie le dossier `docs/` de la branche `main` sur https://antoninche.github.io/centralhome/. Pour mettre le site à jour :

1. Modifier `site.json` ou les fichiers de `src/`.
2. `python3 outils/construire.py --publication` : la construction refuse de remplacer `docs/` tant qu'il manque une information obligatoire, la mention « EI » ou les conditions générales.
3. `python3 outils/verifier.py /chemin/vers/axe.min.js`.
4. Commit et push : GitHub Pages publie la nouvelle version en une à deux minutes.

Après un changement de nom commercial ou de symbole, relancer d'abord `outils/visuels.py` (voir [Visuels et photos](visuels.md)).

Le formulaire n'a besoin d'aucun serveur : il prépare un e-mail dans la messagerie du visiteur. Le site ne dépose aucun cookie et ne charge rien depuis un autre domaine.

---
name: bonhomme-blanc
description: Crée des vidéos MP4 animées dans le style « bonhomme blanc » — fond noir, personnage blanc minimaliste lumineux sous un projecteur, compteurs qui défilent, gros mots qui claquent, barres de progression, pluie de billets, grain de film. À utiliser dès que l'utilisateur envoie des images (storyboard, captures, photos, croquis) ou un texte/script et demande une vidéo « comme celles-ci », « style bonhomme blanc », « même visuel / même concept », une vidéo motivation/business/storytelling minimaliste noir et blanc, ou veut modifier une vidéo déjà faite avec ce skill.
---

# Bonhomme blanc — vidéos minimalistes noir & blanc

Ce skill transforme les images (ou le texte) de l'utilisateur en une vidéo MP4 animée.
Tu écris un fichier `scene.json`, le moteur (`engine/engine.js`) le dessine image par image
dans Chromium et `scripts/render.js` l'encode avec ffmpeg. Tout est déterministe : même JSON = même vidéo.

## Déroulé

1. **Regarde chaque image** envoyée (outil Read). Pour chacune, note : l'idée, les textes, les chiffres,
   les objets, l'émotion. Décide de son rôle :
   - **storyboard / inspiration** (cas par défaut) → tu la *redessines* avec les éléments du moteur ;
   - **image à montrer telle quelle** (photo produit, capture d'écran, visage) → élément `image`
     ou `monitor` avec `content: "image"` : elle passe automatiquement en noir et blanc dans un cadre lumineux.
   Si l'utilisateur ne donne que des images sans texte, déduis toi-même l'histoire et avance ; ne pose une
   question que si le message de la vidéo est vraiment indevinable.
2. **Écris le découpage** : une ligne par scène (durée, phrase à l'écran, métaphore visuelle). Une image
   de l'utilisateur = en général une scène. Suis la structure narrative ci-dessous.
3. **Écris `scene.json`** dans le dossier de travail (ex. `videos/<nom>/scene.json`, images copiées à côté).
   Référence complète des éléments : `reference/elements.md`. Exemples complets : `examples/demo.json`
   (16:9, business) et `examples/mariage.json` (9:16, histoire à personnages + quiz « A ou B » avec chrono).
4. **Vérifie avant le rendu complet** — une image fixe par scène, que tu regardes avec Read :
   `node <skill>/scripts/render.js scene.json --still 12.5 /chemin/scratch/s.jpg`
   Corrige chevauchements, textes coupés, éléments hors cadre.
5. **Rendu final** (≈ 5 s de calcul par seconde de vidéo — lance-le en arrière-plan au-delà de 20 s de vidéo) :
   `node <skill>/scripts/render.js scene.json -o video.mp4 --sheet planche.jpg`
   Regarde la planche contact, puis envoie le MP4 à l'utilisateur (SendUserFile).

Options de `render.js` : `--audio musique.mp3` (ajoute une bande-son fournie par l'utilisateur),
`--scale 0.5` (brouillon rapide), `--from 10 --to 20` (un extrait), `--still t fichier` (une image).
Le skill ne génère ni voix ni musique : dis-le et propose `--audio` si l'utilisateur fournit un fichier.

Prérequis : `node`, `playwright` (Chromium) et `ffmpeg`. La police Inter est utilisée si elle est installée.

## Règles du style (à respecter strictement)

- **Noir et blanc uniquement.** Fond noir, formes blanches, gris pour le secondaire. Jamais de couleur.
- **Une seule idée par scène**, 2 à 6 secondes. Beaucoup de vide autour des éléments.
- **Texte : MAJUSCULES, très court** (1 à 5 mots), gras, lettres espacées. Le moteur met en majuscules.
  Accroche = mots géants qui claquent un par un (`in: "slam"`), chacun remplaçant le précédent.
- **Le bonhomme** : tête ronde + corps en pion, sans visage. Dans les scènes « histoire », toujours avec
  `ground` (ligne pointillée) + `spotlight` (projecteur) et son anneau au sol. Il exprime tout par la pose :
  `work` (acharné au bureau), `stand` (attente), `cheer` (victoire), `phone` (distraction), `point`,
  `sit` (immobile), `run` (passage à l'action), `fallen` (échec). `ghost: true` = version fantôme en contour
  (le « toi possible », les autres, le passé).
- **Tout chiffre bouge** : `counter` qui défile (`ease: "inExpo"` pour une explosion finale, `"in"` pour une
  lente accumulation), `progress` qui se remplit, `tiles` qui s'allument une à une, `chart` qui se trace.
- **Métaphores visuelles plutôt que phrases** : barre bloquée à 99 % = procrastination ; cadenas = blocage ;
  escalier = progression ; courbe exponentielle = effet cumulé ; dents de scie = abandons répétés ;
  feu tricolore = permission ; pile + pluie de billets = réussite ; foule + bulles = regard des autres ;
  batterie = motivation ; horloge = impatience.
- **Rythme** : `transition: "flash"` sur les moments forts (éclair gris + coup de zoom), `"fade"` pour une
  ellipse de temps, coupe franche sinon. Un léger zoom lent est appliqué automatiquement à chaque scène.
- **Structure type (45–90 s)** : 1) accroche en mots qui claquent ou image du succès final → 2) retour à zéro,
  le problème → 3) la traversée du désert (compteur de jours, `$0` répétés) → 4) le déclic / la leçon →
  5) la récompense (compteur qui explose, billets, `cheer`) → 6) phrase finale en `slam`.

## Format de `scene.json`

```json
{
  "format": "16:9",
  "fps": 30,
  "images": { "photo1": "mes-images/photo1.jpg" },
  "scenes": [
    {
      "duration": 5,
      "transition": "flash",
      "elements": [
        { "type": "spotlight", "x": 420, "y": 820 },
        { "type": "ground", "y": 820 },
        { "type": "workstation", "x": 420, "y": 820, "scale": 1.5,
          "pose": [[0, "work"], [3.2, "cheer"]] },
        { "type": "counter", "x": 1400, "y": 260, "label": "Net worth", "prefix": "$",
          "from": 0, "to": 1009400, "start": 0.3, "dur": 4, "ease": "inExpo" }
      ]
    }
  ]
}
```

- `format` : `"16:9"` → repère 1920×1080 (YouTube) ; `"9:16"` → 1080×1920 (TikTok/Reels/Shorts) ;
  `"1:1"` → 1080×1080. Demande le format s'il n'est pas évident ; sinon 16:9.
- Coordonnées en pixels dans ce repère, origine en haut à gauche. Les éléments sont dessinés dans l'ordre
  du tableau (le dernier passe devant).
- **Temps** : toujours en secondes *depuis le début de la scène*.
- **Toute propriété numérique peut être animée** par des keyframes `[[t, valeur, "ease"], ...]`
  (ease : `linear`, `in`, `out`, `inOut`, `outBack`, `inExpo`, `outExpo`), ex. `"x": [[0, 300], [2, 900, "out"]]`.
  Les propriétés texte (comme `pose`) acceptent des paliers : `[[0, "work"], [3, "cheer"]]`.
- Propriétés communes : `x`, `y`, `scale`, `rot`, `alpha`, `at` (apparition), `until` (disparition),
  `in` (`fade` | `pop` | `slam` | `up` | `type` | `none`), `inDur`, `out: "blur"`, `outDur`.
- Scène : `duration`, `transition` (`cut` | `flash` | `fade`), `camera` `{zoom, x, y}` (animables),
  `flashes: [1.2, 3]` (éclairs supplémentaires), `backdrop` (0–1, lueur du fond).
- Global : `bloom` (halo, défaut 1), `grain` (défaut 1), `dots: false` (retire la grille de points),
  `locale` (`"fr-FR"` pour des nombres à la française), `audio`.

## Repères de mise en page

| | 16:9 (1920×1080) | 9:16 (1080×1920) |
|---|---|---|
| Sol (`ground.y`, pieds du bonhomme) | 820–880 | 1250–1400 |
| Bonhomme principal `scale` | 1.2–1.6 | 1.3–1.8 |
| Titre géant `size` | 150–210 | 110–150 (retours à la ligne `\n`) |
| Sous-titre `caption.size` | 24–54 | 28–48 |
| Compteur en haut | y ≈ 170–300 | y ≈ 300–450 |
| Marges de sécurité | 100 px | 90 px côtés, 220 px haut/bas |

Le bonhomme mesure environ 230 × `scale` px de haut et 140 × `scale` de large ; `workstation` occupe
≈ 520 × `scale` de large vers la droite et 430 × `scale` de haut. Vérifie toujours avec `--still`.

## Pièges

- Un texte long en `slam` déborde : au-delà de ~9 caractères à `size` 210 en 16:9, réduis ou coupe en deux mots.
- Deux éléments au même endroit au même moment : utilise `until` sur le premier et `at` sur le second.
- Un type inconnu est ignoré (le script l'affiche en avertissement) : n'invente pas de types, compose avec
  `shape`, `line`, `icon`, `text`.
- Les dessins de l'utilisateur ont souvent des visages et de la couleur : ne les reproduis pas. L'émotion passe
  par la pose, `marks`, `shake` et les bulles ; un « A vert / B rouge » devient deux cadres blancs.
- S'il manque un objet (ex. arche, chrono), ajoute-le proprement au moteur (`engine/engine.js`, table `DRAW`)
  et documente-le dans `reference/elements.md`, plutôt que de bricoler.
- N'ajoute pas de couleur, d'emoji ni de dégradé coloré : cela casse immédiatement le style.

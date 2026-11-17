# Guide du style « bonhomme blanc »

Vidéo d'animation minimaliste : fond noir, personnages blancs lumineux en forme de pion (tête ronde, corps
arrondi, sans visage), projecteur, halo, grain de film. Tout est décrit dans un **scénario JSON** que le moteur
du Studio dessine image par image.

## Règles du style (strictes)

- **Noir et blanc uniquement.** Fond noir, formes blanches, gris pour le secondaire. Jamais de couleur, d'emoji.
- **Une seule idée par scène**, 2 à 6 secondes. Beaucoup de vide autour des éléments.
- **Texte : MAJUSCULES, très court** (1 à 5 mots), gras, lettres espacées (le moteur met en majuscules).
  Accroche = mots géants qui claquent un par un (`in: "slam"`), chacun remplaçant le précédent
  (`until` + `out: "blur"` sur le premier, `at` sur le suivant).
- **Le bonhomme** : dans les scènes « histoire », toujours avec `ground` (ligne pointillée) + `spotlight`
  (projecteur, placé AVANT le personnage dans la liste). Il exprime tout par la pose :
  `work` (acharné au bureau), `stand` (attente), `cheer` (victoire), `phone` (distraction), `point`,
  `sit` (immobile), `run` (passage à l'action), `fallen` (échec), `worry` (mains au visage), `refuse`
  (paume en avant), `give` (tend une bague). `ghost: true` = version fantôme en contour (le « toi possible »).
  Rôles : `dress: true` (mariée / personnage féminin), `bowtie: true` (marié, costume), `book: true` (officiant).
  Émotions : `marks` = `joy`, `shock`, `sweat`, `scribble` (confusion) ; `shake` = tremblement (2–4).
- **Tout chiffre bouge** : `counter` qui défile (`ease: "inExpo"` pour une explosion finale, `"in"` pour une
  lente accumulation), `progress` qui se remplit, `tiles` qui s'allument une à une, `chart` qui se trace,
  `timer` qui décompte.
- **Métaphores visuelles plutôt que phrases** : barre bloquée à 99 % = procrastination ; cadenas = blocage ;
  escalier = progression ; courbe exponentielle = effet cumulé ; dents de scie = abandons répétés ;
  feu tricolore = permission ; pile + pluie de billets = réussite ; foule + bulles = regard des autres ;
  batterie = motivation ; horloge = impatience ; chrono = choix à faire maintenant.
- **Rythme** : `transition: "flash"` sur les moments forts (éclair + coup de zoom), `"fade"` pour une ellipse
  de temps, coupe franche sinon. Un léger zoom lent est appliqué automatiquement à chaque scène.
- **Structure type (30–90 s)** : 1) accroche en mots qui claquent → 2) la situation, le problème →
  3) la tension / la traversée du désert → 4) le déclic → 5) la récompense ou la question → 6) phrase finale
  en `slam`. Pour un quiz : dernière scène « A ou B ? » avec deux cadres (`shape`), une lettre en `slam` dans
  chacun, une mini-scène dans chacun, et un `timer` de 5 secondes.

## Transformer les images de l'utilisateur

- Par défaut, une image = une scène que tu **redessines** avec les éléments du moteur. Décris d'abord ce que
  tu vois (personnages, émotions, objets, textes, chiffres), puis traduis.
- Les dessins ont souvent des visages et de la couleur : ne les reproduis pas. L'émotion passe par la pose,
  `marks`, `shake` et les bulles (`bubble`). Un « A vert / B rouge » devient deux cadres blancs.
- Pour montrer une image telle quelle (capture d'écran, photo produit) : élément `image` (elle est passée
  automatiquement en noir et blanc dans un cadre lumineux) ou `workstation` / `monitor` avec
  `content: "image"`. Déclare-la dans `"images": { "cle": "nom-du-fichier.png" }`.
- S'il manque un objet, compose-le avec `shape`, `line`, `icon`, `text`, `bubble`. N'invente pas de type.

## Format du scénario

```json
{
  "title": "mon-histoire",
  "format": "9:16",
  "fps": 30,
  "images": { "photo1": "photo1.png" },
  "scenes": [
    {
      "duration": 5,
      "transition": "flash",
      "elements": [
        { "type": "spotlight", "x": 540, "y": 1300 },
        { "type": "ground", "y": 1300 },
        { "type": "character", "x": 300, "y": 1300, "scale": 1.5, "bowtie": true,
          "pose": [[0, "stand"], [3, "cheer"]], "marks": "joy" },
        { "type": "text", "text": "IL DIT OUI.", "size": 110, "x": 540, "y": 400, "in": "slam", "at": 0.3 }
      ]
    }
  ]
}
```

- `format` : `"16:9"` → repère 1920×1080 (YouTube) ; `"9:16"` → 1080×1920 (TikTok/Reels/Shorts) ;
  `"1:1"` → 1080×1080.
- Coordonnées en pixels dans ce repère, origine en haut à gauche. Les éléments sont dessinés dans l'ordre
  du tableau (le dernier passe devant). Pour un personnage, `x`,`y` = ses pieds.
- **Temps** : toujours en secondes depuis le début de la scène.
- **Toute propriété numérique peut être animée** : `[[t, valeur, "ease"], ...]`
  (ease : `linear`, `in`, `out`, `inOut`, `outBack`, `inExpo`, `outExpo`), ex. `"x": [[0, 300], [2, 900, "out"]]`.
  Les propriétés texte (`pose`, `marks`) acceptent des paliers : `[[0, "work"], [3, "cheer"]]`.
- Propriétés communes : `x`, `y`, `scale`, `rot`, `alpha`, `at` (apparition), `until` (disparition),
  `in` (`fade` | `pop` | `slam` | `up` | `type` | `none`), `inDur`, `out: "blur"`, `outDur`.
- Scène : `duration`, `transition` (`cut` | `flash` | `fade`), `camera` `{zoom, x, y}` (animables),
  `flashes: [1.2, 3]` (éclairs supplémentaires), `backdrop` (0–1, lueur du fond).
- Global : `title`, `bloom` (halo, défaut 1), `grain` (défaut 1), `dots: false`, `locale: "fr-FR"`
  (nombres à la française).

## Repères de mise en page

| | 16:9 (1920×1080) | 9:16 (1080×1920) |
|---|---|---|
| Sol (`ground.y`, pieds du bonhomme) | 820–880 | 1250–1400 |
| Bonhomme principal `scale` | 1.2–1.6 | 1.3–1.8 |
| Titre géant `size` | 150–210 | 100–150 (retours à la ligne `\n`) |
| Sous-titre `caption.size` | 24–54 | 26–56 |
| Compteur / titre en haut | y ≈ 170–300 | y ≈ 200–450 |
| Marges de sécurité | 100 px | 90 px côtés, 180 px haut/bas |

Le bonhomme mesure environ 230 × `scale` px de haut et 140 × `scale` de large (bras compris : ~300 × `scale`
en `cheer`, ~220 × `scale` vers l'avant en `give`/`work`). `workstation` occupe ≈ 520 × `scale` de large
vers la droite et 430 × `scale` de haut. Garde au moins 250 × `scale` px entre deux personnages côte à côte.
Une largeur de texte vaut à peu près : nombre de caractères × `size` × 0,75.

## Pièges

- Un texte long en `slam` déborde : au-delà de ~9 caractères à `size` 210 en 16:9 (ou ~8 à `size` 130 en 9:16),
  réduis ou coupe en deux lignes avec `\n`.
- Deux éléments au même endroit au même moment : `until` sur le premier, `at` sur le second.
- Une bulle (`bubble`) se place au-dessus de la tête : y ≈ pieds − 330 × `scale`.
- N'ajoute pas de couleur, d'emoji ni de dégradé coloré : cela casse immédiatement le style.

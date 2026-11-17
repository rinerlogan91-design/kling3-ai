# Référence des éléments

Toutes les propriétés numériques sont animables par keyframes `[[t, valeur, "ease"], ...]`.
Propriétés communes à tous : `x`, `y`, `scale`, `rot`, `alpha`, `at`, `until`, `in`, `inDur`, `out`, `outDur`.
`x`/`y` par défaut = centre de l'image. Sauf mention contraire, `x`,`y` désignent le **centre** de l'élément.

## Animations d'entrée (`in`)

| Valeur | Effet | Usage |
|---|---|---|
| `fade` (défaut) | fondu | décor, éléments secondaires |
| `slam` | arrive en grand + flou, se pose net, éclair gris sur tout l'écran | mots-chocs, icône clé |
| `pop` | rebond élastique | bulles, icônes, étiquettes |
| `up` | glisse vers le haut | sous-titres, barres |
| `type` | machine à écrire | phrases de narration (`text` / `caption`) |
| `none` | apparition sèche | remplacement instantané |

`out: "blur"` avec `until` : l'élément part en flou (utile entre deux mots `slam`).

## Personnage

### `character` — origine = pieds
| Prop | Défaut | |
|---|---|---|
| `pose` | `stand` | `stand`, `cheer`, `work`, `point`, `phone`, `sit`, `run`, `fallen` — ou paliers `[[0,"work"],[3,"cheer"]]` |
| `scale` | 1 | ≈ 230 px de haut à 1 |
| `glow` | 0.6 | intensité du halo (1–1.3 pour un moment de gloire, 0 pour un figurant) |
| `ghost` | false | contour seul, sans remplissage |
| `ring` | true | anneau pointillé au sol |
| `facing` | 1 | −1 pour le retourner |
| `dress` | false | robe + voile + chignon (mariée, personnage féminin) |
| `bowtie` | false | nœud papillon noir (marié, personnage habillé) |
| `book` | false | livre ouvert tenu devant lui (officiant, professeur) |
| `marks` | — | émotion au-dessus de la tête : `joy`, `shock`, `sweat`, `scribble` (confusion) — paliers possibles |
| `shake` | 0 | tremblement en px (2–4 = nervosité) |

Poses supplémentaires : `worry` (mains au visage), `refuse` (bras tendu, paume en avant), `give` (tend un écrin avec une bague).

Pour `sit`, `y` est la hauteur de l'assise. Pour le faire marcher : anime `x` avec `pose: "run"`.

### `workstation` — bonhomme + bureau + écran alignés, origine = pieds du bonhomme
Mêmes props que `character` (`pose` par défaut `work`) + celles de `monitor` (`content`, `label`, `value`…).
Centre de l'écran ≈ (`x` + 318×scale, `y` − 261×scale) — pratique pour y poser un `icon` `check`.

### `crowd` — rangée de petits bonshommes
`count` (10), `gap` (80), `size` (0.26), `alpha`, `pose`, `marks` (ex. `shock` pour une foule choquée). `y` = pieds.

## Décor

| Type | Props | Notes |
|---|---|---|
| `ground` | `y`, `solid` | ligne pointillée sur toute la largeur |
| `spotlight` | `x`, `y` (sol), `width` (440), `topWidth` (110), `power` (1) | cône de lumière venant du haut ; à placer avant le personnage |
| `desk` | `x` (bord gauche), `y` (sol), `w` (430), `h` (150) | |
| `window` | `w`, `h` (200), `moon` | fenêtre avec lune = nuit, travail tardif |
| `arch` | `x`,`y` (centre au sol), `w` (760), `h` (980) | arche fleurie (mariage, cérémonie) |
| `rings` | `count` (3), `maxR` (320), `period` (2.4), `static` | ondes concentriques derrière un mot ou un personnage |

## Texte et chiffres

### `text` / `caption`
`text` (avec `\n` pour les lignes), `size` (120 / 34), `weight` (900 / 800), `spacing` (0.05 / 0.2),
`align` (`center`), `glow` (1 / 0.5), `color` (`#fff`, ou `#8a8a8a` pour du gris), `upper: false` pour garder la casse.

### `counter` — nombre qui défile
`label`, `from`, `to`, `start` (s), `dur` (s), `ease`, `prefix` (`"$"`), `suffix` (`" €"`, `"×"`), `decimals`, `size` (96).
Ou `value` fixe (nombre ou texte).

### `progress` — barre de progression
`w` (640), `h` (28), `value` (0–1), `label`, `tag` (ex. `"STUCK"`, affiché à droite), `percent: false`.

### `tiles` — rangée/grille de cases qui s'allument
`count` (7), `cols`, `w` (74), `h` (58), `gap` (16), `text` (`"$0"`), `progress` (nombre de cases allumées),
`highlight` (index mis en lumière), `hideEmpty`. `x` = centre horizontal, `y` = haut de la grille.

### `chart` — origine = coin bas-gauche des axes
`w` (700), `h` (420), `title`.
- Barres : `bars: [{ "label": "Year 1", "text": "$0", "value": 0 }]` (`value` 0–1), `reveal` (nb de barres visibles), `grow`.
- `saw` (0–1) : dents de scie le long de l'axe (essais abandonnés).
- `curve` (0–1) : courbe exponentielle qui se trace, avec un mini-bonhomme au bout (`rider: false` pour l'enlever).

### `stairs` — origine = bas-gauche
`steps` (7), `stepW` (110), `stepH` (62), `lead` (150), `progress` (tracé 0–1),
`climber` (0 → `steps` : position du mini-bonhomme qui grimpe par bonds).

## Objets

### `monitor`
`w` (340), `h` (210), `stand`, `glow`, `content` :
- `editor` (montage vidéo avec tête de lecture), `code` (lignes qui s'écrivent), `play` (lecteur),
- `value` + `label` + `value` texte **ou** `from`/`to`/`start`/`dur`/`prefix` (compteur dans l'écran), `loading: true`,
- `image` + `src` (clé de `images`).

### `image` — image de l'utilisateur dans un cadre lumineux
`src` (clé déclarée dans `"images"` à la racine), `w` (520), `h` (320), `r`, `frame: false`,
`contrast` (1.35), `brightness` (0.92), `color: true` pour ne **pas** la passer en noir et blanc (à éviter).
L'image est recadrée pour remplir le cadre (cover). Formats : png, jpg, webp, gif.

### `icon`
`name` : `lock`, `unlock`, `warning`, `check`, `cross`, `clock` (aiguilles animées, `speed`), `briefcase`,
`play`, `dollar`, `search`, `battery` (`level` 0–1), `people`, `city`, `arrow`, `heart`, `star`, `bulb`, `ring` (bague), `flower`.
`size` (140), `label` (texte dessous), `glow`.

### `card` — carte encadrée
`w`, `h` (190), `icon`, `label`, `tag` (étiquette blanche, ex. `"SAME"`).

### `bubble` — bulle de dialogue
`text`, `size` (22), `tail` (`left` | `right` | `none`).

### `money`
- `mode: "rain"` : `x`,`y` = coin haut-gauche de la zone, `w`, `h`, `count` (40), `intensity` (0–1).
- `mode: "pile"` : `x`,`y` = centre de la base, `rows` (8), `progress` (0–1), `symbol` (`"$"`, `"€"`).

### `trafficlight`
`active` (0 haut, 1 milieu, 2 bas = feu « vert » blanc brillant), `pole`.

### `timer` — chronomètre à rebours
`from` (5), `start` (s), `r` (150). Le chiffre descend d'une unité par seconde jusqu'à 0. Idéal pour un « choisis A ou B ».

### `line` / `shape`
- `line` : `points: [[x,y],…]` (relatifs à `x`,`y`), `progress` (tracé), `width`, `dash`.
- `shape` : `kind` (`rect` | `circle`), `w`, `h`, `r`, `fill` (true ou couleur grise), `stroke: false`, `dash`.

## Recettes

**Mots qui claquent (accroche)**
```json
{ "type": "text", "text": "STOP.", "size": 210, "in": "slam", "at": 0.1, "until": 1.15, "out": "blur" },
{ "type": "text", "text": "WAITING.", "size": 210, "in": "slam", "at": 1.2 }
```

**Le temps passe, rien ne vient**
```json
{ "type": "counter", "x": 1500, "y": 300, "label": "Days", "from": 1, "to": 600, "start": 0.5, "dur": 4.5, "ease": "in" },
{ "type": "tiles", "x": 1500, "y": 480, "count": 7, "text": "$0", "progress": [[1, 0], [5, 7, "linear"]] }
```

**La réussite**
```json
{ "type": "workstation", "x": 380, "y": 860, "scale": 1.4, "pose": [[0, "work"], [3.2, "cheer"]] },
{ "type": "money", "mode": "rain", "x": 1000, "y": 0, "w": 900, "h": 860, "count": 60, "intensity": [[0.3, 0], [3.5, 1, "in"]] },
{ "type": "money", "mode": "pile", "x": 1420, "y": 860, "rows": 9, "progress": [[0.5, 0], [4.5, 1, "in"]] },
{ "type": "counter", "x": 960, "y": 170, "label": "Net worth", "prefix": "$", "from": 398, "to": 1009400, "start": 0.3, "dur": 4.4, "ease": "inExpo", "size": 130 }
```

**Le « toi possible »** : un `character` normal à gauche, un `character` `ghost: true` à droite, une `bubble` « WHAT IF… ».

**Photo de l'utilisateur dans l'écran**
```json
"images": { "shot": "capture.png" },
…
{ "type": "workstation", "x": 420, "y": 820, "scale": 1.5, "content": "image", "src": "shot" }
```

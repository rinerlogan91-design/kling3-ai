# Installer « Bonhomme Blanc » dans ChatGPT

Ce kit crée un **GPT personnalisé** qui transforme vos images en vidéo style « bonhomme blanc ».
ChatGPT écrit la vidéo et vous donne une page « Studio » ; vous l'ouvrez dans votre navigateur et
cliquez **Exporter en MP4**.

Il faut un compte ChatGPT payant (Plus, Pro, Team…) pour créer un GPT personnalisé.
Comptez 5 minutes.

## 1. Créer le GPT

1. Sur ordinateur, allez sur **chatgpt.com** → menu de gauche **GPT** (ou « Explorer les GPT »)
   → bouton **+ Créer** en haut à droite.
2. Ouvrez l'onglet **Configurer** (pas « Créer »).
3. Remplissez :
   - **Nom** : `Bonhomme Blanc`
   - **Description** : `Transforme tes images en vidéo animée minimaliste noir et blanc.`
   - **Instructions** : copiez-collez **tout** le contenu du fichier `instructions-gpt.txt`.
   - **Amorces de conversation** (facultatif) :
     - `Voici mes images, fais-moi une vidéo bonhomme blanc`
     - `Fais une vidéo verticale de 30 s sur ce texte : …`
4. **Connaissances** → **Importer des fichiers** → sélectionnez les **6 fichiers** du dossier
   `fichiers-a-importer` :
   - `bonhomme-blanc-studio.html`
   - `construire_video.py`
   - `guide-style.md`
   - `reference-elements.md`
   - `exemple-mariage.json`
   - `exemple-demo.json`
5. **Fonctionnalités** : cochez **Interpréteur de code et analyse de données** (indispensable).
   Le reste (recherche web, génération d'images) peut rester décoché.
6. Cliquez **Créer** (en haut à droite) → visibilité **Moi uniquement** (ou « Toute personne disposant
   du lien » si vous voulez le partager) → **Enregistrer**.

Le GPT apparaît maintenant dans votre menu de gauche : il est disponible à tout moment.

## 2. Faire une vidéo

1. Ouvrez le GPT **Bonhomme Blanc**, envoyez vos images avec une phrase, par exemple :
   « Fais-moi une vidéo bonhomme blanc avec ces images, format TikTok ».
2. ChatGPT décrit les scènes puis vous donne un lien vers un fichier `.html`.
3. Téléchargez-le et ouvrez-le avec **Chrome, Edge ou Safari** (de préférence sur ordinateur).
4. **▶ Lecture** pour vérifier, puis **Exporter en MP4** : la vidéo arrive dans vos Téléchargements
   (environ 1 à 2 secondes d'attente par seconde de vidéo).
5. Pour changer quelque chose, dites-le simplement à ChatGPT (« la scène 2 est trop longue », « mets le
   texte en anglais »…) : il vous redonne un nouveau fichier.

## Tester tout de suite, sans ChatGPT

Ouvrez `tester-exemple-mariage.html` dans Chrome : c'est la vidéo de mariage déjà prête.
Cliquez **Exporter en MP4** pour vérifier que l'export fonctionne sur votre ordinateur.

## À savoir

- **Pas de son** : ajoutez musique ou voix ensuite dans CapCut, InShot, iMovie…
- **Connexion internet** nécessaire à l'ouverture de la page (police d'écriture et module d'export MP4).
  Sans connexion, la page exporte quand même, en temps réel, au format WebM.
- **Sur téléphone**, l'export marche avec un navigateur récent mais est plus lent ; l'ordinateur est
  plus confortable.
- **ChatGPT ne voit pas le rendu final** : il s'appuie sur des repères de mise en page et sur les
  vérifications automatiques du script. Si un élément se chevauche, signalez-le-lui avec le numéro de
  la scène.
- Dans le Studio, **« Coller ou modifier un scénario »** permet aussi de retoucher le JSON à la main
  ou de coller un scénario que ChatGPT vous a donné en texte.

## Mettre à jour le kit

Le kit est généré à partir du skill Claude (`.claude/skills/bonhomme-blanc/`). Après une modification
du skill : `python3 chatgpt-bonhomme-blanc/source/build.py`, puis remplacez les fichiers de
connaissance du GPT par ceux du dossier `fichiers-a-importer`.

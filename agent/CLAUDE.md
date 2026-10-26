# Hyperframes — montage des vidéos de la personal brand

Ce dossier sert au **montage** des vidéos (face-cam) de la personal brand IA/automatisation.

## 📎 Accès à la stratégie (pont live — toujours à jour)
Le dossier `personal-brand-ref/` est un **pont** vers « My personnal brand ». **Lis-le AVANT de monter :**
- `personal-brand-ref/voice.md` → la voix / le ton (pour les sous-titres, le rythme).
- `personal-brand-ref/brand-profile.md` → marque, cible, garde-fous.
- `personal-brand-ref/content/reel-XX-*.md` → **le script, et rien d'autre** : les phrases dites, ligne par ligne, le mot-clé et la légende. ⚠️ **Depuis le 2026-09-14, sur ordre du créateur, ce fichier ne contient plus AUCUNE indication de montage** — ni timing, ni durée, ni coupe, ni transition, ni effet, ni animation, ni son, ni code couleur, ni brief de cover, ni liste de captures. Le scripting n'est pas expert en montage : **tu es l'expert, tu reçois la vidéo de référence, tu décides.** Le fichier te dit seulement ce qui est dit dans la vidéo.
- `personal-brand-ref/brand-visual-system.md` → **source de vérité visuelle canonique et verrouillée** pour les vidéos, captions, carrousels, stories et sites.

## 🗂️ Organisation (lire `POSTS.md` — c'est l'index maître)
```
1_A-POSTER/AAAA-MM-JJ_slug/     ← monté, pas encore publié (doit rester quasi vide)
2_PUBLIE/AAAA-MM/…              ← archive par mois de publication
ma-video/videos/AAAA-MM-JJ_slug/ ← atelier de montage — MÊME NOM que le dossier du post
ma-video/asset-library/         ← musiques (1-EN-USAGE / 2-LABO), sfx, broll
```
**Nomenclature d'export, non négociable :** `AAAA-MM-JJ_slug-parlant_TYPE.ext`, avec
`_VIDEO.mp4`, `_COUVERTURE.png`, `_COUVERTURE-grille.png`, `_LEGENDE.txt`.
**+ le lead magnet, dans le même dossier du post (règle du 2026-09-30) :** `Guide-MOTCLE-Sujet.pdf`
— il garde son nom public, parce que c'est ce nom que le prospect reçoit en DM. Chaque vidéo a son
guide, fabriqué pendant le montage dans `ma-video/videos/<nom>/lead-magnet/` (source HTML +
`guide-style.css`), copié dans le post par `finish.py`. Le créateur doit trouver au même endroit
tout ce qu'il faut pour poster ET répondre aux DM.
C'est **Hyperframes qui fabrique les ressources** (délégation du 2026-09-30) : elles ne sont plus
copiées dans `personal-brand-ref/` ni dans `dm-messages.md` — on ne sort pas du dossier pour ça.
**Fabrication du guide :**
- Style : copier `personal-brand-ref/content/guide-style.css` (LECTURE seule) dans `lead-magnet/`.
- Structure : s'inspirer des anciens guides `personal-brand-ref/content/ressource-*.html` et `Guide-*.pdf`
  (lecture seule). On n'écrit **jamais** dans `personal-brand-ref/`.
- Contenu : ce qui est **réellement dit dans la vidéo tournée** (transcript), pas le script prévu.
  Chaque affirmation factuelle sur un produit (prix, commande, fonction, disponibilité) est vérifiée
  sur sa **page officielle** ; sinon elle sort du guide.
- Rendu PDF, en ligne de commande (l'extension Chrome refuse les `file://`) :
  `chrome --headless=new --disable-gpu --virtual-time-budget=10000 --no-pdf-header-footer --print-to-pdf="out.pdf" <file-uri>`
- Contrôle avant de dire « fini » : nombre de pages, puis 2-3 pages du PDF **rendues en image**
  avec `pypdfium2` (installé ; `pdftoppm` ne l'est pas) et regardées : rien de coupé, rien qui déborde.
Le nom doit être reconnaissable **isolé**, sans son dossier (galerie du téléphone).
Le dossier de montage et le dossier du post portent le même nom : un seul nom par vidéo.
Après chaque export, ajouter la ligne dans `POSTS.md`.

## 🎬 Workflow
1. L'utilisateur dépose la vidéo filmée dans `ma-video/videos/`.
2. Il ouvre Claude sur CE dossier (Hyperframes), dit quel Reel monter et donne en général une **vidéo de
   référence** virale : tu la décortiques image par image et tu reproduis sa mécanique (phase des reels d'essai,
   depuis le 2026-10-13).
3. Tu lis le `reel-XX-*.md` correspondant dans `personal-brand-ref/content/` + `voice.md`.
4. Tu montes : les affirmations à l'écran viennent de **ce qui est dit dans la vidéo tournée**, **le rythme et la
   mise en forme sont à toi** (ou à la référence).
5. Tu exportes dans `1_A-POSTER/` avec la nomenclature ci-dessus, puis tu mets `POSTS.md` à jour.

## 🧹 Hygiène disque (le projet a atteint 12 Go le 2026-08-30, ramené à 1,2 Go)
Tout ce qui est régénérable ne survit pas à la fin d'un montage. **Avant de dire « terminé », tu supprimes :**
- les caches de frames et dossiers de travail (`exports/`, `render-cache/`, `work-*-*/`) ;
- les frames candidates de couverture (`cover/cand/` — 200 Mo par vidéo) ;
- les snapshots de QC (`snapshots-*/`), les dossiers de version (`v1/`, `v2-…/`) ;
- les renders intermédiaires : **un seul MP4 final survit, et il vit dans le dossier du post** ;
- les `.bak`, les `.log`, les rushes bruts une fois `public/input-video.mp4` découpé.
Ce qui reste dans un projet actif : `public/` (composition + rush découpé + audio), `frame.md`,
`storyboard.json`, `transcript*.json`, `analysis/`. Rien d'autre.
Les scratchs volumineux vont dans `ma-video/temp/`, jamais dans le dossier du projet.

### Cycle de vie d'une vidéo (règle du 2026-09-30)
| État | Signal | Ce qui part à la **corbeille** (jamais `rm`) | Ce qui reste |
|---|---|---|---|
| Validée | le créateur dit qu'il poste | le rush brut 4K (`ma-video/videos/<rush>.mp4`), après une frame vérifiée | tout le reste |
| Publiée | dossier déplacé dans `2_PUBLIE/`, **ou** 30 jours dans `1_A-POSTER/` sans retour | dans l'atelier : `public/input-video.mp4`, `public/voice.wav`, `public/music-bed.mp3`, `analysis/*.wav` | la **recette** (scripts, `index.html`, transcript, `frame.md`, `analysis/*.json`, captures b-roll, `lead-magnet/`) |
- Le post final (`_VIDEO.mp4`, couvertures, légende, guide) **ne se supprime pas** : c'est la seule copie pleine qualité (Instagram recompresse), ~30 Mo par vidéo.
- Avant d'alléger : vérifier que le `_VIDEO.mp4` du post existe et que la durée des fichiers à jeter correspond. Un atelier sans post archivé ne s'allège pas.
- La date seule déclenche le passage en `2_PUBLIE/` (un déplacement, réversible) ; elle ne justifie jamais de toucher à un fichier dont on n'a pas vérifié le contenu.

## 🎨 Style de montage (aligné sur la stratégie)
- **Sous-titres : sur tous les plans** (règle du 2026-09-06, mesurée sur la référence à 13,5k likes — elle n'a pas un seul plan nu). ⚠️ Ceci **remplace** la règle d'exclusivité du 2026-08-15, qui interdisait sous-titre et titre sur le même plan. Les deux ont cohabité jusqu'au 2026-09-10 ; c'est la version mesurée qui l'emporte.
  - 1 à 3 mots par groupe, **ancrés sur la couture du split** (y≈857, couture à y≈865) quand le plan est en split — c'est le point de repos de l'œil ; **sous le menton** sur le visage plein cadre. Jamais sous y 1550 : `tools/zones-mortes.mjs` avant chaque rendu.
  - Ce qui survit de l'ancienne règle : le sous-titre ne **recopie** pas le titre éditorial. Il dit autre chose, ou il le prolonge.
  - CTA → le mot-clé du lead-magnet doit être lisible sound-off.
  - Style : gros, lisibles, mot-à-mot rythmé, safe-zone centrale, aucun fond ni boîte.
- **Hook (0-3s) :** un **moment VISUEL dès l'image 0**, jamais « tête + titre » (retour du 2026-10-22). Le concevoir en premier, le montrer en images fixes avant le rendu ; titre et 1er sous-titre visibles dès l'image 0.
- **Rythme : coupe toutes les ~1,5 s, plafond dur 2,3 s** (mesuré : 1,46 s et 1,62 s sur les deux références qui performent). Zéro temps mort — couper toutes les respirations du rush, même au prix de sauts d'image. ⚠️ Remplace les « 2-4 s » d'origine et les « 1,8-3 s » d'`EDITING_SYSTEM.md`, qui étaient des estimations, pas des mesures.
  - **Sauf si la vidéo de référence fait autrement** (phase des reels d'essai, 2026-10-13) : la référence l'emporte sur le style maison. Restent imposés : zéro temps mort, synchro, loudness, nommage et livraison.
- **Direction visuelle :** l'identité est le **métal neutre** (graphite + ivoire chaud + chrome/acier). Le cyan est une ponctuation fonctionnelle `3-5%` max, jamais l'identité dominante. **Panneau de preuve sombre graphite-bleu par défaut** (2026-09-30) ; l'ivoire reste en ponctuation (une pastille, une carte isolée), jamais en fond de panneau. **Pas d'orange par défaut.** Voir `personal-brand-ref/brand-visual-system.md`.
- **Les affirmations à l'écran = ce qui est dit dans la vidéo tournée** (transcript du rush ; le `reel-XX` sert de repère). Les libellés de structure (badges, étiquettes, « avant / après ») sont ajoutés par le montage — voir les garde-fous.
- **Clip de frappe, de ta propre initiative :** dès qu'une ligne du script décrit **quelque chose qu'on tape** (un prompt, une demande à une IA, une commande), générer le clip avec `ma-video/tools/generate-typing-broll.py` — le texte de la voix s'écrit dans la barre, zoom serré par défaut, avec une légère poussée. Ne pas attendre qu'on le demande.
- **Couverture :** style par défaut du 2026-10-22 = **logo du sujet géant en aura derrière la tête + mot-clé métal** (patron : `ma-video/videos/2026-10-22_prof-apprend-en-12h/cover/cover.py`). Safe zone centrale, non modifiable après publication.
- **Pas de watermark** CapCut/TikTok (throttle IG). Export natif propre.

## ⚠️ Garde-fous
- Respecter `personal-brand-ref/brand-profile.md` : **spectaculaire permis, faux interdit** (l'anti-hype a été retiré comme stratégie le 2026-10-01).
- Appliquer `personal-brand-ref/brand-visual-system.md` comme direction visuelle par défaut, avec une flexibilité créative intentionnelle plutôt qu'une dérive esthétique.
- **Ne pas inventer d'affirmation** que la vidéo ne dit pas. En revanche la **mise en forme est le métier du montage** : badges numérotés `01 02 03`, étiquettes de colonne, « avant / après », mot surligné, ordre des éléments — tout cela s'ajoute librement. *(Reformulé le 2026-09-10 : la version d'origine, « ne pas inventer de texte à l'écran », interdisait aussi les badges numérotés que la doctrine de rétention réclame.)*

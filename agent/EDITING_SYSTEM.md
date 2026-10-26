## Editing System

This file captures the standing creative rules for this project.

### Positioning

- Primary goal: authority and brand image, now paired with audience growth and lead capture
- **Every video ends with a lead-magnet CTA (standing rule, set 2026-08-09).** The close asks for a comment keyword or a DM in exchange for a concrete deliverable (checklist, workflow, template, list). One keyword, in caps, spoken and on screen.
- The CTA is a close, never a plea: it stays inside the anti-hype guardrails, promises only what actually gets sent, and never oversells the deliverable
- The keyword must be a single short word tied to the topic, and the same word must appear in the caption
- Keep the ending visually clean; the CTA is carried by the copy and the voice, not by decoration

### Instagram 9:16 rule

- Treat platform UI zones as hostile space
- Keep critical text, key numbers, and logos inside a protected central safe area
- For a 1080x1920 Reel, default critical-content bounds are x=80..920 and y=260..1550
- Keep the right control column and bottom caption area free of critical information
- Remove persistent decorative labels from the top UI band unless they carry essential meaning
- Use dead space intentionally: empty wall, headroom, and negative space are preferred overlay zones
- Do not anchor important copy too low, too high, or too close to the right edge
- Measure these bounds on the delivered MP4, not on the code: real bounding box of every caption box, label and card (Reel #29 shipped two boxes 16-18 px past x=920 and labels 28 px above y=260 until this check; tool: `videos/2026-10-13_classement-outils-ia/analysis/verif-zones.py`)
- Check the composition BEFORE rendering too (since 2026-10-22): `"C:\Program Files\nodejs\node.exe" tools/zones-mortes.mjs videos/<slug>/public` (~12 s for 50 s). It measures the real ink of every text and the box of every card every 0.25 s; required result `❌ HORS ZONE : 0`. Hard limits: y < 220, y > 1550, x > 920 between y 1050 and 1700 (the icon column only exists bottom right), 2 px tolerance. `⚠️` = text between y 220 and 260 (tolerated for the top pills at y 232). Calibrated on #29 and #30 (0, matching their MP4 check). The MP4 check above stays the final proof
- ⚠️ The #32 template (`videos/2026-10-16_chine-seedance-monstre/`) has captions 10-30 px below y=1550 and two cards in the icon column (found by `zones-mortes.mjs`, confirmed on the published MP4): raise captions ~35 px when reusing it

### Talking-head motion rule

- Use zooms only as emphasis, not as filler
- Prefer subtle punch-ins over aggressive crash zooms
- Reserve zooms for thesis lines, reversals, or emotional peaks
- If a zoom does not add meaning, do not use it

### B-roll framing rule

- Choose the display mode from the information goal, never from a reusable visual habit
- Use a floating card with side margins for screenshots that should read as premium proof while keeping the speaker present
- Use full-screen, split-screen, or a close detail crop when context, action, or legibility matters more than the speaker
- Before approval, state why each B-roll is positioned that way and reject the layout if a better framing serves the idea
- Vary framing across videos when useful; never let the same top-card treatment become the default signature by accident

### Cover portrait rule

- The creator's appearance is brand-critical: a cover frame must flatter the face before it serves the concept
- Reject closed or half-closed eyes, motion blur, mid-speech distortion, awkward hand placement, tired-looking expressions, or any frame that could make the creator look impaired or careless
- Compare a contact sheet of several candidates before selecting the portrait; never accept the first technically usable frame
- Prefer an open, intentional gaze, clean facial definition, natural warm skin, and an expression that strengthens authority or approachability
- Prefer a frame from the current video, but a stronger portrait from another shoot may be used when the clothing, lighting, and context remain coherent and the result is not misleading
- Validate both the full 9:16 cover and the centered Instagram grid crop before delivery
- **Default cover layout since 2026-10-14** (validated by the creator on Reel #29, "better than all the previous ones"): the frame's own natural background, untouched; a large metal keyword placed BEHIND the head (photo, then keyword, then the same subject cut out on top, pixel-aligned, matte edge softened) so the skull hides about 40 % of the letters; kicker on top, white logo cards for the tools named, footer with the comment keyword and the handle. No graphite backdrop, no vignette, no tagline that cannot be read at grid size (~150 px wide). Template: `videos/2026-10-13_classement-outils-ia/cover/cover.py`

### Audio rule

- SFX should reinforce structure: transition, impact, reveal, confirmation, urgency
- Prefer clean, premium, restrained sound design over noisy or over-edited choices
- If an SFX draws attention to itself more than to the idea, reject it
- Restrained must still be audible: reject any SFX that disappears at normal phone volume
- Mix short SFX transients roughly 14-16 dB below the voice peak as a starting target
- Audition the sound-design pass with a low Instagram-style music bed before approval
- Preserve speech dominance, but never lower SFX merely to create unused headroom

### Lip-sync rule

- Lip sync is export-blocking: speech must remain sample-aligned with the original camera recording
- Preserve the original video timing and audio PTS; never retime the voice independently without a measured correction
- Compare every processed voice track against the source by audio cross-correlation before rendering
- Compare the audio inside every final rendered MP4 against the source again after encoding and muxing
- At 60 FPS, reject an export when the absolute measured delay exceeds 8.33 ms, half of one frame
- Apply only the measured compensation, render again, and repeat the measurement until the export passes
- Visual inspection is an additional human check, never the only lip-sync test
- Music and SFX must never be used to conceal or rationalize a voice-to-lips offset

### Reference intake

- **Replication from a link is now a standard operating mode (set 2026-08-09), not an exception.** The user sends a social URL of a US creator's winning video; the edit adapts it for the French market.
- Adapt, never photocopy: keep the mechanism that made it work (hook, structure, rhythm, proof type, CTA shape) and re-author the specifics in the brand's own voice, visual system, and examples
- Name the transferable mechanism explicitly in the analysis before editing; if the mechanism cannot be stated in one sentence, the reference is not understood yet
- A linked replication reference governs only the named edit; it never replaces the standing Proof First, brand, caption, audio, or retention system
- Never copy a reference's exact title cards, layouts, transition order, or unverified claims; never inherit its audio flaws
- Analyze the complete reference package before adapting it: footage, exact duration, edit rhythm, on-screen text, audio, caption, CTA, and visible engagement signals
- Never infer the soundtrack from visuals alone; retrieve or inspect the actual reference audio before deciding whether to reuse, replace, or reinterpret it
- Temporary reference downloads are allowed only for analysis and must be removed after the useful findings or selected assets have been recorded
- If a platform blocks the media, request a screen recording with sound rather than asking the user to download the original file

### Asset intake

- Reusable SFX, B-roll, images, music, and brand assets live in `asset-library/`
- Assets intended for one specific edit go in that video's `uploads/` folder
- Never duplicate reusable source assets between video folders
- The edit stages only its selected assets locally and records that selection
- See `videos/ASSET_INTAKE.md` for folder conventions

### Split layout standard (relevé sur le montage validé 0726-2, verrouillé 2026-08-14)

Géométrie mesurée au pixel sur `videos/0726-2/renders/0726-2-FINAL-60fps.mp4`, qui est
la référence interne de ce qui a été approuvé et publié. Ne pas réinventer un split.

- **Le visage descend, il ne rétrécit pas dans une boîte.** En mode preuve, la vidéo
  source passe à `scale ≈ 0.78` avec `transform-origin: 50% 0%` et `translateY ≈ 872px`.
  Elle garde une largeur dominante et occupe tout le bas du cadre. Une vidéo réduite en
  petit panneau flottant entouré de noir est un défaut, pas un style.
- **Couture** : dégradé graphite → transparent sur ~150px posé sur le bord haut du
  panneau visage. Jamais de bord net.
- **La zone de preuve se remplit, toujours** : kicker (tiret cyan + libellé capitales
  ~19px) à `y≈104`, **titre éditorial** Sora 700 ~60px à `y≈146`, puis la carte média
  centrée dans la zone `y 300..748`, largeur 972px à `x=54`. Un grand vide sombre sous
  le titre est un défaut.
- **Le titre éditorial n'est pas optionnel.** C'est lui qui porte le sens et la
  rétention, pas le sous-titre. Une ligne courte, avec accent Bodoni Moda italique en
  seconde ligne quand il y a une nuance (« Le même modèle. / *à zéro dollar.* »).
- **Sous-titres : aucun fond, aucune boîte.** Ivoire plein, Sora 700, 46-52px, ombre
  portée pour la lisibilité. Le karaoké garde les mots non prononcés à ~55% d'opacité,
  jamais moins : en dessous ils deviennent illisibles sur un visage éclairé.
- **Cyan** : il souligne, il ne remplit pas. Un trait de 3-4px sous un mot resté ivoire,
  le tiret du kicker, les numéros `01 02 03`. Jamais un mot entier rempli en gros.
- **Tout texte posé sur le visage en plein cadre exige un voile dégradé.** Sans lui le
  contraste tombe sous le seuil et le lint le signale.

### Product marks — show the logo, not just the name (set 2026-08-22)

When the voice names a recognizable tool, company, or product, the screen shows its
**mark**, not only its name in letters. The user asked for this explicitly during the
0813-97 edit: a logo lands faster than a word, it reinforces authority, and it makes
the point understood rather than read.

- Sweep the transcript for proper nouns and plan a logo slot for each **before**
  writing the composition.
- The mark enters **on the word**, like any other animation cue.
- Slots that work: above the number in a full-bleed slam, in a card title bar, in a URL
  bar, on a list row, on every row of a final recap, in the cover kicker.
- **Product colors by default.** The ivory-monochrome exception on 0813-tpe held because
  the logos there were a *list of connectors*; when the brand is the subject of the shot,
  it keeps its color.
- Never draw an approximation of a known logo, and never illustrate a name that cannot
  be sourced. A fake mark is worse than no mark.
- Source official SVGs into the video's `public/assets/press/`. One file copy per slot:
  the linter flags `<img>` elements sharing a source.
- **Check the frame before adding a mark.** On the 0813 Fish Audio edit the official
  lockup already filled the proof card at the moment the voice named the tool; a second
  mark added at the top read as a duplicate and was reverted. A logo repeated inside one
  shot is not reinforcement.
- Monochrome ivory stays correct in two cases: a **list of connectors**, where the names
  are the proof and three saturated logos side by side would read as a logo wall
  (0813-tpe), and marks that are **monochrome by design** (OpenAI). In those cases the
  work is on size and legibility, not on color.
- A mark that is present but too small does not do the job. Measured floor from the
  0813-2 revision: **42 px** in a grid tile, **36 px** in a card title bar, **150 px**
  full-bleed, at 0.96 opacity.

### Kill stale preview servers before a long render (2026-08-23)

`hyperframes preview` survives the harness task that launched it. An orphaned Studio
starved a render to **zero bytes written** for eight minutes; the same render finished in
9 min 42 s once the orphan was killed. Before any long render, check
`Get-CimInstance Win32_Process -Filter "Name='node.exe'"` and stop any leftover
`hyperframes preview`.



### Doctrine de rétention (2026-09-06 — remplace les réglages de rythme antérieurs)

Établie en décortiquant un reel de référence de la même niche à **13,5k likes / 29,1k
commentaires** (Nate Herk, @nateherkai). Mesures complètes :
`reference-analysis/nate-herk-DbLuwUVlE9Z/analysis.md`. **Feu vert utilisateur du
2026-09-06** pour casser les deux règles marquées ⚠️ ci-dessous.

**Cadence**
- Coupe toutes les **~1,5 s**. **Plafond dur : 2,3 s.** (Référence : 1,48 s de moyenne,
  2,30 s au maximum. Notre 0906 : 2,62 s de moyenne, 3,20 s au pire.)
- **Hook : moins de 2 s.** La première preuve est à l'écran à **0,00 s**, pas à 5 s.
- **Zéro blanc.** Couper toutes les respirations du rush, même au prix de sauts d'image :
  la référence n'en laisse que 0,68 s sur 26,6 s. Les sauts sont masqués par le changement
  du panneau de preuve. *(À ne pas confondre avec la règle « ⛔ silences insérés » : on
  supprime, on n'ajoute jamais.)*

**⚠️ Sous-titres — la règle d'exclusivité du 2026-08-15 est LEVÉE**
- Sous-titres sur **100 % des plans**, 1 à 3 mots. La référence n'a pas un seul plan nu.
- **Ancrés sur la couture du split**, pas en bas de cadre (mesuré chez elle : sous-titre à
  y≈857, couture à y≈865). C'est le point de repos de l'œil.
- La règle anti-doublon survit sous une forme réduite : le sous-titre ne **recopie** pas le
  titre éditorial, il dit autre chose ou le prolonge.

**Code couleur sémantique (deux accents, pas un)**
- **Bleu signal** = le mot qui compte, le positif, la preuve. *(inchangé)*
- **Rouge sobre** = la menace, le négatif, ce qui est barré. Nouvel accent, réservé à ça,
  jamais décoratif. La référence l'utilise deux fois en 26 s (`just killed`, `generic` barré).
- Prévoir dans chaque vidéo **une paire négatif/positif** à opposer visuellement.
- Badges numérotés **#1 #2 #3** dans le panneau de preuve pour les étapes.

**⚠️ Contraste — l'équilibre « 55 % graphite » est assoupli en mode preuve**
- Le panneau de preuve doit être **lumineux** : luminance mesurée chez elle **223/255** en
  haut contre **94/255** sur le visage. Nos cartes graphite sur fond graphite écrasent ce
  contraste et rendent le cadre mou.
- Les vraies captures de produit sont majoritairement claires : **on les laisse claires.**
  C'est déjà ce que dit la règle « Product colors remain truthful ».
- Graphite et ivoire restent l'identité sur le reste du cadre.

**Son — contour, pas moquette** ⚠️ HYPOTHÈSE, PAS ENCORE UNE RÈGLE (voir note en bas)
- **Supprimer le lit musical continu.** Mesuré sur la référence (canal L−R, qui annule la
  voix centrée) : seulement **25 %** de la timeline porte une couche sonore audible,
  concentrée en **3 zones** — le hook (pic −15,4 dB), la révélation centrale (−23,1 dB),
  la fermeture CTA (−32 dB). Entre les deux : **voix sèche, plancher à −45 dB.**
- **Registre : sub-grave, pas métal brillant.** Centroïde spectral mesuré de son design
  sonore : **315 Hz** sur le hook, **219 Hz** sur la révélation, **0 % d'énergie au-dessus
  de 3 kHz**. Ce sont des impacts qu'on ressent. Notre bibliothèque actuelle
  (`metal-reveal`, `dry-transition`…) est brillante : mauvais registre pour ce rôle.

**B-roll**
- **Captures réelles uniquement.** La référence : 0 schéma inventé sur 18 plans.
- Un schéma dessiné est un aveu qu'on n'a rien de réel à montrer. Si on n'a rien de réel,
  **le problème est dans le script, pas dans le montage** — voir
  `../personal-brand-ref/script-contraintes-montage.md`.
- Le monteur peut capturer lui-même toute page web publique (contrôle de Chrome). Ce qu'il
  ne peut pas produire : l'écran de l'utilisateur en train d'utiliser l'outil.

**CTA**
- Le mot-clé se déduit d'un mot du hook, pour refermer la boucle. Référence :
  *« just killed »* → *« comment DIE »*.

**⚠️ Statut des mesures ci-dessus (mis à jour le 2026-09-07, 2 références)**

Une seconde vidéo du même créateur (`2026-08-09_reference-kakashi-DbTsfELAMBK`, 40,4 s,
post sponsorisé Fish Audio) a été passée au même banc de mesure. Résultat :

| Élément | Reel 700k (DbLuwUVlE9Z) | Reel sponsorisé (DbTsfELAMBK) | Statut |
|---|---|---|---|
| Cadence moyenne | 1,48 s | **1,68 s** | ✅ **confirmé** |
| Première coupe | dans le hook, < 1,5 s | **0,98 s** | ✅ **confirmé** |
| Plan le plus long | 2,30 s | **3,67 s** | ⚠️ variable |
| Contour sonore en 3 zones | oui (25 % de la timeline) | **non — lit continu, 5 %** | ❌ **NON confirmé** |

→ La cadence de coupe et le hook ultra-court sont **son système**. Le contour sonore en
3 zones est **une décision propre à la vidéo à 700k vues**, pas une signature.
Hypothèse à tester sur les prochaines références : *l'absence de lit continu est corrélée
à la performance.* Deux échantillons ne prouvent rien — **ne pas verrouiller cette règle
avant 5 références.** En attendant : disponible comme option de montage, pas comme défaut.

### Quality bar

- Readability beats decoration
- Motion must feel intentional
- Layout should look premium even when paused on any frame
- Every revision should improve clarity, authority, and retention
- An illustration must be understandable without the editor explaining it afterward
- Never label a reference asset as a generated result; asset role must be verified before authoring
- Do not use a full-screen proof layout when the media leaves most of the vertical frame empty; use a deliberate face/proof split instead
- A beautiful but semantically weak B-roll is inferior to a simpler visual that directly proves the spoken claim
- When semantic overlays already carry the message, captions should support them rather than duplicate every title

### Performance reset - Proof First

- Prove before decorating: prefer real interfaces, actions, outputs, and results over invented diagrams
- The first promise must be understandable within 3 seconds and the first concrete proof should appear by 5 seconds
- Change visual state every 1.8-3 seconds only when the new state adds information
- Use the loop `claim -> proof -> face reset` to preserve both authority and human connection
- Do not reuse a fixed split-screen template across every video
- Keep the creator visually large; full-face resets are required at hooks, reversals, and conclusions
- Use sparse semantic captions of 2-5 words instead of either full karaoke subtitles or no captions at all

### Factual verification — owner split (set 2026-08-15)

The user owns the veracity of his own claims and will check them on his side. **The
editor does not run web verification passes on the spoken content any more** — that
time goes into the edit itself.

- Do not research, source-check, or fact-table the voice-over unless explicitly asked.
- The one thing the editor still owns: **the screen is the editor's output.** If a
  figure or claim is put on screen, say plainly whether it came from the user or from
  the editor. If the user supplies a number, display it without argument.
- Historical note: the 0813 and 0813-2 edits were built under the previous rule and
  their `frame.md` files contain source tables. Those stay as a record; they are not
  a template for new edits.

### ~~Caption exclusivity rule (2026-08-15)~~ — RÉVOQUÉE le 2026-09-10

Cette section énonçait « captions and the editorial title are mutually exclusive, never both
on the same shot ». Elle a été **levée** par la doctrine de rétention du 2026-09-06 (sous-titres
sur 100 % des plans, mesuré sur la référence à 13,5k likes), mais son texte complet est resté
dans ce fichier **plus bas que la doctrine qui l'annulait** — donc quiconque lisait le fichier
en entier appliquait la règle morte. Supprimée le 2026-09-10.

Ce qui en survit, et qui reste vrai : **un sous-titre ne recopie pas le titre éditorial.**
Il dit autre chose, ou il le prolonge. C'est ce qui avait motivé la règle (mesuré sur 0813 :
neuf groupes de sous-titres sur dix-sept répétaient mot pour mot le titre affiché au même
instant). Le remède était trop large ; le constat, lui, tient.

- The identity is neutral metal: graphite, warm ivory, and chrome/steel; ice-cyan is functional punctuation at `3-5%` max, never the dominant identity; product colors remain product colors
- Temperature is a semantic cursor: personal/journey content is ivory-dominant, while proof/agency content is graphite/steel-dominant with restrained cyan signals
- The canonical colors, signature gradient, format-specific applications, and anti-commodity guardrails live in `../personal-brand-ref/brand-visual-system.md` and must be consulted before defining a new visual direction
- Preserve natural, warm skin tones; the blue system frames the creator and the proof but never casts the footage cold
- Use the ice-metal gradient only for decisive proof, a key number, or a reveal; never as permanent caption styling or ambient decoration
- Default type direction is Sora with a rare Bodoni Moda editorial accent
- Background removal is optional proof choreography, not a permanent look; use it for at most roughly 20% of a video
- For a 30-45 second Reel, prefer 4-6 structural SFX plus meaningful native UI clicks over constant whooshes
- Delivery audio target is now approximately -14 LUFS with protected true peaks, based on the supplied successful references
- Preserve 60 FPS when the source is 60 FPS, but never treat frame rate as a growth lever

### Bibliothèques d'assets — état du 2026-09-10 (remplace « la bibliothèque est vide »)

Deux bibliothèques réelles existent maintenant. **Les consulter avant de fabriquer quoi que
ce soit**, et les alimenter plutôt que de créer des assets jetables dans un dossier de vidéo.

- `asset-library/sfx/LISEZ-MOI.md` + `catalogue.json` — **83 sons**, mesurés et normalisés.
- `asset-library/broll/00-INDEX.md` + `catalogue.json` — **2 147 fichiers, 1 026 sujets**, classés
  en 10 catégories / 47 sous-catégories, **toutes peuplées**. Dont **737 logos de marques**
  (`09-marques-et-logos/LISEZ-MOI.md`, planches-contact par secteur) et **178 clips vidéo**, tous passés au contrôle qualité.

Provenance : captures réelles (Chrome headless), écrans construits en HTML, fonds procéduraux
à la charte, logos officiels (`cdn.simpleicons.org`), et photos **CC0 uniquement** (Openverse —
domaine public, usage commercial libre, aucune attribution exigée).

Deux pièges consignés dans l'index :
- **Les photos de banque ne sont pas à la charte** : les étalonner avant usage.
  `tools/broll_triage.py` écarte les plus datées **sur mesure** (saturation, dominante colorée,
  netteté), pas à l'œil ; les écartées vont dans `_ecartes/`, elles ne sont pas supprimées.
- **Un logo marqué `simplifié` n'a pas la vraie colorimétrie de la marque.** Simple Icons ne
  fournit qu'un tracé monochrome. Forme officielle, couleurs non : bon pour une liste de
  connecteurs, à remplacer par le lockup officiel si la marque est le **sujet** du plan.
  LinkedIn, Amazon, Adobe et Canva en ont été retirés pour raisons de marque déposée : on ne
  contourne pas, on les source à la main sur leur page presse.

Les deux index sont **générés** (`tools/sfx_catalog.py`, `tools/broll_catalog.py`). Après tout
ajout, les régénérer — un index écrit à la main devient faux au premier fichier suivant.

### Registre sonore de la marque — mesuré, verrouillé (2026-09-10)

**L'identité visuelle est le métal. L'identité SONORE ne l'est pas.**

C'est l'erreur qui a produit une bibliothèque SFX inutilisable : les prompts de génération
demandaient *« liquid-chrome shimmer »*, *« glass highlight »*, *« brushed-steel click »* —
le vocabulaire de la charte visuelle transposé tel quel en audio. Le modèle a produit
littéralement du chrome. Mesure de l'ancienne bibliothèque : **8 000 à 10 700 Hz de centroïde,
91 à 98 % de l'énergie au-dessus de 3 kHz.**

Mesure des deux références qui performent (Nate Herk, `DbLuwUVlE9Z` et `DbTsfELAMBK`) :
**96 à 100 Hz de centroïde, 0,08 à 0,12 % au-dessus de 3 kHz, 92 à 97 % sous 200 Hz.**
Registre exactement inverse.

- **Vocabulaire autorisé en prompt audio :** sub, low, deep, chest, thud, rumble, muffled, felt.
- **Vocabulaire interdit :** chrome, glass, shimmer, sparkle, metallic, crystal, bright.
- **Aucun son n'entre dans la bibliothèque sans passer `tools/sfx_bench.py`.** Ce qui sort du
  spec est jeté, pas réécouté. On ne juge plus à l'oreille.
- **Exception documentée : le rôle `ui`.** C'est le seul dont le spec n'est pas mesuré — aucune
  des 5 références analysées ne contient de son d'interface. Ses bornes sont larges à dessein.
  À recaler dès qu'une référence avec du son d'interface sera mesurée.
- La génération IA est bonne sur les nappes et les impacts, **mauvaise sur le mécanique court
  et sec** (1 son UI utilisable sur 6). Ces sons-là sont **synthétisés** (`tools/synth_sfx.py`),
  ce qui donne un contrôle exact du spectre : 9 impacts sur 9 passent le banc.

### B-roll — la contrainte « captures réelles uniquement » est LEVÉE (2026-09-10, décision du créateur)

L'ancienne règle (« un schéma dessiné est un aveu qu'on n'a rien de réel à montrer ») punissait
le montage pour un manque de stock : la bibliothèque contenait 3 fichiers.

- **Illustrer est libre.** Fonds, bureaux, mains, écrans génériques, ambiances, images générées
  ou sourcées : le critère est « est-ce que ça fait mieux comprendre et mieux retenir ».
- **Une seule réserve, et elle est factuelle, pas esthétique :** ne pas fabriquer l'écran d'un
  **produit nommé** et le présenter comme sa vraie interface. Un écran générique n'affirme rien ;
  un faux écran « Claude » ou « n8n » est une affirmation vérifiable, et elle contredit le
  positionnement (« de l'IA vérifiée, montrée à l'écran »).
- Les écrans générés le sont **clairs**, jamais graphite : la référence a un panneau de preuve
  à 223/255 de luminance contre 94/255 sur le visage, et nos cartes graphite sur fond graphite
  écrasaient ce contraste.
- **Aucun asset ne doit laisser la majorité du cadre vide.** Les écrans sont recadrés
  automatiquement sur leur contenu (`tools/generate-ui-screens.py`) — un canevas fixe laissait
  jusqu'à 70 % de vide.

### Traitement des captures — relevé sur références (2026-09-10)

Sur les trois références InsiderForce analysées, **aucune capture n'est posée à plat** :
coins arrondis, ombre portée profonde, légère rotation, parfois pile de cartes décalées.
C'est le traitement qui fait la valeur perçue, pas la capture.

`tools/broll_treatments.py` applique ces traitements à n'importe quelle image — les écrans
générés comme les captures réelles à venir. **Ne plus jamais poser une capture brute dans un
plan.**


### B-roll vidéo — mettre en mouvement ce qu'on a déjà (2026-09-10)

178 clips MP4 60 fps, produits par `tools/generate-video-broll.py` **à partir des images de la
bibliothèque**. On ne cherche pas de rushes ailleurs : un plan fixe de 2 s se voit, le même plan
avec une dérive lente se regarde.

- **Dérive (Ken Burns)** — zoom et translation très lents, 1080×1920 ou 1920×1080. 45 clips.
- **Défilement** — une capture longue qui défile. Ça ne lit pas comme un panoramique, ça lit
  comme **quelqu'un qui scrolle une page** : c'est le plan le plus utile de la niche. 54 clips.
  Les captures produits sont gardées en version longue (3 000 px) dans `_longues/` pour ça.
- **Curseur** — un pointeur qui rejoint une cible. Donne l'impression d'un enregistrement
  d'écran sans en faire un. 23 clips.
- **Frappe de prompt** (`tools/generate-typing-broll.py`) — un prompt qui s'écrit caractère par
  caractère dans une interface d'IA, curseur qui clignote, en plein cadre ou en **zoom serré
  sur la barre de saisie**. Plus une variante complète : on tape, on envoie, la réponse s'écrit.
  9 clips. C'est le plan le plus parlant de la niche — on parle d'IA, donc voir un prompt
  s'écrire dit le sujet sans un mot de commentaire.

  *Fabrication :* Chrome rend la coque **une seule fois**, PIL dessine le texte image par image.
  Un lancement de navigateur par frame coûterait 0,5 s × 200 frames par clip.
### Interfaces familières — la marque est le décor, pas la source (2026-09-10)

Demande explicite du créateur : une conversation ou une notification doit être **familière**
pour être crédible. Une bulle générique ne déclenche rien ; un WhatsApp, un DM Instagram, une
notification Stripe se reconnaissent en un quart de seconde.

**La ligne, en une phrase :** on reproduit l'**idiome visuel** d'une plateforme connue pour
illustrer une situation banale — une conversation client, un paiement reçu, un prompt qu'on
tape. On ne fabrique pas une **annonce officielle attribuée à une marque**, ni une réponse
produit qui affirmerait une capacité. Dans le premier cas la marque est le décor du geste ;
dans le second elle est la source d'une affirmation, et c'est vérifiable.

### Clip de frappe : à générer de sa propre initiative (règle permanente, 2026-09-11)

Demande explicite du créateur. **Le monteur n'attend pas qu'on le lui demande.**

Dès qu'une ligne du script mentionne un prompt, une demande faite à une IA, une commande,
une recherche — bref, dès que la voix décrit **quelque chose qu'on tape** — le montage
génère le clip correspondant avec `tools/generate-typing-broll.py` et le pose sur le plan.

- **Le texte tapé est celui de la voix**, ou sa forme la plus courte. Si le script dit
  « t'es expert en négociation, voilà ma situation », c'est ça qui s'écrit à l'écran.
- **Cadrage par défaut : le zoom serré sur la barre de saisie.** C'est le plan qui se lit
  en une seconde. Le plein cadre sert quand on veut montrer l'interface autour.
- **Ajouter une poussée** (léger zoom avant sur la durée du clip) : le texte seul fait
  bouger 0,2 % des pixels, le plan paraît figé sans ça.
- L'interface est choisie selon l'outil nommé dans le script. À défaut, la version générique.
- Enchaîner sur la variante « on tape → on envoie → la réponse s'écrit » quand le script
  décrit aussi le résultat.

C'est paramétrique : n'importe quel texte, dans n'importe quelle interface, en une minute.
Aucune raison de s'en priver sur un montage qui parle d'IA.

### Contrôle qualité vidéo — obligatoire avant d'indexer (2026-09-11)

`tools/video_qc.py` mesure chaque clip : variance de l'image, **part de pixels qui bougent**,
part du cadre d'une seule teinte. Il recale ce qui est **mort** — pas ce qui est discret.

Trois défauts réels qu'il a trouvés, et qui sont corrigés dans les générateurs :

1. **Recadrer une capture large en 9:16 par le centre** tombait sur la bande vide du milieu
   de page : des clips à variance 0 alors que l'image source était bonne. On recadre
   désormais **par le haut**.
2. **Animer un dégradé lisse est vain** — il n'a aucun détail à déplacer, le zoomer produit
   le même dégradé. Mesure : 0,00 % de pixels en mouvement même à forte amplitude. Les
   dégradés restent en PNG ; seuls les fonds **texturés** gardent une version vidéo.
3. **Un curseur de 54 px sur un cadre de 1600 px** ne fait bouger que 0,3 % des pixels : le
   plan paraît figé. On ajoute une légère poussée pour que le cadre entier vive.

⚠️ **Le banc arbitre le mort, jamais le goût.** S'il recale un asset validé à l'œil, c'est la
métrique qui est fausse. Et ce qu'il ne sait pas voir — matériel daté, sujet hors propos —
demande une revue visuelle : elle a sorti un cockpit de chasseur rangé en « bureau de nuit »
et une photo datée de 2009, que trois filtres mesurés avaient laissés passer.

---

## Les 8 layers — la pile de composition (definie le 2026-09-18)

> Le terme « les 8 layers » revenait dans les consignes sans exister nulle part dans le
> projet ni dans les skills : verifie par recherche, aucune occurrence. Il est defini ici
> une bonne fois, comme **pile de composition** — l'ordre dans lequel une image se fabrique.
> Un plan qui saute un layer n'est pas forcement faux, mais il doit sauter **par decision**.

| # | Layer | Ce qu'il porte | Ou il vit dans `emit-html.py` |
|---|---|---|---|
| 1 | **Fond** | graphite ou ivoire — et il **alterne** | `.base-bg`, `.slam.ivory` |
| 2 | **Sujet** | le rush : plein cadre ou demi-cadre | `#source-video`, `#face-window` |
| 3 | **Traitement** | voile bas, vignette, couture, filet | `.low-scrim`, `.face-vig`, `.seam`, `.split-line` |
| 4 | **Decor** | lueur, grain, matiere de fond | `.hero-glow`, `.grain` |
| 5 | **Preuve** | les cartes : objets poses, inclines, ombres | `.th`, `.hero`, `.term`, `.repo` |
| 6 | **Illustration** | scenes vectorielles, quantification, motion-elements | `.mosaic`, `.rows`, `.pipe`, `.pick-ring`, `.strike` |
| 7 | **Typographie** | titre editorial, accent mobile, wordmark | `.hooktype`, `.slam-t`, `.metal`, `.rank` |
| 8 | **Sous-titres + CTA** | la parole, le mot-cle du lead-magnet | `.caption-group`, `.cta` |

**La regle qui va avec :** les layers 2 et 5 se **disputent le meme espace**. Un visage plein
cadre occupe le centre du cadre ; une carte de preuve aussi. On ne peut donc pas avoir les
deux — sauf en demi-cadre, qui est precisement le compromis. D'ou la choregraphie ci-dessous.

## Choregraphie de cadre — mesuree contre les references (2026-09-18)

Releve du montage #23 **avant** correction : visage plein cadre **8,6 %** de la duree, et
uniquement sur le CTA final. Une seule geometrie de carte (`972x596` a `54/104`) pour **12
plans sur 20**. Le cadre ne changeait jamais de forme.

| | ce montage (avant) | kakashi | InsiderForce |
|---|---|---|---|
| Visage plein cadre | 8,6 % | **~25 %** | ~4 %, **mais tout au hook** |
| Moments en plein cadre | le CTA | punch du hook, urgence, **pivot**, douleur, CTA | le hook |

**Regle retenue :** le plein cadre visage est **reserve**, et il est reserve aux memes moments
chez les deux references — **le hook, le pivot, le CTA**. Ailleurs, demi-cadre. Chaque bascule
est **jouee** (`power3.inOut`, ~0,34 s), jamais coupee : c'est un mouvement de mise en scene.

Corollaire : **le hook s'ouvre sur un visage plein cadre.** Un visage qui regarde arrete le
scroll ; une carte posee dessus, non. Le titre s'ecrit dans le **tiers bas**, sur le buste,
jamais sur le visage — et il **meurt a la coupe**, sinon il se retrouve sur la figure au plan
suivant (defaut constate et corrige le 2026-09-18).

## Revelation additive — l'autre voie vers la retention

`CLAUDE.md` fixe « coupe toutes les ~1,5 s », mesure sur les deux Nate Herk. La reference
InsiderForce (1,16 M vues) **ne coupe presque pas : elle empile.** Le layout reste, les lignes
s'ajoutent une par une — environ **un changement d'etat par seconde**, sans jamais relancer le
regard a zero.

Les deux mecanismes sont valides et **opposes**. Ce que HyperFrames fait le mieux, c'est le
second : `data-start` decales sur une meme sous-composition, un seul timeline. A utiliser
partout ou une enumeration se presente ; garder la coupe franche pour les **ruptures de
section**.

Autres releves transferables de cette reference, par ordre d'effet :
1. **Accent typographique mobile** — un seul mot en gras par ligne, et il se deplace.
2. **Montrer les nombres** au lieu de les ecrire (une grille de 64 elements se remplit).
3. **Cartes inclinees a ombre large**, entrant en pile decalee — des objets, pas des captures.
4. **Une seule couleur d'accent** + les vrais logos produits. Notre equivalent : l'ice-cyan 3-5 %.

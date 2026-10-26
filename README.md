# Agent IA de montage vidéo

Un agent IA qui monte des vidéos courtes pour créateurs de contenu, d'un rush brut filmé face caméra
jusqu'à la vidéo prête à publier : découpe, sous-titres, motion design, visuels, musique, couverture
et contrôle qualité.

Je l'ai construit sur **Claude Code** et le framework vidéo **HyperFrames** (des compositions
HTML/GSAP rendues en MP4). Il a produit **une trentaine de vidéos publiées** entre juillet et octobre 2026.

## Ce que fait l'agent

1. **Il analyse une vidéo de référence** image par image : rythme des coupes, placement des
   sous-titres, couleurs, musique. Puis il en reproduit la mécanique.
2. **Il transcrit le rush** mot à mot, en local, pour caler chaque sous-titre et chaque visuel sur la voix.
3. **Il monte** : coupe toutes les respirations, place les sous-titres dans les zones lisibles,
   ajoute du motion design, des captures d'écran, des logos et des clips générés.
4. **Il habille le son** : musique, effets sonores, niveau sonore contrôlé, voix toujours au-dessus.
5. **Il vérifie avant de livrer** : synchronisation son/image, raccords trop brutaux, éléments
   hors des zones visibles, palette de couleurs, qualité de la vidéo finale.
6. **Il livre** la vidéo, la couverture, la légende et un guide PDF, nommés selon une convention fixe.

## Comment il est construit

```
agent/
  CLAUDE.md              le poste de travail de l'agent : workflow, conventions, style, garde-fous
  EDITING_SYSTEM.md      la doctrine de montage : 512 lignes de règles, mesurées sur des vidéos qui performent
tools/                   49 outils Python et JavaScript (≈ 9 300 lignes) que l'agent appelle lui-même
```

**Les outils, par famille**

| Famille | Exemples |
|---|---|
| Analyse | `analyze_reference.py`, `analyze_music_refs.py`, `transcribe_local.py` |
| Images et b-roll | `broll_triage.py`, `broll_coherence.py`, `generate-typing-broll.py`, `generate-ui-screens.py`, `fetch-logos.py` |
| Son | `mix_guard.py`, `bed-masking.py`, `sfx_catalog.py`, `signature_sonore.py`, `generate-elevenlabs-music-v2.mjs` |
| Contrôle qualité | `video_qc.py`, `check_audio_sync.py`, `jumpcut-audit.py`, `palette-audit.py`, `gap-audit.py` |

## Les principes qui le rendent fiable

- **Des règles mesurées, pas devinées.** Le rythme de coupe (une coupe toutes les ~1,5 s) et la
  position des sous-titres viennent de mesures faites sur des vidéos de référence.
- **Une seule source de vérité par sujet** : quand une règle change, l'ancienne est barrée et datée, jamais laissée en contradiction.
- **Rien n'est livré sans contrôle** : chaque rendu passe par les outils de vérification.
- **Le fond n'est jamais inventé** : ce qui s'affiche à l'écran vient de ce qui est dit dans la vidéo.
  La mise en forme, elle, est le métier de l'agent.
- **Hygiène** : tout ce qui se régénère est nettoyé après chaque montage ; rien n'est supprimé définitivement.

## Stack

Claude Code · HyperFrames (HTML, GSAP) · Python (FFmpeg, analyse audio et image) · Node.js ·
Whisper (transcription locale) · ElevenLabs (musique et effets, clé lue depuis une variable d'environnement)

---

> Les rushes, les vidéos et les bibliothèques de médias ne sont pas publiés : ce dépôt montre
> l'architecture de l'agent, ses règles et ses outils.

Conçu par **Gadiri Bah**, étudiant ingénieur à Junia ISEN Lille.

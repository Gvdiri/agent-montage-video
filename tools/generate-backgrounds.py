#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generateur de fonds et textures de marque - Hyperframes.

Pourquoi ce fichier existe : les fonds sont la seule categorie de b-roll qu'on n'a
aucune raison d'aller chercher ailleurs. Du stock generique ne sera jamais exactement
au graphite #071017 ni a l'ivoire #F3F1EA, et un fond hors charte se voit.
Ici c'est procedural : gratuit, illimite, deterministe, exactement a la palette.

Palette lue dans personal-brand-ref/brand-visual-system.md (v1.1, verrouillee).

Sortie : asset-library/broll/06-fonds-et-textures/<sous-categorie>/
  - stills   -> PNG 1080x1920 (alpha quand c'est un voile ou un overlay)
  - motion   -> MP4 60 fps, bouclables
  - overlays -> WebM VP9 avec alpha (grain, balayages, particules)

Usage :
    python tools/generate-backgrounds.py [--only gradients,grain,...] [--list]
"""
import os
import sys
import math
import json
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- charte
GRAPHITE = (0x07, 0x10, 0x17)
IVOIRE = (0xF3, 0xF1, 0xEA)
STEEL = (0x8D, 0x9A, 0xA1)
SIGNAL = (0x22, 0xB9, 0xF2)
ICE = (0x8E, 0xDD, 0xF7)
MINERAL = (0xF4, 0xF7, 0xF3)
CYAN = (0x25, 0xB9, 0xEE)

W, H = 1080, 1920
FPS = 60

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "06-fonds-et-textures")

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

_produits = []


def dest(sub, name):
    d = os.path.join(OUT, sub)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def note(sub, name, kind, desc):
    _produits.append(dict(sous_categorie=sub, fichier=name, type=kind, description=desc))


# --------------------------------------------------------------------------- outils
def lin_grad(w, h, c0, c1, angle_deg):
    """Degrade lineaire, angle en degres (0 = gauche->droite, 90 = haut->bas)."""
    a = math.radians(angle_deg)
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    t = xs * math.cos(a) + ys * math.sin(a)
    t = (t - t.min()) / max(float(np.ptp(t)), 1e-6)
    c0 = np.array(c0, dtype=np.float32)
    c1 = np.array(c1, dtype=np.float32)
    return (c0[None, None, :] + (c1 - c0)[None, None, :] * t[:, :, None])


def tri_grad(w, h, c0, c1, c2, angle_deg, mid=0.48):
    """Degrade a trois arrets - c'est la forme du gradient signature de la marque."""
    a = math.radians(angle_deg)
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    t = xs * math.cos(a) + ys * math.sin(a)
    t = (t - t.min()) / max(float(np.ptp(t)), 1e-6)
    c0, c1, c2 = (np.array(c, dtype=np.float32) for c in (c0, c1, c2))
    lo = t < mid
    out = np.zeros((h, w, 3), dtype=np.float32)
    u = np.clip(t / max(mid, 1e-6), 0, 1)[:, :, None]
    v = np.clip((t - mid) / max(1 - mid, 1e-6), 0, 1)[:, :, None]
    out = np.where(lo[:, :, None], c0 + (c1 - c0) * u, c1 + (c2 - c1) * v)
    return out


def radial(w, h, c_in, c_out, cx=0.5, cy=0.35, radius=0.85, falloff=1.6):
    xs = (np.linspace(0, 1, w, dtype=np.float32)[None, :] - cx)
    ys = (np.linspace(0, 1, h, dtype=np.float32)[:, None] - cy) * (h / w)
    d = np.sqrt(xs ** 2 + ys ** 2) / radius
    t = np.clip(d, 0, 1) ** falloff
    c_in = np.array(c_in, dtype=np.float32)
    c_out = np.array(c_out, dtype=np.float32)
    return c_in[None, None, :] + (c_out - c_in)[None, None, :] * t[:, :, None]


def fbm(w, h, octaves=5, seed=0, persistence=0.55):
    """Bruit fractal - la base du grain mineral et du metal brosse."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        res = 2 ** (o + 2)
        small = rng.random((max(res, 2), max(int(res * w / h), 2))).astype(np.float32)
        up = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                      dtype=np.float32) / 255.0
        out += up * amp
        tot += amp
        amp *= persistence
    out /= max(tot, 1e-6)
    return (out - out.min()) / max(float(np.ptp(out)), 1e-6)


def save_png(arr, sub, name, desc, alpha=None):
    a = np.clip(arr, 0, 255).astype(np.uint8)
    if alpha is not None:
        al = np.clip(alpha, 0, 255).astype(np.uint8)
        img = Image.fromarray(np.dstack([a, al]), mode="RGBA")
    else:
        img = Image.fromarray(a, mode="RGB")
    p = dest(sub, name)
    img.save(p, optimize=True)
    note(sub, name, "still", desc)
    print("  still  %-52s %s" % (name, desc))
    return p


def run_ff(args, label):
    r = subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  ! ffmpeg a echoue sur %s : %s" % (label, (r.stderr or "").strip()[:300]))
        return False
    return True


def drift_mp4(src_png, sub, name, desc, dur=6.0, zoom_from=1.0, zoom_to=1.12, dx=0.0, dy=0.0):
    """Anime un still en derivant lentement dedans. Beaucoup plus rapide que de
    calculer 360 frames en numpy, et le rendu est plus doux."""
    n = int(dur * FPS)
    # zoompan travaille sur l'image agrandie, on cadre 1080x1920 dedans
    zexpr = "%.5f+(%.5f-%.5f)*on/%d" % (zoom_from, zoom_to, zoom_from, n)
    xexpr = "iw/2-(iw/zoom/2)+(%.1f*on/%d)" % (dx, n)
    yexpr = "ih/2-(ih/zoom/2)+(%.1f*on/%d)" % (dy, n)
    vf = ("scale=%d:%d,zoompan=z='%s':x='%s':y='%s':d=%d:s=%dx%d:fps=%d"
          % (W * 2, H * 2, zexpr, xexpr, yexpr, n, W, H, FPS))
    p = dest(sub, name)
    ok = run_ff(["-loop", "1", "-i", src_png, "-vf", vf, "-t", "%.3f" % dur,
                 "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                 "-pix_fmt", "yuv420p", "-an", p], name)
    if ok:
        note(sub, name, "motion", desc)
        print("  motion %-52s %s" % (name, desc))
    return ok


def grain_webm(sub, name, desc, dur=4.0, strength=18, mono=True):
    """Grain anime avec alpha, a poser en surimpression. VP9 pour garder l'alpha."""
    p = dest(sub, name)
    src = "color=c=black:s=%dx%d:r=%d:d=%.2f" % (W, H, FPS, dur)
    flt = ("noise=alls=%d:allf=t%s,format=gray,"
           "geq=r='p(X,Y)':g='p(X,Y)':b='p(X,Y)':a='p(X,Y)',format=yuva420p"
           % (strength, "+u" if mono else ""))
    ok = run_ff(["-f", "lavfi", "-i", src, "-vf", flt,
                 "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30",
                 "-an", p], name)
    if ok:
        note(sub, name, "overlay", desc)
        print("  overlay %-51s %s" % (name, desc))
    return ok


# --------------------------------------------------------------------------- blocs
def bloc_gradients():
    sub = "gradients"
    print("\n[gradients]")
    save_png(radial(W, H, (0x12, 0x20, 0x2B), GRAPHITE, cy=0.30, radius=0.95),
             sub, "fond_graphite-projecteur-haut_01.png",
             "graphite avec une source lumineuse haute - le fond de preuve par defaut")
    save_png(radial(W, H, (0x0E, 0x1A, 0x24), (0x03, 0x08, 0x0C), cy=0.5, radius=1.1, falloff=1.2),
             sub, "fond_graphite-profond-centre_02.png",
             "graphite tres sombre, centre a peine releve - pour du texte plein cadre")
    save_png(lin_grad(W, H, (0x0A, 0x14, 0x1C), (0x02, 0x06, 0x09), 90),
             sub, "fond_graphite-vertical-descendant_03.png",
             "graphite qui s'assombrit vers le bas - laisse respirer le haut de cadre")
    save_png(radial(W, H, IVOIRE, (0xDE, 0xDA, 0xCF), cy=0.4, radius=1.0, falloff=1.3),
             sub, "fond_ivoire-chaud-doux_04.png",
             "ivoire chaud - mode perso / editorial, jamais en mode preuve")
    save_png(lin_grad(W, H, IVOIRE, (0xD5, 0xD1, 0xC6), 90),
             sub, "fond_ivoire-vertical_05.png", "ivoire vertical, papier premium")
    save_png(lin_grad(W, H, GRAPHITE, IVOIRE, 90),
             sub, "fond_graphite-vers-ivoire_06.png",
             "bascule graphite -> ivoire : la transition preuve -> humain")
    save_png(lin_grad(W, H, IVOIRE, GRAPHITE, 90),
             sub, "fond_ivoire-vers-graphite_07.png", "bascule inverse, humain -> preuve")
    save_png(tri_grad(W, H, ICE, MINERAL, CYAN, 110),
             sub, "fond_gradient-signature-ice-metal_08.png",
             "LE gradient signature (110deg ice -> mineral -> cyan) - reserve a un chiffre decisif")
    g = radial(W, H, (0x10, 0x1C, 0x26), GRAPHITE, cy=0.32, radius=0.95)
    glow = radial(W, H, SIGNAL, (0, 0, 0), cx=0.5, cy=0.92, radius=0.55, falloff=1.1)
    save_png(np.clip(g + glow * 0.13, 0, 255), sub, "fond_graphite-halo-cyan-bas_09.png",
             "graphite avec un halo cyan bas - signal fonctionnel, reste sous 18% d'opacite")
    save_png(lin_grad(W, H, (0x2A, 0x33, 0x39), (0x0A, 0x12, 0x18), 105),
             sub, "fond_acier-diagonal_10.png", "acier neutre en diagonale - fond de carte technique")
    save_png(np.clip(lin_grad(W, H, (0x0B, 0x16, 0x1F), (0x05, 0x0B, 0x10), 90)
                     + radial(W, H, STEEL, (0, 0, 0), cx=0.22, cy=0.18, radius=0.7) * 0.10, 0, 255),
             sub, "fond_graphite-lumiere-rasante-gauche_11.png",
             "graphite eclaire en rasant depuis la gauche - donne du volume derriere une carte")
    save_png(radial(W, H, (0x1A, 0x26, 0x30), (0x04, 0x09, 0x0D), cx=0.5, cy=0.5, radius=0.62, falloff=2.2),
             sub, "fond_graphite-projecteur-serre_12.png",
             "projecteur serre au centre - isole un objet ou un chiffre")

    # ⛔ ON N'ANIME PLUS LES DEGRADES PURS.
    # Constat du controle qualite (2026-09-11) : meme avec une amplitude quatre
    # fois plus forte, un degrade lisse mesure 0,00 % de pixels en mouvement.
    # Ce n'est pas un probleme d'amplitude — **un degrade n'a aucun detail a
    # deplacer**. Le zoomer produit exactement le meme degrade. Les clips etaient
    # donc des plans fixes de 8 s qui pesaient 40 fois le poids du PNG.
    #
    # Les degrades restent en PNG : au montage, animer les ARRETS DE COULEUR en
    # CSS donne le mouvement voulu, ce qu'un panoramique sur bitmap ne fera jamais.
    # Seuls les fonds qui portent une TEXTURE ou une rampe forte gardent une
    # version video (mesures : texture minerale 12,6 %, gradient signature 47 %).
    for src, nm, z0, z1, dx, dy, d in [
        ("fond_gradient-signature-ice-metal_08.png", "fond-anime_signature-derive_02.mp4", 1.02, 1.38, 620, -420, 6.0),
    ]:
        drift_mp4(dest(sub, src), sub, nm, "derive lente, bouclable, sans point de repere visible",
                  dur=d, zoom_from=z0, zoom_to=z1, dx=dx, dy=dy)


def bloc_grain():
    sub = "grain-et-metal"
    print("\n[grain-et-metal]")
    n = fbm(W, H, octaves=6, seed=7)
    base = np.array(GRAPHITE, dtype=np.float32)[None, None, :]
    save_png(np.clip(base + (n[:, :, None] - 0.5) * 46, 0, 255),
             sub, "texture_graphite-mineral_01.png", "graphite mineral, grain de pierre - fond premium mat")
    n2 = fbm(W, H, octaves=3, seed=21, persistence=0.75)
    streak = np.repeat(n2.mean(axis=1, keepdims=True), W, axis=1)
    streak = streak * 0.55 + n2 * 0.45
    save_png(np.clip(np.array(STEEL, dtype=np.float32)[None, None, :] * 0.42
                     + (streak[:, :, None] - 0.5) * 70, 0, 255),
             sub, "texture_metal-brosse-horizontal_02.png", "metal brosse horizontal - carte technique")
    n3 = fbm(W, H, octaves=6, seed=33)
    save_png(np.clip(np.array(IVOIRE, dtype=np.float32)[None, None, :] - (n3[:, :, None]) * 26, 0, 255),
             sub, "texture_papier-ivoire_03.png", "papier ivoire, grain fin - mode editorial")
    n4 = fbm(W, H, octaves=7, seed=51, persistence=0.62)
    save_png(np.clip(np.array((0x0D, 0x18, 0x21), dtype=np.float32)[None, None, :]
                     + (n4[:, :, None] - 0.5) * 58, 0, 255),
             sub, "texture_beton-graphite_04.png", "beton graphite, grain large - fond de plan large")
    n5 = fbm(W, H, octaves=4, seed=88)
    save_png(np.clip(np.array((0x14, 0x1E, 0x26), dtype=np.float32)[None, None, :]
                     + (n5[:, :, None] - 0.5) * 34, 0, 255),
             sub, "texture_ardoise-douce_05.png", "ardoise douce - fond neutre discret")

    grain_webm(sub, "overlay_grain-argentique-fin_01.webm", "grain argentique fin, alpha - a 8-12% par-dessus n'importe quel plan", dur=4.0, strength=14)
    grain_webm(sub, "overlay_grain-argentique-fort_02.webm", "grain plus marque, alpha - pour un plan qui doit avoir du corps", dur=4.0, strength=30)
    drift_mp4(dest(sub, "texture_graphite-mineral_01.png"), sub,
              "texture-animee_graphite-mineral-derive_01.mp4",
              "le grain mineral qui derive lentement", dur=8.0, zoom_from=1.0, zoom_to=1.34, dx=520, dy=-380)


def bloc_grilles():
    sub = "grilles-et-plans"
    print("\n[grilles-et-plans]")

    def grid(step, thick, color, bg, alpha_bg=None, dot=False):
        img = np.tile(np.array(bg, dtype=np.float32), (H, W, 1))
        c = np.array(color, dtype=np.float32)
        if dot:
            for y in range(0, H, step):
                for x in range(0, W, step):
                    img[y:y + thick, x:x + thick] = c
        else:
            for y in range(0, H, step):
                img[y:y + thick, :] = c
            for x in range(0, W, step):
                img[:, x:x + thick] = c
        return img

    save_png(grid(90, 1, (0x1B, 0x2A, 0x35), GRAPHITE), sub, "grille_fine-graphite_01.png",
             "grille fine graphite - structure discrete derriere une carte")
    save_png(grid(180, 2, (0x21, 0x33, 0x40), GRAPHITE), sub, "grille_large-graphite_02.png",
             "grille large - plan technique, lecture plus calme")
    save_png(grid(60, 3, (0x1E, 0x2E, 0x3A), GRAPHITE, dot=True), sub, "grille_points-graphite_03.png",
             "grille de points - fond de plan facon blueprint")
    save_png(grid(90, 1, (0xDD, 0xD9, 0xCD), IVOIRE), sub, "grille_fine-ivoire_04.png",
             "grille fine sur ivoire - version claire")
    g = grid(120, 2, (0x1F, 0x30, 0x3D), GRAPHITE)
    v = radial(W, H, (255, 255, 255), (0, 0, 0), cy=0.35, radius=0.8, falloff=1.4)
    save_png(np.clip(g * (0.35 + 0.65 * (v[:, :, :1] / 255.0)), 0, 255),
             sub, "grille_projecteur-graphite_05.png",
             "grille qui s'eteint sur les bords - concentre l'oeil au centre")
    drift_mp4(dest(sub, "grille_points-graphite_03.png"), sub, "grille-animee_points-derive_01.mp4",
              "grille de points qui derive - mouvement de fond permanent", dur=8.0,
              zoom_from=1.0, zoom_to=1.28, dx=-520, dy=-520)


def bloc_voiles():
    sub = "vignettes-voiles"
    print("\n[vignettes-voiles]")
    # Le voile de couture du split : impose par le standard de montage verrouille.
    seam = np.zeros((H, W), dtype=np.float32)
    band = 150
    for i in range(band):
        seam[i, :] = 255 * (1 - i / band) ** 1.5
    save_png(np.tile(np.array(GRAPHITE, dtype=np.float32), (H, W, 1)),
             sub, "voile_couture-split-150px_01.png",
             "LA couture du split : graphite -> transparent sur 150px, bord haut du panneau visage",
             alpha=seam)
    top = np.zeros((H, W), dtype=np.float32)
    for i in range(560):
        top[i, :] = 255 * 0.86 * (1 - i / 560) ** 1.25
    save_png(np.tile(np.array(GRAPHITE, dtype=np.float32), (H, W, 1)),
             sub, "voile_haut-lisibilite-texte_02.png",
             "voile haut - obligatoire des qu'un texte est pose sur le visage plein cadre", alpha=top)
    bot = np.zeros((H, W), dtype=np.float32)
    for i in range(620):
        bot[H - 1 - i, :] = 255 * 0.90 * (1 - i / 620) ** 1.25
    save_png(np.tile(np.array(GRAPHITE, dtype=np.float32), (H, W, 1)),
             sub, "voile_bas-sous-titres_03.png",
             "voile bas - assoit les sous-titres sans boite", alpha=bot)
    vig = np.zeros((H, W), dtype=np.float32)
    xs = (np.linspace(-1, 1, W, dtype=np.float32)[None, :])
    ys = (np.linspace(-1, 1, H, dtype=np.float32)[:, None])
    d = np.sqrt(xs ** 2 + (ys * 0.62) ** 2)
    vig = np.clip((d - 0.55) / 0.75, 0, 1) ** 1.4 * 255 * 0.80
    save_png(np.tile(np.array((0x02, 0x05, 0x08), dtype=np.float32), (H, W, 1)),
             sub, "voile_vignette-douce_04.png",
             "vignette douce - resserre le regard, a 40-60% d'opacite", alpha=vig)
    safe = np.zeros((H, W), dtype=np.float32)
    safe[:260, :] = 150
    safe[1550:, :] = 150
    safe[:, :80] = np.maximum(safe[:, :80], 150)
    safe[:, 920:] = np.maximum(safe[:, 920:], 150)
    save_png(np.tile(np.array((0xF2, 0x3B, 0x3B), dtype=np.float32), (H, W, 1)),
             sub, "reperes_safe-zone-instagram_05.png",
             "GABARIT de controle (ne pas exporter) : zone critique x 80..920 / y 260..1550", alpha=safe)


def bloc_lumiere():
    sub = "balayages-lumiere"
    print("\n[balayages-lumiere]")
    sweep = np.zeros((H, W), dtype=np.float32)
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    prof = np.exp(-((xs - 0.5) ** 2) / (2 * 0.055 ** 2))
    sweep[:, :] = prof * 255 * 0.55
    save_png(np.tile(np.array(MINERAL, dtype=np.float32), (H, W, 1)),
             sub, "balayage_bande-mineral_01.png",
             "bande de lumiere minerale - a faire glisser en surimpression", alpha=sweep)
    save_png(np.tile(np.array(ICE, dtype=np.float32), (H, W, 1)),
             sub, "balayage_bande-ice_02.png", "meme bande, teinte ice - reveal d'un chiffre", alpha=sweep * 0.8)
    glow = radial(W, H, (255, 255, 255), (0, 0, 0), cx=0.5, cy=0.42, radius=0.5, falloff=1.5)
    save_png(np.tile(np.array(SIGNAL, dtype=np.float32), (H, W, 1)),
             sub, "halo_signal-centre_03.png",
             "halo cyan centre, alpha - ponctuation, reste sous 18% d'opacite", alpha=glow[:, :, 0] * 0.55)
    save_png(np.tile(np.array((0xFF, 0xF3, 0xDE), dtype=np.float32), (H, W, 1)),
             sub, "halo_chaud-coin-haut-gauche_04.png",
             "halo chaud d'angle - rechauffe un plan visage sans bleuir la peau",
             alpha=radial(W, H, (255, 255, 255), (0, 0, 0), cx=0.12, cy=0.10, radius=0.85, falloff=1.3)[:, :, 0] * 0.45)

    p = dest(sub, "balayage-anime_traverse-mineral_01.mp4")
    ok = run_ff(["-f", "lavfi", "-i", "color=c=0x071017:s=%dx%d:r=%d:d=2.2" % (W, H, FPS),
                 "-loop", "1", "-i", dest(sub, "balayage_bande-mineral_01.png"),
                 "-filter_complex",
                 "[1:v]format=rgba[s];[0:v][s]overlay=x='-W+ (2*W)*t/2.2':y=0:format=auto,format=yuv420p",
                 "-t", "2.2", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-an", p],
                "balayage anime")
    if ok:
        note(sub, os.path.basename(p), "motion", "balayage de lumiere qui traverse le cadre en 2,2 s")
        print("  motion %-52s %s" % (os.path.basename(p), "traverse en 2,2 s"))


def bloc_particules():
    sub = "particules-poussiere"
    print("\n[particules-poussiere]")
    rng = np.random.default_rng(5)
    for idx, (nb, taille, opac, nom, desc) in enumerate([
        (900, 1, 0.55, "poussiere_fine-dense_01.png", "poussiere fine et dense, alpha - profondeur d'air"),
        (260, 2, 0.75, "poussiere_moyenne-clairsemee_02.png", "particules moyennes clairsemees, alpha"),
        (90, 4, 0.85, "poussiere_grosses-bokeh_03.png", "grosses particules facon bokeh, alpha - premier plan"),
    ], 1):
        al = np.zeros((H, W), dtype=np.float32)
        for _ in range(nb):
            x = rng.integers(0, W - taille - 1)
            y = rng.integers(0, H - taille - 1)
            a = rng.random() * 255 * opac
            al[y:y + taille, x:x + taille] = a
        save_png(np.tile(np.array(MINERAL, dtype=np.float32), (H, W, 1)), sub, nom, desc, alpha=al)
    drift_mp4(dest(sub, "poussiere_fine-dense_01.png"), sub, "poussiere-animee_derive-montante_01.mp4",
              "poussiere qui monte (fond noir, a passer en mode ecran)", dur=8.0,
              zoom_from=1.30, zoom_to=1.0, dx=120, dy=-700)


BLOCS = {
    "gradients": bloc_gradients,
    "grain": bloc_grain,
    "grilles": bloc_grilles,
    "voiles": bloc_voiles,
    "lumiere": bloc_lumiere,
    "particules": bloc_particules,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="blocs separes par des virgules : " + ",".join(BLOCS))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k in BLOCS:
            print(k)
        return 0
    noms = [x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)
    for n in noms:
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    man = os.path.join(OUT, "_manifeste-fonds.json")
    os.makedirs(OUT, exist_ok=True)
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-backgrounds.py",
                   "palette": "brand-visual-system.md v1.1",
                   "assets": _produits}, fh, ensure_ascii=False, indent=2)
    print("\n%d fonds produits -> %s" % (len(_produits), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

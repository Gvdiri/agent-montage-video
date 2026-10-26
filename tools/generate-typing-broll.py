#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B-roll de FRAPPE animee - Hyperframes.

Demande du createur (2026-09-10) : « une illustration de quelqu'un en train de
taper un prompt, qu'on zoome sur la barre et que ca s'ecrive ». C'est le plan qui
manquait, et c'est probablement le plus utile de la niche : on parle d'IA, donc
voir un prompt s'ecrire dit le sujet sans un mot de commentaire.

Comment c'est fabrique, et pourquoi :
Chrome rend **une seule fois** la coque de l'interface (fond, en-tete, champ de
saisie) en PNG. Ensuite le texte est dessine image par image avec PIL, puis ffmpeg
assemble. Un lancement de Chrome par frame couterait ~0,5 s x 200 frames par clip ;
la coque unique ramene ca a quelques secondes.

Ligne rouge tenue :
On reproduit l'IDIOME d'une interface connue pour illustrer le GESTE de prompter.
On ne fabrique pas une reponse qui affirmerait une capacite produit — les reponses
affichees restent generiques et neutres. La marque est le decor du geste, pas la
source d'une affirmation.

Usage :
    python tools/generate-typing-broll.py [--only claude-fr,terminal] [--liste]
"""
import os
import re
import sys
import json
import math
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
OUT = os.path.join(BROLL, "02-ecrans-generiques", "chat-ia", "video")
TMP = os.path.join(ROOT, "temp", "_typing")
LOGOS = os.path.join(BROLL, "09-marques-et-logos")
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break

W, H = 1080, 1920

# Geometrie des champs de saisie, partagee entre la coque HTML et le dessin PIL.
# C'est la seule facon d'etre sur que le texte tombe DANS la boite.
CLAUDE_BOX_Y, CLAUDE_BOX_H = 1470, 330
CLAUDE_ZONE = (96, 1508, 888, 250)
BARRE_BOX_Y, BARRE_BOX_H = 660, 470
BARRE_ZONE = (150, 716, 780, 300)
FPS_RENDU = 25            # la frappe reelle tourne autour de 12-15 signes/s
FPS_SORTIE = 60           # le projet est en 60

POLICES = {
    "sans": r"C:\Windows\Fonts\segoeui.ttf",
    "sans-gras": r"C:\Windows\Fonts\seguisb.ttf",
    "mono": r"C:\Windows\Fonts\consola.ttf",
}

_faits = []


def police(nom, taille):
    p = POLICES.get(nom, POLICES["sans"])
    try:
        return ImageFont.truetype(p, taille)
    except Exception:
        return ImageFont.load_default()


def logo_inline(slug, taille=40, couleur=None):
    for r, _, fs in os.walk(LOGOS):
        f = "logo_%s_couleur.svg" % slug
        if f in fs:
            s = open(os.path.join(r, f), encoding="utf-8").read()
            s = s.replace("<svg ", "<svg width='%d' height='%d' style='display:block' " % (taille, taille), 1)
            if couleur:
                s = re.sub(r'fill="#[0-9A-Fa-f]{6}"', 'fill="%s"' % couleur, s, count=1)
            return s
    return ""


def rendre_coque(nom, html):
    """Une seule capture Chrome par coque."""
    os.makedirs(TMP, exist_ok=True)
    hp = os.path.join(TMP, "%s.html" % nom)
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write(html)
    png = os.path.join(TMP, "%s.png" % nom)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--screenshot=%s" % png,
                    "--window-size=%d,%d" % (W, H), "--virtual-time-budget=1400",
                    "file:///%s" % hp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=90)
    return png if os.path.isfile(png) else None


def envelopper(corps, css=""):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>"
            "*{box-sizing:border-box;margin:0;padding:0}"
            "html,body{width:%dpx;height:%dpx;overflow:hidden}"
            "body{font-family:'Segoe UI',system-ui,sans-serif;-webkit-font-smoothing:antialiased}"
            "%s</style></head><body>%s</body></html>" % (W, H, css, corps))


def couper_lignes(texte, fonte, largeur_max, dessin):
    """Retour a la ligne au mot, comme un vrai champ de saisie."""
    mots = texte.split(" ")
    lignes, courante = [], ""
    for m in mots:
        essai = (courante + " " + m).strip()
        if dessin.textlength(essai, font=fonte) <= largeur_max or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = m
    if courante:
        lignes.append(courante)
    return lignes or [""]      # un contenu d'espaces seules renvoyait [] -> IndexError


def assembler(frames_dir, sortie, fps_rendu=FPS_RENDU):
    ok = subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-framerate", str(fps_rendu), "-i", os.path.join(frames_dir, "f%05d.png"),
         "-vf", "fps=%d,format=yuv420p" % FPS_SORTIE,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", sortie],
        capture_output=True, text=True)
    if ok.returncode != 0:
        print("  ! assemblage : %s" % (ok.stderr or "")[:150])
        return False
    return True


def produire(nom, coque_png, zone, texte, desc, taille=44, couleur="#1F1E1D",
             fonte="sans", vitesse=14.0, pause_avant=0.5, pause_apres=1.6,
             coque_apres=None, zone_apres=None, reponse=None, vitesse_reponse=26.0):
    """Ecrit `texte` dans `zone` (x, y, largeur, hauteur) frame par frame."""
    base = Image.open(coque_png).convert("RGB")
    f = police(fonte, taille)
    d0 = ImageDraw.Draw(base)
    x, y, lw, lh = zone
    interligne = int(taille * 1.42)

    frames = os.path.join(TMP, "frames_" + nom)
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames, exist_ok=True)

    n_avant = int(pause_avant * FPS_RENDU)
    n_texte = int(len(texte) / vitesse * FPS_RENDU)
    n_apres = int(pause_apres * FPS_RENDU)
    i = 0

    def poser(img, contenu, curseur, zx, zy, zlw, fonte_, coul, inter):
        im = img.copy()
        dr = ImageDraw.Draw(im)
        lignes = couper_lignes(contenu, fonte_, zlw, dr) if contenu else [""]
        for k, ligne in enumerate(lignes):
            dr.text((zx, zy + k * inter), ligne, font=fonte_, fill=coul)
        if curseur:
            der = lignes[-1]
            cx = zx + dr.textlength(der, font=fonte_)
            cy = zy + (len(lignes) - 1) * inter
            dr.rectangle([cx + 2, cy + 3, cx + 5, cy + fonte_.size + 4], fill=coul)
        return im

    # 1) attente, curseur qui clignote
    for k in range(n_avant):
        clign = (k // int(FPS_RENDU * 0.55)) % 2 == 0
        poser(base, "", clign, x, y, lw, f, couleur, interligne).save(
            os.path.join(frames, "f%05d.png" % i)); i += 1

    # 2) la frappe
    for k in range(n_texte):
        n_car = int(len(texte) * (k + 1) / max(n_texte, 1))
        poser(base, texte[:n_car], True, x, y, lw, f, couleur, interligne).save(
            os.path.join(frames, "f%05d.png" % i)); i += 1

    # 3) texte complet, curseur qui clignote
    for k in range(n_apres):
        clign = (k // int(FPS_RENDU * 0.55)) % 2 == 0
        poser(base, texte, clign, x, y, lw, f, couleur, interligne).save(
            os.path.join(frames, "f%05d.png" % i)); i += 1

    # 4) reponse en flux, sur la seconde coque
    if reponse and coque_apres and zone_apres:
        b2 = Image.open(coque_apres).convert("RGB")
        f2 = police("sans", 40)
        x2, y2, lw2, _ = zone_apres
        inter2 = int(40 * 1.5)
        n_rep = int(len(reponse) / vitesse_reponse * FPS_RENDU)
        for k in range(int(0.35 * FPS_RENDU)):     # petit temps de latence
            b2.save(os.path.join(frames, "f%05d.png" % i)); i += 1
        for k in range(n_rep):
            n_car = int(len(reponse) * (k + 1) / max(n_rep, 1))
            poser(b2, reponse[:n_car], False, x2, y2, lw2, f2, "#1F1E1D", inter2).save(
                os.path.join(frames, "f%05d.png" % i)); i += 1
        for k in range(int(1.4 * FPS_RENDU)):
            poser(b2, reponse, False, x2, y2, lw2, f2, "#1F1E1D", inter2).save(
                os.path.join(frames, "f%05d.png" % i)); i += 1

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "frappe_%s.mp4" % nom)
    if assembler(frames, dest):
        _faits.append(dict(fichier=os.path.basename(dest), description=desc,
                           duree_s=round(i / FPS_RENDU, 2), texte=texte))
        print("  %-46s %4.1fs  %s" % (os.path.basename(dest), i / FPS_RENDU, desc))
    shutil.rmtree(frames, ignore_errors=True)


# =========================================================== COQUES / SCENES
def coque_claude(avec_prompt=None):
    """Fond ivoire chaud, logo etoile + serif : releve sur la vraie page."""
    logo = logo_inline("claude", 46)
    corps = ("<div style='width:100vw;height:100vh;background:#FAF9F5;display:flex;"
             "flex-direction:column'>"
             "<div style='padding:34px 40px;display:flex;align-items:center;gap:12px'>"
             "%s<span style='font-family:Georgia,serif;font-size:34px;color:#1F1E1D'>Claude</span></div>"
             % logo)
    if avec_prompt:
        corps += ("<div style='flex:1;padding:40px'>"
                  "<div style='display:flex;justify-content:flex-end;margin-bottom:34px'>"
                  "<div style='max-width:78%%;background:#F0EEE6;border-radius:20px;padding:20px 26px;"
                  "font-size:40px;color:#1F1E1D;line-height:1.4'>%s</div></div>"
                  "<div style='display:flex;gap:18px'>%s<div style='flex:1'></div></div></div>"
                  % (avec_prompt, logo_inline("claude", 40)))
    else:
        # Le champ est place en absolu : PIL doit savoir exactement ou ecrire.
        # Avec un centrage par le flux CSS, la boite bougeait et le texte se
        # dessinait au-dessus d'elle.
        corps += ("<div style='position:absolute;left:0;right:0;top:1080px;text-align:center;"
                  "font-family:Georgia,serif;font-size:52px;color:#3D3A34'>"
                  "Par quoi on commence&nbsp;?</div>"
                  "<div style='position:absolute;left:60px;right:60px;top:%dpx;height:%dpx;"
                  "background:#FFF;border:1px solid #E5E1D8;border-radius:26px;"
                  "box-shadow:0 2px 10px rgba(0,0,0,.04)'>"
                  "<div style='position:absolute;right:26px;bottom:24px;width:62px;height:62px;"
                  "border-radius:50%%;background:#1F1E1D;display:grid;place-items:center;"
                  "color:#FFF;font-size:26px'>&#8593;</div></div>" % (CLAUDE_BOX_Y, CLAUDE_BOX_H))
    return envelopper(corps)


def coque_barre(marque, fond, bordure, carte="#FFF", fleche="#1F1E1D", encre="#FFF"):
    """Zoom serre sur le champ de saisie — le cadrage demande par le createur.

    `carte` / `fleche` / `encre` ont ete ajoutes le 2026-09-22 : la coque etait
    forcee en blanc, et posee plein panneau dans un montage graphite elle faisait
    un trou de lumiere (le defaut « pixels clairs » releve sur le Reel #23).
    Les valeurs par defaut reproduisent exactement l'ancien rendu.
    """
    corps = ("<div style='width:100vw;height:100vh;background:%s'>"
             "<div style='position:absolute;left:46px;right:46px;top:%dpx;height:%dpx;"
             "background:%s;border:2px solid %s;border-radius:34px;"
             "box-shadow:0 6px 28px rgba(0,0,0,.07)'>"
             "<div style='position:absolute;left:44px;bottom:36px;display:flex;gap:18px;"
             "align-items:center'>%s</div>"
             "<div style='position:absolute;right:40px;bottom:32px;width:66px;height:66px;"
             "border-radius:50%%;background:%s;display:grid;place-items:center;"
             "color:%s;font-size:28px'>&#8593;</div>"
             "</div></div>"
             % (fond, BARRE_BOX_Y, BARRE_BOX_H, carte, bordure, marque, fleche, encre))
    return envelopper(corps)


def coque_terminal():
    corps = ("<div style='width:100vw;height:100vh;background:#0C1117;display:flex;"
             "flex-direction:column'>"
             "<div style='height:78px;background:#161B22;border-bottom:1px solid #232A33;"
             "display:flex;align-items:center;padding:0 28px;gap:12px'>"
             "<div style='width:16px;height:16px;border-radius:50%;background:#F35C4E'></div>"
             "<div style='width:16px;height:16px;border-radius:50%;background:#F5BE4F'></div>"
             "<div style='width:16px;height:16px;border-radius:50%;background:#5FC454'></div></div>"
             "<div style='padding:44px 40px;font-family:Consolas,monospace;font-size:38px;"
             "color:#6B7A8C'>~/projet <span style='color:#4ADE80'>&#10095;</span></div></div>")
    return envelopper(corps)


def bloc_prompts():
    print("\n[frappe de prompt]")
    if CHROME is None:
        print("  ! Chrome introuvable")
        return

    # --- plein cadre, interface facon Claude
    c_vide = rendre_coque("claude-vide", coque_claude())
    if c_vide:
        produire("claude-fr-argent", c_vide, CLAUDE_ZONE,
                 "Voilà mon export bancaire. Dis-moi où part mon argent.",
                 "prompt tapé en français dans une interface façon Claude", taille=42)
        produire("claude-fr-role", c_vide, CLAUDE_ZONE,
                 "T'es expert en négociation. Un client trouve mon devis trop cher.",
                 "prompt avec un rôle assigné — le réflexe qu'on enseigne", taille=42)
        produire("claude-en", c_vide, CLAUDE_ZONE,
                 "Find the flaws in my plan before I ship it.",
                 "le même geste, en anglais", taille=42)

    # --- zoom serre sur la barre : le cadrage demande
    marque_claude = ("%s<span style='font-size:30px;color:#8A857A'>Claude</span>"
                     % logo_inline("claude", 34))
    c_barre = rendre_coque("barre-claude", coque_barre(marque_claude, "#FAF9F5", "#E5E1D8"))
    if c_barre:
        produire("barre-claude-automatiser", c_barre, BARRE_ZONE,
                 "Automatise le tri de mes emails et la relance de mes devis.",
                 "ZOOM sur la barre de saisie — le plan demandé", taille=54)
        produire("barre-claude-explique", c_barre, BARRE_ZONE,
                 "Explique-moi ça comme si j'y connaissais rien.",
                 "zoom barre — le premier des 3 prompts du script", taille=54)

    marque_gpt = ("<div style='width:34px;height:34px;border-radius:50%;background:#000'></div>"
                  "<span style='font-size:30px;color:#8E8EA0'>Poser une question</span>")
    c_barre2 = rendre_coque("barre-sombre", coque_barre(marque_gpt, "#F7F7F8", "#D9D9E3"))
    if c_barre2:
        produire("barre-generique-agent", c_barre2, BARRE_ZONE,
                 "Crée-moi un agent qui répond à mes prospects sur WhatsApp.",
                 "zoom barre, interface générique — réutilisable partout", taille=54)

    # --- prompt puis reponse en flux
    c_rep = rendre_coque("claude-reponse",
                         coque_claude(avec_prompt="Où part mon argent&nbsp;?"))
    if c_vide and c_rep:
        produire("claude-fr-avec-reponse", c_vide, CLAUDE_ZONE,
                 "Où part mon argent ?",
                 "on tape, on envoie, la réponse s'écrit — le plan le plus complet",
                 taille=42, pause_apres=0.7,
                 coque_apres=c_rep, zone_apres=(160, 620, 800, 700),
                 reponse="Trois postes pèsent 71 % de tes dépenses. La publicité "
                         "arrive en tête, suivie des abonnements outils.")


def bloc_terminal():
    print("\n[frappe en terminal]")
    if CHROME is None:
        return
    c = rendre_coque("terminal", coque_terminal())
    if not c:
        return
    produire("terminal-agent-run", c, (262, 148, 780, 300),   # decale : le chevron ne colle pas
             'agent run --tache "relancer les devis"',
             "une commande qui se tape dans un terminal", taille=38,
             couleur="#E6EDF3", fonte="mono", vitesse=11.0)
    produire("terminal-npm-run", c, (262, 148, 780, 300),
             "npm run build",
             "commande courte — bon pour une coupe de 2 s", taille=38,
             couleur="#E6EDF3", fonte="mono", vitesse=9.0, pause_apres=1.0)


BLOCS = {"prompts": bloc_prompts, "terminal": bloc_terminal}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    if a.liste:
        print("\n".join(BLOCS))
        return 0
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    man = os.path.join(BROLL, "_manifeste-frappe.json")
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-typing-broll.py",
                   "principe": "l'idiome d'une interface connue pour illustrer le GESTE de "
                               "prompter ; jamais une reponse qui affirmerait une capacite produit",
                   "clips": _faits}, fh, ensure_ascii=False, indent=2)
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n%d clips de frappe" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())

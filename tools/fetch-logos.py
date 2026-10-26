#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Banque de logos produits - Hyperframes.

Regle permanente du projet (EDITING_SYSTEM, redemandee explicitement le 2026-08-22) :
tout nom de marque prononce porte son logo a l'ecran, en couleurs produit par defaut.
Et : "ne jamais dessiner l'approximation d'un logo connu ; un faux logo est pire que
pas de logo".

Source : cdn.simpleicons.org, qui renvoie le TRACE OFFICIEL de la marque deja rempli
a sa couleur officielle.

⚠️ LIMITE ASSUMEE ET MARQUEE FICHIER PAR FICHIER :
Simple Icons ne fournit qu'un tracé monochrome. Pour une marque dont le vrai logo est
monochrome (Anthropic, OpenAI, GitHub, Notion...) c'est le logo exact. Pour une marque
multicolore ou en degrade (Figma, Slack, Google, Instagram, Canva...) c'est une
SIMPLIFICATION : la forme est officielle, la colorimetrie ne l'est pas.

Le manifeste porte donc un champ `fidelite` :
  - "exact"     -> utilisable partout, y compris quand la marque est le sujet du plan
  - "simplifie" -> bon pour une LISTE DE CONNECTEURS (cas que la charte autorise en
                   monochrome) ; si la marque est le SUJET du plan, aller chercher le
                   lockup officiel sur sa page presse.

Usage :
    python tools/fetch-logos.py [--only slug1,slug2]
"""
import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "09-marques-et-logos")
IVOIRE = "F3F1EA"

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break

# (slug simple-icons, nom affiche, famille, fidelite)
# fidelite "simplifie" = le vrai logo est multicolore ou en degrade.
MARQUES = [
    # --- modeles et assistants IA
    ("anthropic", "Anthropic", "ia", "exact"),
    ("claude", "Claude", "ia", "exact"),
    ("openai", "OpenAI", "ia", "exact"),
    ("googlegemini", "Gemini", "ia", "simplifie"),
    ("perplexity", "Perplexity", "ia", "exact"),
    ("mistralai", "Mistral AI", "ia", "simplifie"),
    ("huggingface", "Hugging Face", "ia", "simplifie"),
    ("ollama", "Ollama", "ia", "exact"),
    ("googlecolab", "Colab", "ia", "simplifie"),
    # --- automatisation
    ("n8n", "n8n", "automatisation", "exact"),
    ("zapier", "Zapier", "automatisation", "exact"),
    ("make", "Make", "automatisation", "simplifie"),
    ("airtable", "Airtable", "automatisation", "simplifie"),
    ("notion", "Notion", "automatisation", "exact"),
    ("obsidian", "Obsidian", "automatisation", "simplifie"),
    ("slack", "Slack", "automatisation", "simplifie"),
    ("discord", "Discord", "automatisation", "exact"),
    ("telegram", "Telegram", "automatisation", "exact"),
    ("whatsapp", "WhatsApp", "automatisation", "exact"),
    # --- dev et design
    ("github", "GitHub", "dev", "exact"),
    ("git", "Git", "dev", "exact"),
    ("figma", "Figma", "dev", "simplifie"),
    ("vercel", "Vercel", "dev", "exact"),
    ("nodedotjs", "Node.js", "dev", "exact"),
    ("python", "Python", "dev", "simplifie"),
    ("docker", "Docker", "dev", "exact"),
    ("visualstudiocode", "VS Code", "dev", "exact"),
    ("playwright", "Playwright", "dev", "simplifie"),
    ("supabase", "Supabase", "dev", "exact"),
    # --- creation
    ("canva", "Canva", "creation", "simplifie"),
    ("adobe", "Adobe", "creation", "exact"),
    ("davinciresolve", "DaVinci Resolve", "creation", "simplifie"),
    ("elevenlabs", "ElevenLabs", "creation", "exact"),
    ("capcut", "CapCut", "creation", "simplifie"),
    # --- commerce
    ("shopify", "Shopify", "commerce", "exact"),
    ("stripe", "Stripe", "commerce", "exact"),
    ("wordpress", "WordPress", "commerce", "exact"),
    ("webflow", "Webflow", "commerce", "exact"),
    ("woocommerce", "WooCommerce", "commerce", "exact"),
    # --- reseaux
    ("instagram", "Instagram", "reseaux", "simplifie"),
    ("tiktok", "TikTok", "reseaux", "simplifie"),
    ("youtube", "YouTube", "reseaux", "exact"),
    ("linkedin", "LinkedIn", "reseaux", "exact"),
    ("x", "X", "reseaux", "exact"),
    ("facebook", "Facebook", "reseaux", "exact"),
    ("threads", "Threads", "reseaux", "exact"),
    ("meta", "Meta", "reseaux", "simplifie"),
    # --- plateformes
    ("google", "Google", "plateformes", "simplifie"),
    ("googledrive", "Google Drive", "plateformes", "simplifie"),
    ("googlesheets", "Google Sheets", "plateformes", "exact"),
    ("googlecalendar", "Google Agenda", "plateformes", "exact"),
    ("gmail", "Gmail", "plateformes", "simplifie"),
    ("apple", "Apple", "plateformes", "exact"),
    ("samsung", "Samsung", "plateformes", "exact"),
    ("amazon", "Amazon", "plateformes", "exact"),
    ("nvidia", "NVIDIA", "plateformes", "exact"),
    ("cloudflare", "Cloudflare", "plateformes", "simplifie"),
]

_faits = []


# Repli AUTORISE uniquement pour les marques dont le repere est monochrome par nature
# ET dont la couleur a ete verifiee a la main. jsdelivr renvoie le trace SANS
# remplissage, donc sans cette table on ne saurait pas quoi mettre.
#
# ⛔ AUCUN REPLI PAR DEFAUT. Un logo dont on n'a pas la couleur officielle doit
# echouer bruyamment. La version precedente peignait en #191919 tout ce qui n'etait
# pas dans cette table : LinkedIn, Amazon, Adobe et Canva se sont retrouves en
# silhouette noire alors que leurs couleurs sont bleu, orange, rouge et cyan.
# C'est precisement le "faux logo" que la charte interdit ("product colors remain
# truthful", "ne jamais dessiner l'approximation d'un logo connu").
#
# Ces quatre marques ont ete RETIREES de Simple Icons pour raisons de marque
# deposee. On ne contourne pas : on les source a la main sur leur page presse.
REPLI_HEX = {"openai": "#000000"}      # le repere OpenAI est noir, verifie


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hyperframes-asset-library"})
    with urllib.request.urlopen(req, timeout=25) as r:
        if r.status != 200:
            raise RuntimeError("HTTP %s" % r.status)
        return r.read().decode("utf-8")


def telecharger(slug, couleur=None):
    url = "https://cdn.simpleicons.org/%s" % slug
    if couleur:
        url += "/%s" % couleur
    try:
        return _get(url)
    except Exception:
        if not couleur and slug not in REPLI_HEX:
            raise RuntimeError("retire de Simple Icons — a sourcer sur la page presse")
        svg = _get("https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/%s.svg" % slug)
        teinte = ("#" + couleur) if couleur else REPLI_HEX[slug]
        return svg.replace("<svg ", "<svg fill=\"%s\" " % teinte, 1)


def hex_de(svg):
    if 'fill="#' in svg:
        i = svg.index('fill="#')
        return svg[i + 6:i + 13]
    return None


def png_depuis_svg(chemin_svg, chemin_png, cote=512):
    """Rendu PNG a fond transparent, via Chrome headless."""
    if CHROME is None:
        return False
    html = os.path.splitext(chemin_png)[0] + ".__tmp.html"
    with open(chemin_svg, encoding="utf-8") as fh:
        svg = fh.read()
    svg = svg.replace("<svg ", "<svg width='%d' height='%d' " % (cote, cote), 1)
    with open(html, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><meta charset='utf-8'><style>*{margin:0;padding:0}"
                 "html,body{width:%dpx;height:%dpx;background:transparent}</style>%s"
                 % (cote, cote, svg))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--force-device-scale-factor=1",
                    "--screenshot=%s" % chemin_png, "--window-size=%d,%d" % (cote, cote),
                    "--virtual-time-budget=900", "file:///%s" % html.replace("\\", "/")],
                   capture_output=True, text=True, timeout=60)
    if os.path.isfile(html):
        os.remove(html)
    return os.path.isfile(chemin_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    cibles = MARQUES
    if a.only:
        garde = {x.strip() for x in a.only.split(",")}
        cibles = [m for m in MARQUES if m[0] in garde]

    echecs = []
    for slug, nom, famille, fidelite in cibles:
        d = os.path.join(OUT, famille)
        os.makedirs(d, exist_ok=True)
        try:
            svg_c = telecharger(slug)
            svg_i = telecharger(slug, IVOIRE)
        except Exception as e:
            print("  ! %-18s introuvable (%s)" % (slug, e))
            echecs.append(slug)
            continue

        p_c = os.path.join(d, "logo_%s_couleur.svg" % slug)
        p_i = os.path.join(d, "logo_%s_ivoire.svg" % slug)
        with open(p_c, "w", encoding="utf-8") as fh:
            fh.write(svg_c)
        with open(p_i, "w", encoding="utf-8") as fh:
            fh.write(svg_i)
        p_png = os.path.join(d, "logo_%s_couleur.png" % slug)
        png_depuis_svg(p_c, p_png)

        h = hex_de(svg_c)
        _faits.append(dict(slug=slug, nom=nom, famille=famille, fidelite=fidelite,
                           couleur=h, svg_couleur=os.path.basename(p_c),
                           svg_ivoire=os.path.basename(p_i),
                           png=os.path.basename(p_png) if os.path.isfile(p_png) else None))
        marque = "" if fidelite == "exact" else "   [!] simplifie (vrai logo multicolore)"
        print("  %-18s %-16s %s%s" % (slug, nom, h or "?", marque))
        time.sleep(0.12)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "_manifeste.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": "cdn.simpleicons.org (trace officiel + couleur de marque)",
                   "limite": "trace monochrome uniquement ; voir le champ fidelite",
                   "logos": _faits, "echecs": echecs}, fh, ensure_ascii=False, indent=2)

    exacts = [f for f in _faits if f["fidelite"] == "exact"]
    simpl = [f for f in _faits if f["fidelite"] == "simplifie"]
    L = ["# Logos produits — banque",
         "",
         "> Généré par `tools/fetch-logos.py`. Source : `cdn.simpleicons.org` — **tracé officiel**",
         "> de la marque, rempli à sa **couleur officielle**.",
         "",
         "## La règle",
         "",
         "Tout nom de marque prononcé porte son logo à l'écran, **en couleurs produit par défaut**.",
         "Tailles planchers mesurées : **42 px** en tuile de grille, **36 px** en barre de titre de",
         "carte, **150 px** en plein cadre, à 0,96 d'opacité. Un logo présent mais trop petit ne",
         "fait pas le travail.",
         "",
         "Exception monochrome ivoire, autorisée dans deux cas seulement : une **liste de",
         "connecteurs** (trois logos saturés côte à côte feraient un mur de logos), et les marques",
         "**monochromes par nature**. Les fichiers `_ivoire.svg` sont là pour ça.",
         "",
         "## ⚠️ Fidélité — à lire avant de poser un logo",
         "",
         "Simple Icons ne fournit qu'un **tracé monochrome**.",
         "",
         "- **`exact` (%d marques)** — le vrai logo est monochrome. Utilisable partout, y compris" % len(exacts),
         "  quand la marque est le **sujet** du plan.",
         "- **`simplifie` (%d marques)** — le vrai logo est multicolore ou en dégradé. La **forme**" % len(simpl),
         "  est officielle, **la colorimétrie ne l'est pas**. Bon pour une liste de connecteurs ;",
         "  si la marque est le sujet du plan, aller chercher le lockup officiel sur sa page presse.",
         "",
         "## Inventaire",
         ""]
    for fam in sorted({f["famille"] for f in _faits}):
        dedans = [f for f in _faits if f["famille"] == fam]
        L += ["### %s — %d" % (fam, len(dedans)), "",
              "| marque | couleur | fidélité | fichier |", "|---|---|---|---|"]
        for f in sorted(dedans, key=lambda x: x["nom"]):
            L.append("| %s | `%s` | %s | `%s` |" % (
                f["nom"], f["couleur"] or "?",
                "exact" if f["fidelite"] == "exact" else "⚠️ simplifié", f["svg_couleur"]))
        L.append("")
    if echecs:
        L += ["## Introuvables", "", ", ".join("`%s`" % e for e in echecs),
              "", "À sourcer à la main sur la page presse de la marque.", ""]
    with open(os.path.join(OUT, "LISEZ-MOI.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print("\n%d logos (%d exacts · %d simplifies) · %d echecs"
          % (len(_faits), len(exacts), len(simpl), len(echecs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

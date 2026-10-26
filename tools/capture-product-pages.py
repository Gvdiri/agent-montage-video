#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Captures reelles de pages produits - Hyperframes.

C'est la SEULE categorie de la bibliotheque b-roll qui doit rester reelle.
La contrainte "captures reelles uniquement" a ete levee le 2026-09-10 pour tout
le reste (illustrations, fonds, ecrans generiques), mais fabriquer l'ecran d'un
produit NOMME et le presenter comme sa vraie interface reste exclu : ce n'est plus
une illustration, c'est une affirmation factuelle et elle est verifiable.

Bannieres de cookies : on ne clique sur rien. Une banniere en position fixe s'ancre
au BAS DU VIEWPORT — on rend donc dans une fenetre tres haute et on recadre le haut,
ce qui la fait sortir du cadre sans qu'aucun consentement ne soit donne ni refuse.
Les bandeaux hauts, eux, restent : ils font partie de la vraie page.

Usage :
    python tools/capture-product-pages.py [--only slug1,slug2] [--liste]
"""
import os
import sys
import json
import time
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "01-ecrans-produits")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break

LARGEUR = 1600
HAUT_RENDU = 3600      # fenetre haute : repousse les bannieres fixes hors du recadrage
HAUT_GARDE = 1000      # la capture "carte", pour un panneau de preuve
HAUT_LONGUE = 3000     # une version longue, gardee pour le b-roll de defilement
                       # (on coupe les 600 derniers px : c'est la que se pose la
                       #  banniere de cookies ancree en bas du viewport)

# (slug, url, famille, description)
PAGES = [
    # --- assistants IA
    ("claude-accueil", "https://claude.ai", "ia-assistants", "page d'accueil de Claude"),
    ("anthropic-claude", "https://www.anthropic.com/claude", "ia-assistants", "page produit Claude chez Anthropic"),
    ("anthropic-pricing", "https://www.anthropic.com/pricing", "ia-assistants", "grille tarifaire Anthropic"),
    ("chatgpt-accueil", "https://chatgpt.com", "ia-assistants", "page d'accueil de ChatGPT"),
    ("openai-accueil", "https://openai.com", "ia-assistants", "page d'accueil d'OpenAI"),
    ("gemini-accueil", "https://gemini.google.com", "ia-assistants", "page d'accueil de Gemini"),
    ("perplexity-accueil", "https://www.perplexity.ai", "ia-assistants", "page d'accueil de Perplexity"),
    ("mistral-accueil", "https://mistral.ai", "ia-assistants", "page d'accueil de Mistral AI"),
    # --- automatisation
    ("n8n-accueil", "https://n8n.io", "automatisation", "page d'accueil de n8n"),
    ("n8n-templates", "https://n8n.io/workflows/", "automatisation", "bibliotheque de workflows n8n"),
    ("zapier-accueil", "https://zapier.com", "automatisation", "page d'accueil de Zapier"),
    ("make-accueil", "https://www.make.com", "automatisation", "page d'accueil de Make"),
    ("airtable-accueil", "https://www.airtable.com", "automatisation", "page d'accueil d'Airtable"),
    ("notion-accueil", "https://www.notion.com", "automatisation", "page d'accueil de Notion"),
    # --- creation video / voix
    ("heygen-accueil", "https://www.heygen.com", "creation-video", "page d'accueil de HeyGen"),
    ("elevenlabs-accueil", "https://elevenlabs.io", "creation-video", "page d'accueil d'ElevenLabs"),
    ("elevenlabs-sfx", "https://elevenlabs.io/sound-effects", "creation-video", "generateur d'effets sonores ElevenLabs"),
    # --- design / dev
    ("figma-accueil", "https://www.figma.com", "design-dev", "page d'accueil de Figma"),
    ("github-accueil", "https://github.com", "design-dev", "page d'accueil de GitHub"),
    # Pages GitHub reelles — signalees manquantes par le createur. Depots publics,
    # donc capturables telles quelles : c'est la categorie qui DOIT rester reelle.
    ("github-depot", "https://github.com/n8n-io/n8n", "design-dev", "page d'un dépôt GitHub réel"),
    ("github-depot-ia", "https://github.com/langchain-ai/langchain", "design-dev", "dépôt GitHub d'un projet IA"),
    ("github-commits", "https://github.com/n8n-io/n8n/commits/master", "design-dev", "historique de commits GitHub"),
    ("github-code", "https://github.com/n8n-io/n8n/blob/master/README.md", "design-dev", "fichier affiché dans GitHub"),
    ("github-issues", "https://github.com/n8n-io/n8n/issues", "design-dev", "liste d'issues GitHub"),
    ("github-pulls", "https://github.com/langchain-ai/langchain/pulls", "design-dev", "liste de pull requests"),
    ("github-tendances", "https://github.com/trending", "design-dev", "dépôts en tendance sur GitHub"),
    ("github-actions", "https://github.com/n8n-io/n8n/actions", "design-dev", "exécutions GitHub Actions"),
    ("vercel-accueil", "https://vercel.com", "design-dev", "page d'accueil de Vercel"),
    ("playwright-accueil", "https://playwright.dev", "design-dev", "page d'accueil de Playwright"),
    # --- commerce / SaaS
    ("shopify-accueil", "https://www.shopify.com", "commerce-saas", "page d'accueil de Shopify"),
    ("shopify-apps", "https://apps.shopify.com", "commerce-saas", "boutique d'applications Shopify"),
    ("stripe-accueil", "https://stripe.com", "commerce-saas", "page d'accueil de Stripe"),
    ("webflow-accueil", "https://webflow.com", "commerce-saas", "page d'accueil de Webflow"),
]

_faits = []


def capturer(slug, url, famille, desc):
    d = os.path.join(OUT, famille)
    os.makedirs(d, exist_ok=True)
    brut = os.path.join(d, "__brut_%s.png" % slug)
    final = os.path.join(d, "capture_%s.png" % slug)
    r = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", "--screenshot=%s" % brut,
         "--window-size=%d,%d" % (LARGEUR, HAUT_RENDU),
         "--virtual-time-budget=11000",
         "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
         url],
        capture_output=True, text=True, timeout=150)
    if not os.path.isfile(brut):
        print("  ! %-22s echec de rendu" % slug)
        return False
    longue = None
    try:
        im = Image.open(brut).convert("RGB")
        im.crop((0, 0, LARGEUR, min(HAUT_GARDE, im.size[1]))).save(final, optimize=True)
        if im.size[1] > HAUT_GARDE + 400:
            dl = os.path.join(d, "_longues")
            os.makedirs(dl, exist_ok=True)
            longue = os.path.join(dl, "capture_%s_longue.png" % slug)
            im.crop((0, 0, LARGEUR, min(HAUT_LONGUE, im.size[1]))).save(longue, optimize=True)
    finally:
        if os.path.isfile(brut):
            os.remove(brut)
    ko = os.path.getsize(final) // 1024
    _faits.append(dict(slug=slug, url=url, famille=famille, description=desc,
                       fichier=os.path.basename(final),
                       version_longue=os.path.basename(longue) if longue else None,
                       capture_le=time.strftime("%Y-%m-%d")))
    print("  %-22s %-16s %5d ko  %s" % (slug, famille, ko, desc))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    if a.liste:
        for s, u, f, d in PAGES:
            print("%-22s %-16s %s" % (s, f, u))
        return 0
    if CHROME is None:
        print("Chrome introuvable")
        return 1
    cibles = PAGES
    if a.only:
        g = {x.strip() for x in a.only.split(",")}
        cibles = [p for p in PAGES if p[0] in g]
    for slug, url, famille, desc in cibles:
        try:
            capturer(slug, url, famille, desc)
        except Exception as e:
            print("  ! %-22s %s" % (slug, str(e)[:90]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "_manifeste.json"), "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/capture-product-pages.py",
                   "note": "captures reelles de pages publiques ; recadrees en haut de page",
                   "captures": _faits}, fh, ensure_ascii=False, indent=2)
    print("\n%d captures" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())

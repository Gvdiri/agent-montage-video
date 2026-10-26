#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Logos officiels depuis Wikimedia Commons - Hyperframes.

Deux usages, tous deux pour AMELIORER l'authenticite de la banque :

1. `--manquants` : les marques absentes de Simple Icons (L'Oreal, Decathlon,
   La Poste, BlaBlaCar, Le Monde...). Commons en heberge les logos officiels.

2. `--multicolores` : Simple Icons ne fournit que du MONOCHROME. Commons heberge
   souvent le vrai logo **en couleurs**. Pour Figma, Google, Slack, Instagram...
   c'est un vrai gain de fidelite : on remplace une silhouette approchee par le
   logo authentique.

Les fichiers Commons gardent leur nom d'origine dans le manifeste, avec l'URL de
la page de description : c'est la que vivent l'auteur et la licence.

Usage :
    python tools/fetch-logos-commons.py --manquants
    python tools/fetch-logos-commons.py --multicolores
"""
import os
import re
import sys
import json
import time
import argparse
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "09-marques-et-logos")
API = "https://commons.wikimedia.org/w/api.php"
UA = "hyperframes-asset-library/1.0 (contact@example.com)"

# Mots qui signalent une version ancienne ou secondaire : on les evite.
MALUS = ("1976", "1980", "1990", "1995", "1999", "2000", "2005", "2008", "2010",
         "2012", "old", "ancien", "former", "history", "historique", "vertical",
         "black", "white", "grayscale", "monochrome", "outline", "wordmark only",
         "inverted", "negative", "draft", "unofficial", "fan", "concept")
BONUS = ("2024", "2023", "2025", "2026", "current", "actuel")


def _get(url, bin=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = r.read()
        return d if bin else d.decode("utf-8")


def chercher(marque, nb=8):
    q = urllib.parse.quote("%s logo" % marque)
    u = "%s?action=query&format=json&list=search&srsearch=%s&srnamespace=6&srlimit=%d" % (API, q, nb)
    return [r["title"] for r in json.loads(_get(u)).get("query", {}).get("search", [])]


def _plat(x):
    return re.sub(r"[^a-z0-9]", "", x.lower())


# Mots de decor qu'on retire du titre avant de comparer au nom de marque.
DECOR = ("file", "svg", "logo", "logos", "emblem", "icon", "symbol", "wordmark",
         "lettermark", "full", "new", "official", "brand", "vector", "text",
         "black", "white", "color", "colour", "rgb", "cmyk", "horizontal",
         "square", "primary", "dark", "light", "transparent", "en", "fr", "de")


def _noyau(titre):
    """Reduit « File:Runway Black Logo SVG.svg » a « runway »."""
    t = titre.split(":", 1)[-1]
    t = re.sub(r"\.(svg|png|jpg)$", "", t, flags=re.I)
    mots = [m for m in re.split(r"[^A-Za-z0-9]+", t) if m]
    garde = [m for m in mots
             if m.lower() not in DECOR and not re.fullmatch(r"(19|20)\d\d", m)]
    return "".join(garde).lower()


def noter(titre, marque):
    """Le nom de la marque DOIT figurer dans le titre du fichier.

    Sans cette exigence, la recherche ramenait n'importe quoi : "xAI" recuperait
    « Grokipedia homepage.svg ». Or la charte est explicite — "ne jamais dessiner
    l'approximation d'un logo connu ; un faux logo est pire que pas de logo".
    Un mauvais logo passe inapercu a la relecture et se voit a la publication.
    """
    t = titre.lower()
    if not t.endswith(".svg"):
        return -100
    m = _plat(marque)
    noyau = _noyau(titre)
    if not m:
        return -100
    if noyau == m:
        n = 40                     # correspondance exacte : sur
    elif m in _plat(titre):
        n = 5                      # le nom apparait, mais noye : a verifier
    else:
        return -100
    if "logo" in t:
        n += 12
    for x in MALUS:
        if x in t:
            n -= 9
    for x in BONUS:
        if x in t:
            n += 4
    n -= len(titre) / 40.0        # a qualite egale, le nom le plus simple
    if "(" in t:
        n -= 2
    return n


def url_fichier(titre):
    u = "%s?action=query&format=json&titles=%s&prop=imageinfo&iiprop=url|mime|size|extmetadata" % (
        API, urllib.parse.quote(titre))
    d = json.loads(_get(u))
    for p in d.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {}) or {}
        return dict(url=ii.get("url"), mime=ii.get("mime"), octets=ii.get("size"),
                    page=ii.get("descriptionurl"),
                    licence=(em.get("LicenseShortName", {}) or {}).get("value"),
                    auteur=re.sub("<[^>]+>", "", (em.get("Artist", {}) or {}).get("value", ""))[:80])
    return None


def slug(nom):
    s = nom.lower().replace("'", "").replace("&", "and").replace("+", "plus")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "marque"


def recuperer(marque, secteur, prefixe="logo"):
    try:
        titres = chercher(marque)
    except Exception as e:
        return None, "recherche : %s" % str(e)[:50]
    if not titres:
        return None, "aucun resultat"
    classe = sorted(((noter(t, marque), t) for t in titres), reverse=True)
    if classe[0][0] < 0:
        return None, "aucun SVG exploitable"
    note, titre = classe[0]
    sur = note >= 40
    info = url_fichier(titre)
    if not info or not info.get("url"):
        return None, "url introuvable"
    # Une correspondance approximative ne rentre PAS dans la bibliotheque :
    # « Chroma » ramenait « ChromaDex » (complements alimentaires), « Tally »
    # ramenait « Tally Hall » (un groupe). Un faux logo est pire que pas de logo.
    d = os.path.join(OUT, secteur) if sur else os.path.join(OUT, "_a-verifier")
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, "%s_%s_officiel.svg" % (prefixe, slug(marque)))
    try:
        data = _get(info["url"], bin=True)
    except Exception as e:
        return None, "telechargement : %s" % str(e)[:50]
    if len(data) < 300:
        return None, "fichier vide"
    with open(dest, "wb") as fh:
        fh.write(data)
    return dict(marque=marque, secteur=secteur, fichier=os.path.basename(dest),
                source_commons=titre, page=info.get("page"), licence=info.get("licence"),
                auteur=info.get("auteur"), octets=len(data), note=round(note, 1),
                confiance="sure" if sur else "a-verifier"), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manquants", action="store_true")
    ap.add_argument("--multicolores", action="store_true")
    ap.add_argument("--limite", type=int, default=0)
    a = ap.parse_args()

    man = os.path.join(OUT, "_manifeste.json")
    d = json.load(open(man, encoding="utf-8")) if os.path.exists(man) else {}

    cibles = []
    if a.manquants:
        for i in d.get("introuvables", []):
            cibles.append((i["nom"], i["secteur"], "logo"))
    if a.multicolores:
        for l in d.get("logos", []):
            if l.get("multicolore"):
                cibles.append((l["nom"], l["secteur"], "logo"))
    if not cibles:
        print("rien a faire — preciser --manquants et/ou --multicolores")
        return 1
    if a.limite:
        cibles = cibles[:a.limite]

    print("%d marques a chercher sur Commons\n" % len(cibles))
    faits, echecs = [], []
    for i, (nom, secteur, pref) in enumerate(cibles, 1):
        r, err = recuperer(nom, secteur, pref)
        if r:
            faits.append(r)
            print("  %s %-28s %-24s %s" % ("  " if r["confiance"] == "sure" else "?~",
                                              nom[:27], secteur[:23], r["source_commons"][:40]))
        else:
            echecs.append(dict(nom=nom, secteur=secteur, motif=err))
            print("  ! %-28s %s" % (nom[:27], err))
        if i % 25 == 0:
            print("     ... %d/%d" % (i, len(cibles)))
        time.sleep(0.12)

    mc = os.path.join(OUT, "_manifeste-commons.json")
    ancien = json.load(open(mc, encoding="utf-8")).get("logos", []) if os.path.exists(mc) else []
    connus = {f["fichier"] for f in faits}
    with open(mc, "w", encoding="utf-8") as fh:
        json.dump({"source": "Wikimedia Commons — logos officiels, souvent en couleurs reelles",
                   "note": "la page de description porte auteur et licence ; usage nominatif "
                           "(on montre la marque dont on parle)",
                   "logos": faits + [x for x in ancien if x["fichier"] not in connus],
                   "echecs": echecs}, fh, ensure_ascii=False, indent=2)

    print("\n%d recuperes · %d echecs -> %s" % (len(faits), len(echecs), os.path.basename(mc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

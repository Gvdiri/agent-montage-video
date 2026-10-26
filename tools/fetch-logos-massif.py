#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Banque de logos massive - Hyperframes.

Objectif fixe par le createur : au moins 600 logos, tous secteurs, "tout ce qui
pourrait etre amene a etre mentionne dans nos videos". Regle permanente du projet :
tout nom de marque prononce porte son logo a l'ecran.

Methode : on ne devine pas les identifiants. On telecharge la liste REELLE des
icones disponibles (3 459 au 2026-09-10), et on croise avec une liste curatee par
secteur, en normalisant les noms pour rattraper les variantes d'ecriture
("Node.js" -> "nodedotjs", "X (Twitter)" -> "x"). Ce qui ne matche pas est
signale, jamais remplace en silence.

⚠️ LIMITE, VALABLE POUR TOUS LES FICHIERS ICI :
Simple Icons ne fournit que des traces MONOCHROMES. Chaque logo sort donc en une
seule couleur — celle de la marque quand la source la porte.
- Pour une marque nativement monochrome (Anthropic, OpenAI, GitHub, Notion...),
  c'est le logo exact.
- Pour une marque multicolore ou en degrade, c'est une SIMPLIFICATION : la forme
  est officielle, la colorimetrie ne l'est pas. Le champ `multicolore` marque
  celles que je sais etre dans ce cas. **Son absence ne vaut pas verification.**

Marques absentes de Simple Icons pour raisons de marque deposee (LinkedIn, Amazon,
Adobe, Canva...) : on ne contourne pas, elles sont listees comme "a sourcer a la
main sur la page presse".

Usage :
    python tools/fetch-logos-massif.py [--verifier] [--secteurs ia,dev]
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
CACHE = os.path.join(ROOT, "temp", "_slugs-simple-icons.txt")
IVOIRE = "F3F1EA"
UA = "hyperframes-asset-library/1.0"
VERSION = "16.30.0"
# Beaucoup de marques ont ete RETIREES de Simple Icons pour raisons de marque deposee
# (OpenAI, LinkedIn, Amazon, Xbox, Nintendo, Disney, la plupart des medias et des
# marques grand public). On va donc les chercher dans une version archivee.
#
# Pourquoi c'est legitime ici : afficher le logo d'une societe pendant qu'on PARLE
# d'elle est un usage nominatif, editorial — c'est exactement ce que fait la
# reference du monteur. Le retrait du catalogue concerne la redistribution dans un
# paquet d'icones, pas le fait de montrer une marque dont on parle.
# Ces logos sont marques `source_archive: true` dans le manifeste.
ARCHIVE = "11.14.0"
CACHE_HEX = os.path.join(ROOT, "temp", "_hex-simple-icons-archive.json")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break

# Marques dont le vrai logo est multicolore ou en degrade.
MULTICOLORE = {
    "figma", "slack", "google", "googledrive", "gmail", "googlemaps", "googleplay",
    "googlecloud", "googlechrome", "googlecolab", "googlegemini", "googlephotos",
    "googlemeet", "googlekeep", "googleclassroom", "googleads", "googleanalytics",
    "googlebigquery", "googlecalendar", "googledocs", "googleforms", "googlelens",
    "instagram", "canva", "microsoft", "microsoftoffice", "microsoftazure",
    "microsoftexcel", "microsoftword", "microsoftpowerpoint", "microsoftoutlook",
    "microsoftteams", "microsoftonedrive", "microsoftsharepoint", "meta", "windows",
    "firefox", "mozillafirefox", "opera", "brave", "safari", "airtable", "asana",
    "trello", "atlassian", "jira", "confluence", "bitbucket", "mailchimp",
    "salesforce", "hubspot", "zoho", "freshworks", "slackware", "zoom", "skype",
    "flutter", "swift", "kotlin", "python", "rust", "ruby", "php", "java",
    "android", "chromium", "cloudflare", "digitalocean", "heroku", "netlify",
    "elastic", "grafana", "kibana", "mongodb", "redis", "postgresql", "mysql",
    "tensorflow", "pytorch", "keras", "kaggle", "huggingface", "mistralai",
    "stackoverflow", "reddit", "pinterest", "snapchat", "spotify", "soundcloud",
    "twitch", "playstation", "xbox", "nintendo", "steam", "epicgames", "unity",
    "unrealengine", "blender", "autodesk", "sketch", "invision", "framer",
    "webflow", "wix", "squarespace", "wordpress", "drupal", "joomla", "magento",
    "prestashop", "woocommerce", "paypal", "visa", "mastercard", "americanexpress",
    "revolut", "n26", "wise", "klarna", "coinbase", "binance", "kraken",
    "ethereum", "bitcoin", "solana", "cardano", "polygon", "chainlink",
    "airbnb", "uber", "ubereats", "deliveroo", "doordash", "booking",
    "tripadvisor", "expedia", "ryanair", "airfrance", "lufthansa", "sncf",
    "fedex", "dhl", "ups", "laposte", "ikea", "carrefour", "leclerc",
    "netflix", "disney", "primevideo", "hulu", "youtube", "tiktok", "vimeo",
    "duolingo", "coursera", "udemy", "khanacademy", "notion", "evernote",
    "dropbox", "box", "icloud", "protonmail", "signal", "telegram", "whatsapp",
    "discord", "twitter", "facebook", "messenger", "wechat", "line",
}


def _get(url, bin=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = r.read()
        return d if bin else d.decode("utf-8")


def slugs_archive():
    """Slugs presents dans la version archivee mais retires depuis."""
    return set(hex_archive().keys())


def slugs_disponibles():
    if os.path.exists(CACHE) and os.path.getsize(CACHE) > 4000:
        return set(open(CACHE, encoding="utf-8").read().split())
    d = json.loads(_get("https://data.jsdelivr.com/v1/packages/npm/simple-icons@%s?structure=flat" % VERSION))
    ic = sorted(f["name"].split("/")[-1][:-4] for f in d.get("files", [])
                if f["name"].startswith("/icons/") and f["name"].endswith(".svg"))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(ic))
    return set(ic)


def norm(n):
    """« Node.js » -> « nodedotjs », « X (Twitter) » -> « xtwitter » puis « x »."""
    n = n.lower().strip()
    n = n.replace(".", "dot").replace("+", "plus").replace("&", "and")
    return "".join(c for c in n if c.isalnum())


def resoudre(nom, dispo):
    """Tente plusieurs formes avant d'abandonner."""
    c = norm(nom)
    for essai in (c, c.replace("dot", ""), c.replace("dot", "-"),
                  nom.lower().replace(" ", ""), nom.lower().replace(" ", "-")):
        e = "".join(ch for ch in essai if ch.isalnum() or ch == "-")
        if e in dispo:
            return e
    return None


_HEX = None


def hex_archive():
    """Table titre -> couleur officielle, depuis la version archivee."""
    global _HEX
    if _HEX is not None:
        return _HEX
    if os.path.exists(CACHE_HEX):
        _HEX = json.load(open(CACHE_HEX, encoding="utf-8"))
        return _HEX
    d = json.loads(_get("https://cdn.jsdelivr.net/npm/simple-icons@%s/_data/simple-icons.json" % ARCHIVE))
    ic = d.get("icons", d) if isinstance(d, dict) else d
    _HEX = {norm(e["title"]): e["hex"] for e in ic if e.get("title") and e.get("hex")}
    os.makedirs(os.path.dirname(CACHE_HEX), exist_ok=True)
    json.dump(_HEX, open(CACHE_HEX, "w", encoding="utf-8"))
    return _HEX


def telecharger_svg(slug, couleur=None):
    """v16 en premier (rend la couleur de marque), sinon repli sur l'archive."""
    try:
        return _get("https://cdn.simpleicons.org/%s%s" % (slug, "/%s" % couleur if couleur else "")), False
    except Exception:
        svg = _get("https://cdn.jsdelivr.net/npm/simple-icons@%s/icons/%s.svg" % (ARCHIVE, slug))
        h = ("#" + couleur) if couleur else ("#" + hex_archive().get(slug, ""))
        if len(h) != 7:
            raise RuntimeError("couleur officielle inconnue pour %s" % slug)
        return svg.replace("<svg ", '<svg fill="%s" ' % h, 1), True


def hex_de(svg):
    if 'fill="#' in svg:
        i = svg.index('fill="#')
        return svg[i + 6:i + 13]
    return None


def png_depuis_svg(svg, dest, cote=512):
    if CHROME is None:
        return False
    html = os.path.splitext(dest)[0] + ".__t.html"
    s = svg.replace("<svg ", "<svg width='%d' height='%d' " % (cote, cote), 1)
    with open(html, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><meta charset='utf-8'><style>*{margin:0;padding:0}"
                 "html,body{width:%dpx;height:%dpx;background:transparent}</style>%s"
                 % (cote, cote, s))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--force-device-scale-factor=1",
                    "--screenshot=%s" % dest, "--window-size=%d,%d" % (cote, cote),
                    "--virtual-time-budget=700", "file:///%s" % html.replace("\\", "/")],
                   capture_output=True, text=True, timeout=60)
    if os.path.isfile(html):
        os.remove(html)
    return os.path.isfile(dest)


def charger_secteurs():
    from logos_secteurs import SECTEURS
    return SECTEURS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secteurs", default=None)
    ap.add_argument("--verifier", action="store_true", help="ne rien telecharger, juste croiser")
    ap.add_argument("--sans-png", action="store_true")
    a = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    SECTEURS = charger_secteurs()
    courant = slugs_disponibles()
    archive = slugs_archive()
    dispo = courant | archive
    print("%d icones au catalogue courant · %d de plus dans l'archive · %d au total\n"
          % (len(courant), len(archive - courant), len(dispo)))

    cibles = SECTEURS
    if a.secteurs:
        g = {x.strip() for x in a.secteurs.split(",")}
        cibles = {k: v for k, v in SECTEURS.items() if k.split("-", 1)[-1] in g or k in g}

    resolus, absents, doublons = [], [], set()
    for secteur, noms in cibles.items():
        for nom in noms:
            s = resoudre(nom, dispo)
            if s is None:
                absents.append((secteur, nom))
            elif s in doublons:
                continue
            else:
                doublons.add(s)
                resolus.append((secteur, nom, s))

    print("%d marques resolues · %d introuvables" % (len(resolus), len(absents)))
    if a.verifier:
        print("\nIntrouvables :")
        for sec, nom in absents:
            print("  %-26s %s" % (sec, nom))
        return 0

    faits, echecs = [], []
    for i, (secteur, nom, slug) in enumerate(resolus, 1):
        d = os.path.join(OUT, secteur)
        os.makedirs(d, exist_ok=True)
        p_c = os.path.join(d, "logo_%s_couleur.svg" % slug)
        if os.path.exists(p_c):
            continue
        try:
            svg_c, arch = telecharger_svg(slug)
            svg_i, _ = telecharger_svg(slug, IVOIRE)
        except Exception as e:
            echecs.append((nom, slug, str(e)[:60]))
            continue
        with open(p_c, "w", encoding="utf-8") as fh:
            fh.write(svg_c)
        with open(os.path.join(d, "logo_%s_ivoire.svg" % slug), "w", encoding="utf-8") as fh:
            fh.write(svg_i)
        png = None
        if not a.sans_png:
            pp = os.path.join(d, "logo_%s_couleur.png" % slug)
            if png_depuis_svg(svg_c, pp):
                png = os.path.basename(pp)
        faits.append(dict(slug=slug, nom=nom, secteur=secteur, couleur=hex_de(svg_c),
                          multicolore=slug in MULTICOLORE, source_archive=arch,
                          svg_couleur=os.path.basename(p_c),
                          svg_ivoire="logo_%s_ivoire.svg" % slug, png=png))
        if i % 40 == 0:
            print("  ... %d/%d" % (i, len(resolus)))
        time.sleep(0.05)

    os.makedirs(OUT, exist_ok=True)
    man = os.path.join(OUT, "_manifeste.json")
    ancien = []
    if os.path.exists(man):
        try:
            ancien = json.load(open(man, encoding="utf-8")).get("logos", [])
        except Exception:
            ancien = []
    connus = {f["slug"] for f in faits}
    tous = faits + [x for x in ancien if x.get("slug") not in connus]

    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"source": "cdn.simpleicons.org — trace officiel, couleur de marque",
                   "limite": "traces MONOCHROMES uniquement ; voir le champ multicolore",
                   "total": len(tous),
                   "introuvables": [{"secteur": s, "nom": n} for s, n in absents],
                   "echecs": [{"nom": n, "slug": s, "erreur": e} for n, s, e in echecs],
                   "logos": tous}, fh, ensure_ascii=False, indent=2)

    print("\n%d nouveaux · %d au total · %d echecs · %d introuvables"
          % (len(faits), len(tous), len(echecs), len(absents)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B-roll photo-realiste depuis Openverse (CC0) - Hyperframes.

Remplit les quatre categories que ni le generateur procedural (fonds) ni le rendu
HTML (interfaces) ne savent produire : mains, lieux, humain au travail, objets.

Source : api.openverse.org, sans cle. **Filtre `license=cc0` uniquement.**
CC0 = renonciation au droit d'auteur : usage commercial libre, aucune attribution
exigee. On enregistre quand meme la source et l'auteur dans le manifeste — ca ne
coute rien et ca permet de retrouver ou verifier une image plus tard.

⚠️ Ce sont des photos de banque brutes. Elles n'ont pas la charte :
- les etalonner avant usage (graphite/ivoire dominants, peau chaude preservee) ;
- la charte interdit "l'esthetique IA generique" — une photo de banque trop typee
  "business souriant" est a ecarter, pas a etalonner.
Une passe humaine de tri reste necessaire : le script ramene de la matiere, il ne
juge pas le gout.

Usage :
    python tools/fetch-stock-broll.py [--only 03,04] [--par-requete 4]
"""
import os
import sys
import json
import time
import argparse
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")

UA = "hyperframes-asset-library/1.0"
API = "https://api.openverse.org/v1/images/"
LARGEUR_MINI = 1100

# categorie -> sous-categorie -> requetes de recherche
PLAN = {
    "03-mains-et-appareils": {
        "scroll-telephone": ["smartphone hand", "phone screen finger", "mobile phone hand"],
        "frappe-clavier": ["hands typing keyboard laptop", "typing mechanical keyboard closeup"],
        "souris-et-clic": ["computer mouse", "trackpad", "mouse hand desk"],
        "tablette-stylet": ["tablet stylus", "drawing tablet", "ipad pencil"],
        "telephone-en-main": ["holding phone", "smartphone screen"],
    },
    "04-lieux-et-bureaux": {
        "bureau-nuit": ["desk at night lamp laptop", "dark home office night"],
        "bureau-jour": ["home office desk daylight window", "minimal desk workspace"],
        "cafe-exterieur": ["laptop coffee shop table", "working cafe laptop"],
        "open-space": ["open space office desks", "coworking space interior"],
        "interieur-chaleureux": ["warm living room interior", "cozy home interior daylight"],
    },
    "05-humain-au-travail": {
        "face-ecran": ["person working laptop screen", "man working computer desk"],
        "reflexion-pause": ["coffee laptop", "thinking person window", "cup desk laptop"],
        "reunion-echange": ["colleagues laptop", "people working together", "team laptop"],
        "satisfaction-resultat": ["working laptop", "student laptop", "freelancer laptop"],
        "surcharge-frustration": ["paperwork desk", "stack of documents", "messy desk papers"],
    },
    "07-objets-et-details": {
        "clavier-macro": ["keyboard keys macro closeup", "mechanical keyboard detail"],
        "ecran-reflet": ["code screen", "programming monitor", "computer screen code"],
        "bureau-objets": ["desk flat lay", "workspace top view", "office supplies desk"],
        "papier-carnet": ["notebook pen handwriting", "open notebook desk paper"],
    },
}

_faits = []
_vus = set()


def chercher(q, nb, essais=3):
    """Openverse limite le debit : on reessaie au lieu d'abandonner la requete."""
    for k in range(essais):
        try:
            return _chercher(q, nb)
        except Exception:
            if k == essais - 1:
                raise
            time.sleep(3 * (k + 1))
    return []


def _chercher(q, nb):
    url = API + "?" + urllib.parse.urlencode({
        "q": q, "license": "cc0", "page_size": nb * 3,
        "mature": "false", "extension": "jpg",
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read().decode("utf-8")).get("results", [])


def slugifier(t):
    t = "".join(c.lower() if c.isalnum() else "-" for c in (t or "image"))
    while "--" in t:
        t = t.replace("--", "-")
    return t.strip("-")[:44] or "image"


def telecharger(u, dest):
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    if len(data) < 12000:
        raise RuntimeError("fichier trop petit (%d o)" % len(data))
    with open(dest, "wb") as fh:
        fh.write(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="prefixes de categorie, ex : 03,05")
    ap.add_argument("--par-requete", type=int, default=4)
    a = ap.parse_args()

    cats = PLAN
    if a.only:
        g = tuple(x.strip() for x in a.only.split(","))
        cats = {k: v for k, v in PLAN.items() if k.startswith(g)}

    for cat, sous in cats.items():
        print("\n[%s]" % cat)
        for sc, requetes in sous.items():
            d = os.path.join(BROLL, cat, sc)
            os.makedirs(d, exist_ok=True)
            garde = 0
            for q in requetes:
                if garde >= a.par_requete * len(requetes):
                    break
                try:
                    res = chercher(q, a.par_requete)
                except Exception as e:
                    print("  ! recherche '%s' : %s" % (q, str(e)[:70]))
                    continue
                for it in res:
                    if garde >= a.par_requete * len(requetes):
                        break
                    if it.get("license") != "cc0":
                        continue                      # ceinture et bretelles
                    if it.get("id") in _vus:
                        continue
                    w = it.get("width") or 0
                    if w and w < LARGEUR_MINI:
                        continue
                    u = it.get("url")
                    if not u:
                        continue
                    nom = "broll_%s_%s.jpg" % (sc, slugifier(it.get("title"))[:34])
                    dest = os.path.join(d, nom)
                    # Ne jamais reimporter une image deja ECARTEE : les rejets sont
                    # deplaces dans `_ecartes/`, pas supprimes, donc un simple test
                    # d'existence sur la destination ne les voit pas. Sans ce garde-fou
                    # la calligraphie anglaise ecartee comme hors sujet revenait au
                    # passage suivant.
                    if os.path.exists(dest) or os.path.exists(os.path.join(d, "_ecartes", nom)):
                        continue
                    try:
                        n = telecharger(u, dest)
                    except Exception as e:
                        print("  ! %-42s %s" % (nom[:41], str(e)[:50]))
                        continue
                    _vus.add(it.get("id"))
                    garde += 1
                    _faits.append(dict(
                        categorie=cat, sous_categorie=sc, fichier=nom,
                        titre=it.get("title"), auteur=it.get("creator"),
                        licence=it.get("license"), source=it.get("foreign_landing_url"),
                        largeur=it.get("width"), hauteur=it.get("height"),
                        requete=q, octets=n))
                    print("  %-46s %4d ko  %sx%s" % (
                        nom[:45], n // 1024, it.get("width"), it.get("height")))
                    time.sleep(0.1)
            print("  -> %-26s %d images" % (sc, garde))

    man = os.path.join(BROLL, "_manifeste-stock.json")
    ancien = []
    if os.path.exists(man):
        try:
            ancien = json.load(open(man, encoding="utf-8")).get("images", [])
        except Exception:
            ancien = []
    connus = {f["fichier"] for f in _faits}
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"source": "api.openverse.org", "licence": "CC0 uniquement (domaine public)",
                   "note": "photos de banque brutes : etalonner avant usage, et trier a l'oeil",
                   "images": _faits + [x for x in ancien if x["fichier"] not in connus]},
                  fh, ensure_ascii=False, indent=2)
    print("\n%d images CC0 recuperees" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())

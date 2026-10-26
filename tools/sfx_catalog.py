#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Catalogue de la bibliotheque SFX - Hyperframes.

Scanne ce qui existe REELLEMENT sur le disque (asset-library/sfx/<role>/*.wav),
mesure chaque son, et reecrit catalogue.json + LISEZ-MOI.md.

La source de verite, c'est le disque - pas une vague de generation. Un catalogue
construit depuis la vague oublie tout ce qui a ete synthetise ou ajoute a la main.

Usage :
    python tools/sfx_catalog.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_bench import measure, judge  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SFX = os.path.join(ROOT, "asset-library", "sfx")

ROLES = ["impact", "transition", "reveal", "riser", "confirmation", "ui", "texture"]

USAGE = {
    "impact": "**Le coup.** Hook a 0,00 s, chiffre qui claque, revelation seche, negatif rouge. "
              "Attaque quasi nulle : il doit tomber pile sur la frame.",
    "transition": "**Le liant entre deux plans.** A 1,5 s de cadence c'est le role le plus consomme "
                  "de la bibliotheque — d'ou le nombre de variantes, pour ne jamais repeter le meme.",
    "reveal": "**La carte de preuve qui apparait**, le logo qui entre, le panneau qui se remplit. "
              "Montee douce sous l'image, pas de transitoire.",
    "riser": "**La tension qui monte** vers la revelation ou vers le CTA. Se pose 1 a 3 s avant le point d'arrivee.",
    "confirmation": "**Ca a marche.** Le positif, la resolution, la coche. A reserver au moment ou "
                    "la promesse est tenue a l'ecran.",
    "ui": "**Sons d'interface** : clic, frappe, envoi, notification, molette. "
          "⚠️ Seul role dont le spec n'est pas mesure sur une reference (voir sfx_bench.py).",
    "texture": "**Le lit sous un panneau de preuve**, la tension continue, l'ambiance. "
               "Normalises en loudness, pas en pic : un drone au meme pic qu'un impact paraitrait deux fois plus fort.",
}

ORIGINE = {
    "synth_": "synthetise (`tools/synth_sfx.py`)",
    "impact_spiderverse": "extrait du Reel IG DejO7XWuxrK a 1:47.9 (pas l'original) — voulu par le createur, hors registre sub-grave",
    "impact_signature-test": "synthetise (`tools/signature_sonore.py`) — son d'ouverture EN TEST (17/10), a poser au cas par cas, jamais d'office",
}


def origine(nom):
    for p, lib in ORIGINE.items():
        if nom.startswith(p):
            return lib
    return "ElevenLabs (`tools/generate-sfx-library.mjs`)"


def main():
    sons = []
    for role in ROLES:
        d = os.path.join(SFX, role)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".wav"):
                continue
            m = measure(os.path.join(d, f))
            if m is None:
                continue
            v, motifs = judge(m, role)
            sons.append(dict(
                fichier=f, role=role, origine=origine(f),
                duree_s=m["duree_utile"], centroide_hz=m["centroide_hz"],
                dominante_hz=m["dominante_hz"],
                energie_aigus_pct=round(m["hf_ratio"] * 100, 1),
                energie_grave_pct=round(m["sub_ratio"] * 100, 1),
                attaque_ms=round(m["attaque_s"] * 1000),
                pic_db=m["peak_db"], verdict=v, motifs=motifs,
            ))

    with open(os.path.join(SFX, "catalogue.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "spec_de_reference": "reference-analysis/nate-herk-DbLuwUVlE9Z — design sonore mesure "
                                 "a 84-225 Hz de centroide, 0-0,3 % d'energie au-dessus de 3 kHz",
            "normalisation": "court = pic -1 dBFS · texture = -23 dB RMS · WAV 44,1 kHz 16 bits mono",
            "total": len(sons),
            "sons": sons,
        }, fh, ensure_ascii=False, indent=2)

    L = ["# Bibliotheque SFX — index",
         "",
         "> Genere par `tools/sfx_catalog.py` en scannant le disque. **Ne pas editer a la main.**",
         "",
         "## Le principe",
         "",
         "Chaque son ici a ete **mesure** avant d'entrer. Le registre de la marque en audio est",
         "le **sub-grave**, pas le metal : mesure sur la reference qui performe (13,5k likes),",
         "son design sonore est a **84-225 Hz de centroide, 0 a 0,3 % d'energie au-dessus de 3 kHz**.",
         "",
         "⚠️ **L'identite visuelle est metal (chrome, acier, verre). L'identite sonore ne l'est pas.**",
         "Transposer le vocabulaire visuel dans un prompt audio produit litteralement du chrome :",
         "l'ancienne bibliotheque, generee sur des prompts \"liquid-chrome shimmer\", mesurait",
         "8 000 a 10 700 Hz avec 91 a 98 % d'energie dans les aigus. Registre inverse.",
         "",
         "Tous les fichiers sont en **WAV** : le MP3 ajoute un padding d'encodeur qui decale le",
         "transitoire, ce qui interdit de caler un impact au frame pres a 60 fps.",
         "",
         "## Comment on s'en sert",
         "",
         "- `catalogue.json` porte les mesures de chaque son — c'est ce qu'on lit pour choisir.",
         "- Pour un nouveau son : generer (`generate-sfx-library.mjs`) ou synthetiser (`synth_sfx.py`),",
         "  puis `sfx_finalize.py` (mesure + reaffectation + normalisation), puis ce script.",
         "- Un son qui ne passe aucun role part dans `_rebut/` et n'est jamais propose au montage.",
         ""]

    for role in ROLES:
        rs = [s for s in sons if s["role"] == role]
        if not rs:
            continue
        L += ["## %s — %d sons" % (role, len(rs)), "", USAGE.get(role, ""), "",
              "| fichier | duree | centroide | grave | attaque | origine |",
              "|---|---:|---:|---:|---:|---|"]
        for s in rs:
            L.append("| `%s` | %.2f s | %.0f Hz | %.0f %% | %d ms | %s |" % (
                s["fichier"], s["duree_s"], s["centroide_hz"],
                s["energie_grave_pct"], s["attaque_ms"], s["origine"]))
        L.append("")

    L += ["---", "", "**Total : %d sons.**" % len(sons), ""]
    with open(os.path.join(SFX, "LISEZ-MOI.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print("%d sons catalogues" % len(sons))
    for role in ROLES:
        n = len([s for s in sons if s["role"] == role])
        if n:
            print("  %-13s %d" % (role, n))
    hs = [s for s in sons if s["verdict"] == "FAIL"]
    if hs:
        print("\n%d hors spec (a revoir) :" % len(hs))
        for s in hs:
            print("  %-40s %s" % (s["fichier"], "; ".join(s["motifs"][:1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

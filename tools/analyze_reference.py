#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Banc d'analyse d'une video de reference - Hyperframes.

Mesure ce qu'on ne peut pas juger a l'oeil ni a l'oreille :

1. CADENCE DE COUPE - detection de changements de plan (difference d'image).
   La doctrine vise ~1,5 s de moyenne, plafond 2,3 s.

2. DESIGN SONORE ISOLE - on calcule le canal lateral L-R. La voix d'un montage
   est mixee au centre, donc L-R l'annule et laisse la musique et les SFX seuls.
   C'est comme ca qu'on a mesure la premiere reference : 315 Hz sur le hook,
   0 % d'energie au-dessus de 3 kHz.

3. EVENEMENTS SONORES - reperage des pics dans le canal lateral, extraction de
   chacun en WAV, et mesure de son spectre. Ce sont les SFX de la reference,
   utilisables comme cible de replication.

4. LUMINANCE - luminance moyenne du tiers haut vs du tiers bas. La reference qui
   performe est a 223/255 en haut (panneau de preuve clair) contre 94/255 en bas
   (visage). Nos cartes graphite sur graphite ecrasaient ce contraste.

Usage :
    python tools/analyze_reference.py <video.mp4> [...] [--out DOSSIER]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
import librosa
import soundfile as sf

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
SR = 44100


def duree(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def coupes(path, seuil=0.30):
    """Changements de plan. On passe par select+showinfo : le parsing de scdet
    ne renvoyait rien (metadata non imprimee sans filtre metadata=print)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", path,
                        "-vf", "select='gt(scene,%.2f)',showinfo" % seuil,
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    ts = []
    for ligne in (r.stderr or "").splitlines():
        if "pts_time:" in ligne and "Parsed_showinfo" in ligne:
            for tok in ligne.split():
                if tok.startswith("pts_time:"):
                    try:
                        ts.append(float(tok.split(":", 1)[1]))
                    except Exception:
                        pass
    return sorted(set(ts))


def audio_st(path):
    """Charge l'audio en stereo (2, n)."""
    wav = path + ".__tmp.wav"
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", path,
                    "-ac", "2", "-ar", str(SR), wav], capture_output=True, text=True)
    if not os.path.isfile(wav):
        return None
    y, _ = librosa.load(wav, sr=SR, mono=False)
    os.remove(wav)
    if y.ndim == 1:
        y = np.vstack([y, y])
    return y


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def spectre(y):
    if y.size < 2048:
        return None
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512)) ** 2
    f = librosa.fft_frequencies(sr=SR, n_fft=2048)
    sp = S.sum(axis=1)
    tot = float(sp.sum()) or 1e-12
    return dict(centroide_hz=round(float((f * sp).sum() / tot), 1),
                dominante_hz=round(float(f[int(np.argmax(sp))]), 1),
                aigus_3k_pct=round(float(sp[f > 3000].sum() / tot) * 100, 2),
                grave_200_pct=round(float(sp[f < 200].sum() / tot) * 100, 2))


def evenements(side, sep_min=0.35, force_min=2.2):
    """Vrais transitoires du canal lateral.

    La premiere version renvoyait des points espaces regulierement de 0,29 s :
    ce n'etait pas de la detection, c'etait le pas minimal qui echantillonnait
    un signal continument au-dessus du seuil. On passe donc par la nouveaute
    spectrale (onset strength) et on ne garde que les pics nettement au-dessus
    de la mediane - un lit musical continu ne produit alors aucun evenement,
    ce qui est le resultat correct.
    """
    if side.size < SR // 2:
        return []
    env = librosa.onset.onset_strength(y=side, sr=SR, hop_length=256)
    if env.size < 8:
        return []
    med = float(np.median(env))
    mad = float(np.median(np.abs(env - med))) or 1e-9
    pics = librosa.util.peak_pick(env, pre_max=8, post_max=8, pre_avg=24, post_avg=24,
                                  delta=mad * force_min, wait=int(sep_min * SR / 256))
    tps = librosa.frames_to_time(pics, sr=SR, hop_length=256)
    forces = [(float(t), float((env[i] - med) / mad)) for t, i in zip(tps, pics)]
    return [(t, f) for t, f in forces if f >= force_min]


def luminance(path, dur):
    """Luminance moyenne du tiers haut et du tiers bas, sur 12 images."""
    hauts, bas = [], []
    tmp = path + ".__f.png"
    for i in range(12):
        t = dur * (i + 0.5) / 12
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", "%.2f" % t,
                        "-i", path, "-frames:v", "1", "-vf", "scale=180:-1", tmp],
                       capture_output=True, text=True)
        if not os.path.isfile(tmp):
            continue
        try:
            from PIL import Image
            a = np.asarray(Image.open(tmp).convert("L"), dtype=np.float32)
            h = a.shape[0]
            hauts.append(float(a[:h // 3].mean()))
            bas.append(float(a[2 * h // 3:].mean()))
        except Exception:
            pass
    if os.path.isfile(tmp):
        os.remove(tmp)
    return (round(float(np.mean(hauts)), 1) if hauts else None,
            round(float(np.mean(bas)), 1) if bas else None)


def analyser(path, out_dir):
    nom = os.path.splitext(os.path.basename(path))[0]
    if nom in ("source", "video", "input"):
        nom = "%s-%s" % (os.path.basename(os.path.dirname(os.path.abspath(path)))[:34], nom)
    d = os.path.join(out_dir, nom)
    os.makedirs(d, exist_ok=True)
    dur = duree(path)
    print("\n=============== %s  (%.2f s)" % (nom, dur))

    # --- cadence
    cuts = coupes(path)
    inters = [b - a for a, b in zip(cuts, cuts[1:])] if len(cuts) > 1 else []
    if cuts:
        inters = [cuts[0]] + inters
    moy = float(np.mean(inters)) if inters else 0.0
    mx = float(np.max(inters)) if inters else 0.0
    print("CADENCE  %d coupes · moyenne %.2f s · plan le plus long %.2f s · 1re coupe %.2f s"
          % (len(cuts), moy, mx, cuts[0] if cuts else -1))

    # --- audio
    st = audio_st(path)
    res_son, evs = {}, []
    if st is not None:
        mid = (st[0] + st[1]) / 2
        side = (st[0] - st[1]) / 2          # annule ce qui est centre : la voix
        p_mid, p_side = float(np.abs(mid).max()), float(np.abs(side).max())
        # part de la timeline ou la couche de design est audible
        env = np.abs(librosa.util.frame(side, frame_length=2048, hop_length=512)).max(axis=0)
        seuil = (p_side or 1e-12) * (10 ** (-34 / 20.0))
        couv = float((env > seuil).mean()) * 100
        sp = spectre(side)
        res_son = dict(pic_voix_db=round(db(p_mid), 1), pic_design_db=round(db(p_side), 1),
                       couverture_design_pct=round(couv, 1), spectre_design=sp)
        print("SON      design a %.1f dB sous la voix · present sur %.0f %% de la timeline"
              % (db(p_mid) - db(p_side), couv))
        if sp:
            print("         centroide %.0f Hz · dominante %.0f Hz · aigus>3k %.2f %% · grave<200 %.1f %%"
                  % (sp["centroide_hz"], sp["dominante_hz"], sp["aigus_3k_pct"], sp["grave_200_pct"]))

        # --- evenements sonores extraits
        ev_t = evenements(side)
        sfx_dir = os.path.join(d, "sfx-isoles")
        os.makedirs(sfx_dir, exist_ok=True)
        for i, (t0, force) in enumerate(ev_t[:14], 1):
            a = int(max(t0 - 0.06, 0) * SR)
            b = min(a + int(1.9 * SR), side.size)
            seg = side[a:b]
            if seg.size < 2048:
                continue
            pk = float(np.abs(seg).max()) or 1e-12
            seg = seg / pk * 0.891
            f = os.path.join(sfx_dir, "ev-%02d_%06.2fs.wav" % (i, t0))
            sf.write(f, (seg * 32767).astype(np.int16), SR, subtype="PCM_16")
            s2 = spectre(seg)
            evs.append(dict(index=i, t=round(t0, 2), force=round(force, 1),
                            fichier=os.path.basename(f), spectre=s2))
        if not ev_t:
            print("SFX      aucun transitoire net : la couche sonore est un lit continu, pas des impacts ponctuels")
        if evs:
            print("SFX      %d transitoires detectes -> %s" % (len(evs), os.path.relpath(sfx_dir)))
            for e in evs[:8]:
                s2 = e["spectre"] or {}
                print("         %5.2f s  force x%-4.1f centroide %6.0f Hz · aigus>3k %5.2f %% · grave<200 %5.1f %%"
                      % (e["t"], e["force"], s2.get("centroide_hz", 0),
                         s2.get("aigus_3k_pct", 0), s2.get("grave_200_pct", 0)))

    lum_h, lum_b = luminance(path, dur)
    print("IMAGE    luminance tiers haut %s/255 · tiers bas %s/255" % (lum_h, lum_b))

    rapport = dict(fichier=os.path.basename(path), duree_s=round(dur, 2),
                   coupes=dict(nombre=len(cuts), moyenne_s=round(moy, 2),
                               plus_long_s=round(mx, 2),
                               premiere_s=round(cuts[0], 2) if cuts else None,
                               horodatages=[round(c, 2) for c in cuts]),
                   son=res_son, evenements_sonores=evs,
                   luminance=dict(tiers_haut=lum_h, tiers_bas=lum_b))
    with open(os.path.join(d, "mesures.json"), "w", encoding="utf-8") as fh:
        json.dump(rapport, fh, ensure_ascii=False, indent=2)
    return rapport


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.dirname(os.path.abspath(a.videos[0]))
    tout = [analyser(v, out) for v in a.videos]
    with open(os.path.join(out, "_synthese.json"), "w", encoding="utf-8") as fh:
        json.dump(tout, fh, ensure_ascii=False, indent=2)
    print("\n-> %s" % os.path.join(out, "_synthese.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Remixe le SON d'un montage sans refaire le rendu de l'image.

Pourquoi (2026-10-01) : chaque essai de niveau de musique coutait un rendu de 6 a 8 min.
Le son d'un rendu HyperFrames est la somme des pistes avec leur data-volume (verifie par
regression le 30/09 : rapport voix/lit = 1,21-1,25 pour 1,25 attendu). On le reconstruit
donc ici — voix + lit x 0,80 x gain + chaque SFX (fichier, debut, duree, volume, depuis
build-data.json) — puis la meme passe de loudness que finish.py (-14,3 LUFS, limiteur
-1,5 dB), et on le pose sur l'image d'une video deja rendue (copie du flux video).

  python tools/remix-audio.py <atelier> <video_source.mp4> <sortie.mp4> [--lit-db +2.5]
"""
import argparse, io, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("atelier")
ap.add_argument("video")
ap.add_argument("sortie")
ap.add_argument("--lit-db", type=float, default=0.0, help="gain applique au lit (dB)")
ap.add_argument("--cible", type=float, default=-14.3)
a = ap.parse_args()

pub = os.path.join(a.atelier, "public")
D = json.load(io.open(os.path.join(a.atelier, "build-data.json"), encoding="utf-8"))
dur = D["dur"]
lit = 0.80 * 10 ** (a.lit_db / 20.0)

ins = ["-i", os.path.join(pub, "voice.wav"), "-i", os.path.join(pub, "music-bed.mp3")]
fil = ["[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[v]",
       "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=%.5f[m]" % lit]
lab = ["[v]", "[m]"]
for k, (f, t, d, g) in enumerate(D["sfx"]):
    ins += ["-i", os.path.join(pub, "assets", "sfx", f)]
    ms = int(round(t * 1000))
    fil.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:%.4f,volume=%.4f,"
               "adelay=%d|%d[s%d]" % (k + 2, d, g, ms, ms, k))
    lab.append("[s%d]" % k)
fil.append("%samix=inputs=%d:normalize=0:dropout_transition=0,atrim=0:%.4f[mix]"
           % ("".join(lab), len(lab), dur))
tmp = a.sortie + ".mix.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins +
               ["-filter_complex", ";".join(fil), "-map", "[mix]", "-c:a", "pcm_f32le", tmp],
               check=True)


def loud(p):
    e = subprocess.run(["ffmpeg", "-v", "info", "-i", p, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr[-2500:]
    return float(re.search(r"I:\s*(-?\d+\.?\d*)\s*LUFS", e).group(1))


i = loud(tmp)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", tmp, "-map", "0:v:0", "-map", "1:a:0",
                "-af", "volume=%.2fdB,alimiter=limit=-1.5dB:level=disabled" % (a.cible - i),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", a.sortie], check=True)
os.unlink(tmp)
print("%s : lit %+.1f dB · mix brut %.1f LUFS -> %.1f LUFS" % (os.path.basename(a.sortie), a.lit_db, i, loud(a.sortie)))

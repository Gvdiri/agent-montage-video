import argparse
import json
import math
import sys
from pathlib import Path

import librosa
import numpy as np


TITLES = {
    "Wp5Gl3dyKOY": "Apovabin - VOID",
    "SfAzZ6Z-fjg": "Grounded",
    "wiXPMa4gW_s": "quietshadow - FOCUS 2",
    "i_mkHfW_pZg": "dnvn - Instinct",
    "ATHhUPrt64U": "ByErik - silent nights",
    "sRXHcu668kY": "PNL - DEUX FRERES (instru)",
    "PfVdbIshnXM": "PNL - COEURS (instru)",
    "acnfqXbbOjg": "PNL - BLANKA (instru)",
    "Rw8Ey5s8qzU": "PNL - SHENMUE (instru)",
    "lCNGwOhqi-0": "PNL - URANUS (instru)",
    "WcXRpK5LVm0": "PNL - MENACE (instru)",
    "XCJiZiG3ygM": "PNL - NAHA (instru)",
}


def band_share(power, freqs, low, high):
    mask = (freqs >= low) & (freqs < high)
    return float(np.sum(power[mask]) / max(np.sum(power), 1e-12))


def regularity(onset_envelope):
    peaks = librosa.util.peak_pick(
        onset_envelope,
        pre_max=3,
        post_max=3,
        pre_avg=6,
        post_avg=6,
        delta=0.12,
        wait=3,
        sparse=True,
    )
    if len(peaks) < 4:
        return 0.0
    intervals = np.diff(peaks).astype(float)
    return float(np.clip(1.0 - np.std(intervals) / max(np.mean(intervals), 1e-6), 0, 1))


def window_features(y, sr, start, duration):
    a = int(start * sr)
    b = min(len(y), int((start + duration) * sr))
    clip = y[a:b]
    if len(clip) < sr:
        return None

    stft = np.abs(librosa.stft(clip, n_fft=2048, hop_length=512))
    power = stft**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    rms = librosa.feature.rms(S=stft)[0]
    onset = librosa.onset.onset_strength(y=clip, sr=sr, hop_length=512)
    speech_share = band_share(power, freqs, 800, 4000)
    low_share = band_share(power, freqs, 30, 250)
    high_share = band_share(power, freqs, 4000, 10000)
    crest = float(np.percentile(rms, 95) / max(np.mean(rms), 1e-9))
    pulse = regularity(onset)
    activity = float(np.mean(onset))

    return {
        "startSec": round(start, 3),
        "endSec": round(min(start + duration, len(y) / sr), 3),
        "rmsDb": round(float(librosa.amplitude_to_db([np.mean(rms)], ref=1.0)[0]), 2),
        "speechBandShare": round(speech_share, 4),
        "lowBandShare": round(low_share, 4),
        "highBandShare": round(high_share, 4),
        "pulseRegularity": round(pulse, 4),
        "onsetActivity": round(activity, 4),
        "crest": round(crest, 3),
    }


def analyze(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = len(y) / sr
    tempo_raw, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    tempo = float(np.asarray(tempo_raw).reshape(-1)[0])

    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    power = stft**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    rms = librosa.feature.rms(S=stft)[0]
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)

    window_duration = min(22.0, max(15.0, duration * 0.18))
    starts = np.arange(0, max(0.01, duration - window_duration), 2.0)
    windows = [window_features(y, sr, float(start), window_duration) for start in starts]
    windows = [w for w in windows if w]

    rms_values = np.array([w["rmsDb"] for w in windows])
    onset_values = np.array([w["onsetActivity"] for w in windows])
    rms_mid = float(np.median(rms_values)) if len(rms_values) else -24.0
    onset_mid = float(np.median(onset_values)) if len(onset_values) else 1.0

    for window in windows:
        voice_room = np.clip((0.42 - window["speechBandShare"]) / 0.28, 0, 1)
        energy_fit = math.exp(-abs(window["rmsDb"] - rms_mid) / 7.0)
        activity_fit = math.exp(-abs(window["onsetActivity"] - onset_mid) / max(onset_mid, 0.1))
        score = (
            0.42 * voice_room
            + 0.28 * window["pulseRegularity"]
            + 0.18 * activity_fit
            + 0.12 * energy_fit
        )
        window["narrationScore"] = round(float(score), 4)

    windows.sort(key=lambda item: item["narrationScore"], reverse=True)
    video_id = path.stem
    return {
        "id": video_id,
        "title": TITLES.get(video_id, video_id),
        "file": str(path),
        "durationSec": round(duration, 3),
        "tempoBpm": round(tempo, 2),
        "beatCount": int(len(beats)),
        "integratedRmsDb": round(float(librosa.amplitude_to_db([np.mean(rms)], ref=1.0)[0]), 2),
        "dynamicRangeDb": round(float(np.percentile(librosa.amplitude_to_db(rms, ref=np.max), 95) - np.percentile(librosa.amplitude_to_db(rms, ref=np.max), 10)), 2),
        "spectralCentroidHz": round(float(np.mean(centroid)), 2),
        "speechBandShare": round(band_share(power, freqs, 800, 4000), 4),
        "lowBandShare": round(band_share(power, freqs, 30, 250), 4),
        "highBandShare": round(band_share(power, freqs, 4000, 10000), 4),
        "pulseRegularity": round(regularity(onset), 4),
        "bestWindows": windows[:5],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    files = sorted(args.input_dir.glob("*.webm"))
    if not files:
        raise SystemExit("No .webm files found")

    results = []
    for path in files:
        print(f"Analyzing {path.name}", file=sys.stderr, flush=True)
        results.append(analyze(path))

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps({"tracks": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "tracks": len(results), "output": str(args.output_json)}))


if __name__ == "__main__":
    main()

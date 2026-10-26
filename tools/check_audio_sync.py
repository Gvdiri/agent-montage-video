import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.signal import correlate, correlation_lags


SAMPLE_RATE = 16000


def decode_audio(path: Path) -> np.ndarray:
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "pipe:1",
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    samples = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        raise RuntimeError(f"No audio stream decoded from {path}")
    samples /= 32768.0
    return samples


def prepare(samples: np.ndarray) -> np.ndarray:
    # Speech transients survive EQ and compression better than absolute levels.
    emphasized = np.diff(samples, prepend=samples[0])
    emphasized -= np.mean(emphasized)
    scale = np.std(emphasized)
    if scale < 1e-8:
        raise RuntimeError("Audio signal is effectively silent")
    return emphasized / scale


def measure_delay(reference: np.ndarray, candidate: np.ndarray, max_lag_ms: float) -> tuple[int, float]:
    reference = prepare(reference)
    candidate = prepare(candidate)
    values = correlate(candidate, reference, mode="full", method="fft")
    lags = correlation_lags(candidate.size, reference.size, mode="full")
    max_lag_samples = round(max_lag_ms * SAMPLE_RATE / 1000)
    allowed = np.abs(lags) <= max_lag_samples
    limited_values = values[allowed]
    limited_lags = lags[allowed]
    peak_index = int(np.argmax(limited_values))
    lag_samples = int(limited_lags[peak_index])
    confidence = float(
        limited_values[peak_index]
        / np.sqrt(np.sum(candidate * candidate) * np.sum(reference * reference))
    )
    return lag_samples, confidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure voice timing drift against the source recording."
    )
    parser.add_argument("reference", type=Path, help="Original source video or audio")
    parser.add_argument("candidate", type=Path, help="Processed audio or rendered video")
    parser.add_argument("--tolerance-ms", type=float, default=16.67)
    parser.add_argument("--max-lag-ms", type=float, default=500.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reference = decode_audio(args.reference)
    candidate = decode_audio(args.candidate)
    lag_samples, confidence = measure_delay(reference, candidate, args.max_lag_ms)
    delay_ms = lag_samples * 1000 / SAMPLE_RATE
    passed = abs(delay_ms) <= args.tolerance_ms

    result = {
        "ok": passed,
        "delayMs": round(delay_ms, 3),
        "toleranceMs": args.tolerance_ms,
        "confidence": round(confidence, 4),
        "interpretation": (
            "candidate audio is late"
            if delay_ms > 0
            else "candidate audio is early"
            if delay_ms < 0
            else "aligned"
        ),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if passed else "FAIL"
        print(
            f"{status}: delay={delay_ms:.3f} ms, "
            f"tolerance=+/-{args.tolerance_ms:.3f} ms, "
            f"confidence={confidence:.4f}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)

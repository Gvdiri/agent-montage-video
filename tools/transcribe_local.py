import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = PROJECT_ROOT / "tools" / "python-packages"
sys.path.insert(0, str(VENDOR_DIR))

from faster_whisper import WhisperModel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe media locally with word-level timestamps."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--details", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="fr")
    args = parser.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(args.input),
        language=args.language,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=True,
    )

    words = []
    segment_details = []
    full_text = []

    for segment in segments:
        text = segment.text.strip()
        if text:
            full_text.append(text)
        segment_details.append(
            {
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": text,
            }
        )
        for word in segment.words or []:
            token = word.word.strip()
            if not token:
                continue
            words.append(
                {
                    "text": token,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "probability": round(word.probability, 4),
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(words, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    details_path = args.details or args.output.with_name("transcript-details.json")
    details_path.write_text(
        json.dumps(
            {
                "engine": "faster-whisper",
                "model": args.model,
                "language": info.language,
                "language_probability": round(info.language_probability, 4),
                "duration": round(info.duration, 3),
                "text": " ".join(full_text),
                "segments": segment_details,
                "words": words,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Transcribed {len(words)} words in {info.duration:.2f}s "
        f"({info.language}, {info.language_probability:.1%})."
    )


if __name__ == "__main__":
    main()

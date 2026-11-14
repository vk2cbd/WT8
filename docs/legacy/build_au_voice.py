#!/usr/bin/env python3
"""Generate WT8 offline Australian-female announcements using Piper.

Run ONCE on the Ubuntu machine after installing piper-tts. At runtime WT8
only reads local WAV files and does not need Piper or a network connection.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "voice" / "models"
MODEL = MODEL_DIR / "en_AU-librivox-medium.onnx"
MODEL_URL = ("https://huggingface.co/DataCraftsmanAustralia/"
             "piper-en_AU-librivox-medium/resolve/main/")
# Confirmed female speaker ids in the model's published speaker map.
FEMALE_VOICES = {"Bindi": 1, "Marlo": 2, "Kirra": 3,
                 "Matilda": 7, "Tully": 8, "Willow": 9}


def download_models():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename in (MODEL.name, MODEL.name + ".json"):
        target = MODEL_DIR / filename
        if not target.is_file() or target.stat().st_size == 0:
            print("Downloading", filename, flush=True)
            temp = target.with_suffix(target.suffix + ".part")
            try:
                urllib.request.urlretrieve(MODEL_URL + filename, temp)
                temp.replace(target)
            finally:
                temp.unlink(missing_ok=True)


def generate(voice, destination):
    from wt8_voice import PHRASES
    speaker = FEMALE_VOICES[voice]
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("east", "west"):
        for key, description in PHRASES.items():
            filename = destination / (name + "_" + key.replace(" ", "_") + ".wav")
            message = f"{name.capitalize()} {description}."
            print(f"Rendering {filename.name}: {message}", flush=True)
            # Piper uses the trained Australian speaker and produces PCM WAV.
            subprocess.run(
                [sys.executable, "-m", "piper", "-m", str(MODEL),
                 "-s", str(speaker), "-f", str(filename)],
                input=message + "\n", text=True, check=True,
            )
            with __import__("wave").open(str(filename), "rb") as wav:
                if wav.getsampwidth() != 2 or wav.getnframes() == 0:
                    raise ValueError(f"Invalid output WAV: {filename}")
    print(f"Generated {2 * len(PHRASES)} announcements in {destination}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", choices=FEMALE_VOICES, default="Matilda")
    parser.add_argument("--output", type=Path, default=ROOT / "voice" / "en_AU_female")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    download_models()
    generate(args.voice, args.output)
    print("Restart WT8, uncheck Mute, and press Test Voice.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Package public source only. Never recurse into private assets or Git data."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".local", ".git", "__pycache__", ".pytest_cache", ".venv", "venv", "dist", "tests"}
EXCLUDED.add("outputs")
ALLOWED = {".py", ".md", ".json", ".svg", ".cmd", ".yml", ".yaml"}
PUBLIC_MEDIA = {"assets/nawa.gif", "assets/laugh.wav", "assets/nawa.png", "assets/card-example.png"}
PUBLIC_MEDIA.update("assets/characters/" + name + ".png" for name in (
    "01-grape", "02-cherry", "03-orange", "04-lemon", "05-kiwi", "06-tomato",
    "07-peach", "08-pineapple", "09-coconut", "10-halfmelon", "11-watermelon"))


def source_files(root=ROOT):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts):
            continue
        if relative.as_posix() in PUBLIC_MEDIA:
            yield path
            continue
        if path.name.startswith(".env") or path.suffix in {".log", ".sqlite3", ".mp4", ".wav", ".exe"}:
            continue
        if path.suffix in ALLOWED or path.name in {"LICENSE", ".gitignore", ".gitattributes"}:
            yield path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".local" / "dist" / "mcd-code-source.zip")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_files():
            archive.write(path, "mcd-code/" + path.relative_to(ROOT).as_posix())
    print(args.output)


if __name__ == "__main__":
    main()

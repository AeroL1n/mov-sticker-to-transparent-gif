#!/usr/bin/env python3
"""Build only the five canonical skill files, not the complete GitHub repository."""
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = ("SKILL.md", "CHANGELOG.md", "TESTS.md", "使用说明.md", "scripts/convert_stickers.py")
PREFIX = "mov-sticker-to-transparent-gif"


def main():
    script = (ROOT / "scripts/convert_stickers.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION = "(\d+\.\d+\.\d+)"$', script, re.MULTILINE)
    if not match:
        raise SystemExit("Cannot read script VERSION.")
    version = match.group(1)
    if f"版本：{version}" not in (ROOT / "SKILL.md").read_text(encoding="utf-8"):
        raise SystemExit("SKILL.md and script versions differ.")
    major_minor = ".".join(version.split(".")[:2])
    out = ROOT / "dist" / f"表情包转GIF_v{major_minor}.skill.zip"
    out.parent.mkdir(exist_ok=True)
    # Refuse accidental replacement of an existing distribution.
    with ZipFile(out, "x", ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / name, f"{PREFIX}/{name}")
    with ZipFile(out) as archive:
        if archive.testzip() is not None:
            raise SystemExit("ZIP CRC validation failed.")
        if set(archive.namelist()) != {f"{PREFIX}/{name}" for name in FILES}:
            raise SystemExit("Unexpected ZIP files.")
        for name in FILES:
            if archive.read(f"{PREFIX}/{name}") != (ROOT / name).read_bytes():
                raise SystemExit(f"ZIP content differs: {name}")
    print(out)
    print("SHA256:", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()

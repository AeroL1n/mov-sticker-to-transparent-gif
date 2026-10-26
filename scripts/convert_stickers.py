#!/usr/bin/env python3
"""MOV stickers: confirmed background modes, three GIF sizes, safe append, batch ZIP."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import cv2
import numpy as np
from PIL import Image

VERSION = "2.3.0"
SIZES = (120, 220, 330)


def size_folder(size):
    return f"{size}gif"


def size_directories(root, size):
    # Write only to the new folders; inspect legacy folders for name collisions.
    return tuple(root / folder for folder in
                 (size_folder(size), f"{size}x{size}", f"{size}x{size}gif"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(path):
    data = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams",
         "-show_frames", "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout)
    require(data.get("streams"), f"No video stream: {path}")
    stream = data["streams"][0]
    parts = stream.get("avg_frame_rate", "0/1").split("/")
    fps = float(parts[0]) / float(parts[1]) if float(parts[1]) else 0
    require(fps > 0, "Cannot determine frame rate; inspect timestamps manually.")
    cap = cv2.VideoCapture(str(path))
    images, shape = [], None
    try:
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            if shape is None:
                shape = rgb.shape[:2]
            require(rgb.shape[:2] == shape, "Variable frame dimensions need manual handling.")
            images.append(rgb)
    finally:
        cap.release()
    require(images, f"No decoded frames: {path}")
    declared = stream.get("nb_frames")
    if declared and str(declared).isdigit():
        require(int(declared) == len(images), "Decoded frame count differs from metadata.")
    stamps = [float(f["best_effort_timestamp_time"]) for f in data.get("frames", [])
              if "best_effort_timestamp_time" in f]
    if len(stamps) == len(images) and all(b > a for a, b in zip(stamps, stamps[1:])):
        timeline = [t - stamps[0] for t in stamps]
        step = timeline[-1] - timeline[-2] if len(timeline) > 1 else 1 / fps
        duration = stream.get("duration")
        end = float(duration) if duration not in (None, "N/A") else timeline[-1] + step
        if end <= timeline[-1]:
            end = timeline[-1] + step
        timeline.append(end)
    else:
        # Falling back is safe only for footage visually confirmed to be CFR.
        raise ValueError("Missing/non-monotonic timestamps; standardize input before conversion.")
    ticks = [int(round(t * 100)) for t in timeline]
    delays = [(b - a) * 10 for a, b in zip(ticks, ticks[1:])]
    require(all(d >= 20 for d in delays),
            "GIF delays below 20 ms: resample to a browser-safe rate first, preserving duration.")
    return images, delays, ticks


def black_mask(rgb, threshold):
    dark = (rgb.max(axis=2) <= threshold).astype(np.uint8)
    _, labels, _, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    border = np.unique(np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1])))
    return (~np.isin(labels, border[border != 0])).astype(np.uint8)


def outline(rgb, mask):
    inside = cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    outside = cv2.distanceTransform(1 - mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    visible = (mask > 0) | (outside <= 3.0)
    white = visible & ~((mask > 0) & (inside > 2.0))
    rgba = np.dstack((rgb.copy(), visible.astype(np.uint8) * 255))
    rgba[white, :3] = 255
    rgba[~visible, :3] = 0
    return rgba, white


def square(rgba, white):
    h, w = rgba.shape[:2]
    if h == w:
        return rgba, white
    side = max(h, w)
    a = np.zeros((side, side, 4), dtype=np.uint8)
    s = np.zeros((side, side), dtype=bool)
    y, x = (side - h) // 2, (side - w) // 2
    a[y:y+h, x:x+w], s[y:y+h, x:x+w] = rgba, white
    return a, s


def prepare(path, mode, threshold):
    images, all_delays, ticks = decode(path)
    h, w = images[0].shape[:2]
    total, keep, margin = len(images), len(images), 0
    frames, whites = [], []
    if mode == "black":
        masks = [black_mask(rgb, threshold) for rgb in images]
        nonempty = [i for i, m in enumerate(masks) if m.any()]
        require(nonempty, "No foreground; inspect source and threshold.")
        keep = nonempty[-1] + 1
        # One common margin for the whole animation prevents per-frame scale jitter.
        if any(m[:4].any() or m[-4:].any() or m[:, :4].any() or m[:, -4:].any()
               for m in masks[:keep]):
            margin = 4
        for rgb, mask in zip(images[:keep], masks[:keep]):
            if margin:
                rgb = np.pad(rgb, ((margin, margin), (margin, margin), (0, 0)))
                mask = np.pad(mask, ((margin, margin), (margin, margin)))
            frames.append(outline(rgb, mask))
    else:
        # Preserve means preserve: no color key, no outline, no arbitrary tail trim.
        for rgb in images:
            a = np.dstack((rgb, np.full(rgb.shape[:2], 255, dtype=np.uint8)))
            frames.append((a, np.zeros(rgb.shape[:2], dtype=bool)))
    for i, (a, s) in enumerate(frames):
        frames[i] = square(a, s)
    frames, whites = map(list, zip(*frames))
    samples = []
    per_frame = max(1, 250000 // keep)
    for a in frames:
        pixels = a[:, :, :3][a[:, :, 3] > 0]
        step = max(1, len(pixels) // per_frame)
        samples.append(pixels[::step][:per_frame])
    sample = np.concatenate(samples)
    quant = Image.fromarray(sample.reshape(1, len(sample), 3)).quantize(
        colors=254, method=Image.Quantize.MEDIANCUT, kmeans=3)
    palette = np.zeros((256, 3), dtype=np.uint8)
    entries = np.array(quant.getpalette(), dtype=np.uint8).reshape(-1, 3)
    palette[:min(254, len(entries))] = entries[:254]
    palette[254] = 255  # Dedicated, exact white.
    palette[255] = palette[0]  # Dedicated transparency; opaque duplicate is index 0.
    meta = {
        "source": path.name, "background_mode": mode,
        "background": "透明背景" if mode == "black" else "保留原装饰背景（原画面不透明）",
        "source_size": [w, h], "source_frames": total, "kept_frames": keep,
        "removed_trailing_frames": total - keep,
        "removed_trailing_ms": (ticks[-1] - ticks[keep]) * 10,
        "duration_ms": sum(all_delays[:keep]),
        "threshold": threshold if mode == "black" else None,
        "outline_source_px": {"inward": 2, "outward": 3, "total": 5} if mode == "black" else None,
        "padding_margin_source_px": margin,
    }
    return frames, whites, all_delays[:keep], palette, meta


def verify(path, expected_frames, masks, whites, delays, size):
    with Image.open(path) as im:
        require(im.size == (size, size) and im.info.get("loop") == 0,
                "Incorrect dimensions or loop flag.")
        times = []
        for i in range(im.n_frames):
            im.seek(i)
            times.append(im.info.get("duration", 0))
        require(sum(times) == sum(delays), "Timeline duration mismatch.")
        source_index, source_elapsed, out_elapsed = 0, 0, 0
        for i, delay in enumerate(times):
            im.seek(i)
            a = np.array(im.convert("RGBA"))
            end = out_elapsed + delay
            while source_index < len(delays) and source_elapsed < end:
                require(np.array_equal(a[:, :, 3] > 0, masks[source_index]),
                        "Transparency/disposal mismatch.")
                require(np.all(a[whites[source_index], :3] == 255), "Outline is not pure white.")
                expected = np.array(expected_frames[source_index].convert("RGBA"))
                require(np.array_equal(a, expected), "Frame pixels changed during GIF encoding.")
                source_elapsed += delays[source_index]
                source_index += 1
            require(source_elapsed == end, "Merged frame timing mismatch.")
            out_elapsed = end
        require(source_index == len(delays), "Missing output animation frames.")
        return im.n_frames


def export(frames, whites, delays, palette, size, target):
    pal = Image.new("P", (1, 1))
    pal.putpalette(palette.ravel().tolist())
    outputs, masks, white_masks = [], [], []
    for rgba, stroke in zip(frames, whites):
        a = np.array(Image.fromarray(rgba).resize((size, size), Image.Resampling.LANCZOS))
        visible = a[:, :, 3] >= 128
        coverage = np.array(Image.fromarray(stroke.astype(np.uint8) * 255).resize(
            (size, size), Image.Resampling.LANCZOS))
        white = (coverage >= 128) & visible
        rgb = a[:, :, :3].copy()
        rgb[~visible] = 255
        q = np.array(Image.fromarray(rgb).quantize(
            palette=pal, dither=Image.Dither.NONE)).copy()
        q[q == 255] = 0
        q[white] = 254  # Lock white AFTER quantization to prevent the pink rim.
        q[~visible] = 255
        f = Image.fromarray(q)
        f.putpalette(palette.ravel().tolist())
        f.info["transparency"] = 255
        outputs.append(f)
        masks.append(visible)
        white_masks.append(white)
    require(not target.exists(), f"Output exists: {target}")
    outputs[0].save(target, save_all=True, append_images=outputs[1:], duration=delays,
                    transparency=255, background=255, disposal=2, loop=0, optimize=False)
    count = verify(target, outputs, masks, white_masks, delays, size)
    return {"size": [size, size], "bytes": target.stat().st_size, "frames": count,
            "duration_ms": sum(delays), "loop": 0, "verified": True,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def safe_name(name):
    name = re.sub(r'[\\/\x00-\x1f<>:"|?*]', "_", name).strip(" .")
    require(name and name not in (".", ".."), "Empty or unsafe filename.")
    return name


def pick_name(stem, used, root):
    base = safe_name(stem)
    name, suffix = base, 2
    while name.casefold() in used or any(
        (directory / f"{name}.gif").exists()
        or (directory / f"{name}_{size}x{size}.gif").exists()
        for size in SIZES for directory in size_directories(root, size)
    ):
        name, suffix = f"{base}_{suffix}", suffix + 1
    used.add(name.casefold())
    return name


def copy_exclusive(src, dst):
    with src.open("rb") as reader, dst.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
    require(hashlib.sha256(src.read_bytes()).digest() == hashlib.sha256(dst.read_bytes()).digest(),
            f"Copy checksum mismatch: {dst}")


def run(args):
    require(shutil.which("ffprobe"), "ffprobe is required.")
    require(0 <= args.threshold <= 200, "threshold must be between 0 and 200.")
    paths = [p.resolve() for p in args.inputs]
    require(len(paths) == len(set(paths)), "Duplicate input paths.")
    require(all(p.is_file() and p.suffix.lower() == ".mov" for p in paths),
            "Pass existing MOV files explicitly, not folders.")
    preserve = {p.resolve() for p in args.preserve_background}
    require(preserve <= set(paths), "Each preserve-background path must also be an input.")
    # This CLI never guesses background mode. The agent must inspect and ask first.
    root = args.output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        (root / size_folder(size)).mkdir(exist_ok=True)
    batches = root / "batches"
    batches.mkdir(exist_ok=True)
    batch_id = safe_name(args.batch_id or datetime.now(timezone.utc).strftime("batch_%Y%m%d_%H%M%S_%f"))
    batch_dir = batches / batch_id
    require(not batch_dir.exists(), "Batch ID already exists; use a new ID.")
    # Reserve basenames across all sizes, case-insensitively for macOS/Windows.
    used = set()
    for size in SIZES:
        for directory in size_directories(root, size):
            if not directory.is_dir():
                continue
            for p in directory.iterdir():
                # Reserve modern and legacy names, case-insensitively, across folders.
                tail = f"_{size}x{size}.gif"
                if p.name.casefold().endswith(tail):
                    used.add(p.name[:-len(tail)].casefold())
                elif p.suffix.casefold() == ".gif":
                    used.add(p.stem.casefold())
    report = {"skill_version": VERSION, "batch_id": batch_id, "sizes": list(SIZES),
              "size_folders": {str(size): size_folder(size) for size in SIZES},
              "only_this_batch_in_zip": True, "items": []}
    # Validate every GIF in a clean staging area BEFORE appending to the live folders.
    with tempfile.TemporaryDirectory(prefix="mov-sticker-stage-") as staging:
        stage = Path(staging)
        pending = []
        for path in paths:
            name = pick_name(path.stem, used, root)
            mode = "preserve" if path in preserve else "black"
            frames, whites, delays, palette, meta = prepare(path, mode, args.threshold)
            meta["output_name"], meta["outputs"] = name, []
            for size in SIZES:
                relative = Path(size_folder(size)) / f"{name}.gif"  # size lives in the folder name
                dst = stage / relative
                dst.parent.mkdir(exist_ok=True)
                details = export(frames, whites, delays, palette, size, dst)
                details["path"] = relative.as_posix()
                meta["outputs"].append(details)
                pending.append(relative)
            report["items"].append(meta)
            print(json.dumps(meta, ensure_ascii=False), flush=True)
            del frames, whites
        require(len(pending) == 3 * len(paths), "Incorrect output count.")
        batch_dir.mkdir(exist_ok=False)
        # Fail rather than overwrite if another process creates a conflicting name.
        for relative in pending:
            copy_exclusive(stage / relative, root / relative)
        report_text = json.dumps(report, ensure_ascii=False, indent=2)
        with (batch_dir / "处理报告.json").open("x", encoding="utf-8") as f:
            f.write(report_text)
        lines = ["本压缩包仅包含本批新增GIF，不包含之前的成品。", "",
                 "尺寸：120x120、220x220、330x330；均无限循环。",
                 "文件夹：120gif、220gif、330gif；文件名只用表情名，不带尺寸。",
                 "黑底素材：透明背景；母版5px白描边（内2px/外3px），随尺寸等比缩放。",
                 "经用户确认保留装饰背景的素材：不抠图、不加白边、不自动裁尾。", ""]
        for item in report["items"]:
            lines.append(f"{item['source']}：{item['background']}；{item['duration_ms']/1000:.2f}秒；"
                         f"去除末尾{item['removed_trailing_frames']}帧。")
        zip_path = batch_dir / f"{batch_id}_三尺寸GIF.zip"
        with ZipFile(zip_path, "x", ZIP_DEFLATED) as z:
            for relative in pending:
                z.write(stage / relative, relative.as_posix())
            z.writestr("处理报告.json", report_text)
            z.writestr("说明.txt", "\n".join(lines) + "\n")
        with ZipFile(zip_path) as z:
            require(z.testzip() is None, "Archive CRC validation failed.")
            require(sum(n.endswith(".gif") for n in z.namelist()) == len(pending),
                    "Incorrect number of GIFs in ZIP.")
        print(json.dumps({"output_root": str(root), "batch_directory": str(batch_dir),
                          "zip": str(zip_path), "gif_count": len(pending)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-root", required=True, type=Path,
                        help="New or existing root; appends into 120gif/220gif/330gif without overwriting.")
    parser.add_argument("--batch-id", help="New batch name for its report and ZIP.")
    parser.add_argument("--threshold", type=int, default=96)
    parser.add_argument("--preserve-background", action="append", default=[], type=Path,
                        help="Repeat for each input explicitly confirmed to keep its background.")
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, FileExistsError) as e:
        parser.exit(2, f"ERROR: {e}\n")


if __name__ == "__main__":
    main()

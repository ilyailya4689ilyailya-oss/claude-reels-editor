#!/usr/bin/env python3
"""Create a rough talking-head edit by trimming detected silent intervals."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def duration_and_audio(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]).stdout)
    if not any(stream.get("codec_type") == "audio" for stream in data.get("streams", [])):
        raise ValueError("Input must have an audio stream")
    if not any(stream.get("codec_type") == "video" for stream in data.get("streams", [])):
        raise ValueError("Input must have a video stream")
    return float(data["format"]["duration"])


def silences(path, threshold, min_silence, duration):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
           f"silencedetect=noise={threshold}dB:d={min_silence}", "-f", "null", "-"]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])
    result_spans = []
    current = None
    for line in result.stderr.splitlines():
        start = re.search(r"silence_start:\s*([\d.]+)", line)
        end = re.search(r"silence_end:\s*([\d.]+)", line)
        if start:
            current = float(start.group(1))
        if end and current is not None:
            result_spans.append((current, float(end.group(1))))
            current = None
    if current is not None:
        result_spans.append((current, duration))
    return result_spans


def speaking_segments(silence_spans, duration, padding, minimum_clip=0.12):
    # Complement of the silent intervals. Preserve slight padding on both sides.
    raw = []
    cursor = 0.0
    for s, e in silence_spans:
        if s > cursor:
            raw.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        raw.append((cursor, duration))
    expanded = [(max(0.0, a - padding), min(duration, b + padding)) for a, b in raw]
    merged = []
    for a, b in expanded:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        elif b - a >= minimum_clip:
            merged.append((a, b))
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--noise", type=float, default=-35, help="Threshold in dB (default -35)")
    parser.add_argument("--min-silence", type=float, default=0.6, help="Minimum silence in seconds")
    parser.add_argument("--padding", type=float, default=0.15, help="Preserve seconds near speech")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.padding <= 2 or not 0.1 <= args.min_silence <= 10:
        parser.error("Check --padding and --min-silence values")
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must differ from input; original source is preserved")
    for binary in ["ffmpeg", "ffprobe"]:
        if not shutil.which(binary):
            parser.error(f"Missing {binary} on PATH")
    if not args.input.is_file():
        parser.error("Input file does not exist")
    try:
        duration = duration_and_audio(args.input)
        quiet = silences(args.input, args.noise, args.min_silence, duration)
        clips = speaking_segments(quiet, duration, args.padding)
        # If the entire source is silent, avoid silently exporting a blank result.
        if not clips:
            raise ValueError("No speech intervals were detected; try a different noise threshold")
        print(json.dumps({"input_seconds": round(duration, 2), "segments": [[round(a, 2), round(b, 2)] for a, b in clips]}, indent=2))
        if args.dry_run:
            return
        args.output.parent.mkdir(parents=True, exist_ok=True)
        filters = []
        for i, (a, b) in enumerate(clips):
            filters.append(f"[0:v:0]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS[v{i}]")
            filters.append(f"[0:a:0]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(clips)))
        filters.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=1[vout][aout]")
        cmd = ["ffmpeg", "-y", "-i", str(args.input), "-filter_complex", ";".join(filters),
               "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
               "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(args.output)]
        subprocess.run(cmd, check=True)
        print(f"Saved draft: {args.output}")
    except (subprocess.CalledProcessError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

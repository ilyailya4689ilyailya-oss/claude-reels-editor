# Claude Reels Editor 🎬

An open-source starter project for teaching **Claude Code** to assemble short, talking-head videos using local tools. It includes a real Python script that detects silence and makes a draft cut with FFmpeg.

> This is an early-stage personal project, not a finished professional editor or an official Anthropic integration.

## Features
- Detect quiet sections with FFmpeg's `silencedetect`.
- Cut long pauses while keeping a small amount of breathing room.
- Export a draft MP4 with H.264 video and AAC audio.
- Work locally: no API key or cloud upload required for the script.

## Requirements
- Python 3.9+
- FFmpeg and FFprobe installed and available on `PATH`

## Quick start

```bash
python3 reels_editor.py input.mp4 output.mp4
```

Adjust the silence detection or how much pause remains:

```bash
python3 reels_editor.py input.mp4 output.mp4 --noise -32 --min-silence 0.5 --padding 0.12
```

To preview the edit plan without encoding:

```bash
python3 reels_editor.py input.mp4 output.mp4 --dry-run
```

## Use with Claude Code

Open this repository in Claude Code and try this prompt:

> Review `reels_editor.py` and help me create a clean talking-head Reel. First run `--dry-run` and show the proposed cut segments. Then, only with my approval, run the export. Preserve the source video and suggest improvements to pacing, subtitle readability, and gentle zoom animations. Do not invent assets or use copyrighted clips without permission.

Claude Code can inspect and modify this project using its normal file and terminal tools, depending on the permissions you grant. It is not required to run the script.

## Limitations
- Requires an audio track.
- Silence is not the same as an uninteresting segment: review all cuts before posting.
- Produces draft jump cuts, not animated subtitles, meme assets, or final grading.
- Very long source videos can require substantial memory while rendering.

## Roadmap
- [ ] Human-reviewable edit decision list
- [ ] Animated captions using Remotion
- [ ] Optional picture-in-picture image cards
- [ ] Vertical video safe-area checks

## License
MIT (see `LICENSE`).

## Attribution
This repository is an independent community starter example and is not affiliated with Anthropic or OpenAI.

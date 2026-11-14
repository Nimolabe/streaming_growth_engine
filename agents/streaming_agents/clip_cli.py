"""Command-line offline clip candidate scan.

Example:
python -m streaming_agents.clip_cli --input my_stream.mp4 --json candidates.json
"""
import argparse
from pathlib import Path

from .agents.clip_export import export_clip_candidates
from .agents.clip_intelligence import ClipScanError, scan_recording
from .agents.clip_intelligence_contracts import ClipScanSettings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan your own local recording for audio peaks")
    parser.add_argument("--input", required=True, help="Existing WAV or video file")
    parser.add_argument("--json", help="Optional output path for candidate metadata")
    parser.add_argument("--extract-dir", help="Optional folder for MP4 review clips (video only)")
    parser.add_argument("--max-candidates", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        settings = ClipScanSettings(max_candidates=args.max_candidates)
        output = scan_recording(args.input, settings)
        if args.extract_dir:
            export_clip_candidates(args.input, output, args.extract_dir)
        serialized = output.model_dump_json(indent=2)
        if args.json:
            target = Path(args.json)
            if target.exists():
                raise ClipScanError("JSON output exists; choose a new path.")
            target.write_text(serialized + "\n", encoding="utf-8")
        else:
            print(serialized)
        return 0
    except (ClipScanError, ValueError, OSError) as exc:
        parser.exit(2, f"Clip Intelligence: {exc}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

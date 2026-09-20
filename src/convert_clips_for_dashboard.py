"""Convert analysis clips to browser-compatible H.264 MP4 files."""

from pathlib import Path
import subprocess

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis_output" / "selected_clips"
DESTINATION = ROOT / "analysis_output" / "web_clips"


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for source in sorted(SOURCE.glob("*.mp4")):
        destination = DESTINATION / source.name
        subprocess.run(
            [
                ffmpeg, "-y", "-i", str(source),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-an", str(destination),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Converted {source.name}")


if __name__ == "__main__":
    main()

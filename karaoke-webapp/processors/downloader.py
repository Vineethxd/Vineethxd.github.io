import sys
import subprocess
from pathlib import Path


def download_youtube(url: str, job_id: str, upload_dir: str) -> str:
    """Download audio from a YouTube URL via yt-dlp; returns path to .mp3 file."""
    out_template = str(Path(upload_dir) / f"{job_id}.%(ext)s")

    result = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--no-playlist",
            "-o", out_template,
            url,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    out = Path(upload_dir) / f"{job_id}.mp3"
    if not out.exists():
        raise FileNotFoundError(
            f"Downloaded audio not found at {out}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    return str(out)

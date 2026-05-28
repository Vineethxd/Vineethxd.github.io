import sys
import subprocess
from pathlib import Path

_RUNNER = Path(__file__).parent / "demucs_runner.py"


def _get_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def separate_vocals(audio_path: str, work_dir: str) -> str:
    """Run demucs with --two-stems=vocals; returns path to no_vocals.wav."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, str(_RUNNER),
            "--two-stems=vocals",
            "--device", _get_device(),
            "-n", "htdemucs",
            "-o", str(work),
            audio_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"demucs failed:\n{result.stderr}")

    stem = Path(audio_path).stem
    no_vocals = work / "htdemucs" / stem / "no_vocals.wav"

    if not no_vocals.exists():
        raise FileNotFoundError(
            f"Expected demucs output not found at {no_vocals}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    return str(no_vocals)

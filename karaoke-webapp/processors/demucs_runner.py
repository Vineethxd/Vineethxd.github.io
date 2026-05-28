"""
Wrapper that replaces torchaudio.save with a soundfile-based implementation
before demucs is imported, bypassing the torchcodec/FFmpeg DLL requirement.
"""
import sys
import numpy as np
import soundfile as sf
import torchaudio


def _sf_save(uri, src, sample_rate, **kwargs):
    wav = src.cpu().numpy().T  # (samples, channels)
    if wav.dtype not in (np.float32, np.float64):
        wav = wav.astype(np.float32)
    sf.write(str(uri), wav, int(sample_rate))


# Patch before demucs.audio imports torchaudio
torchaudio.save = _sf_save

from demucs.__main__ import main  # noqa: E402
main()

import os
from groq import Groq


def transcribe_audio(audio_path: str, custom_lyrics: str | None = None) -> list[dict]:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )

    segments = []
    for seg in response.segments:
        start = seg["start"] if isinstance(seg, dict) else seg.start
        end   = seg["end"]   if isinstance(seg, dict) else seg.end
        text  = seg["text"]  if isinstance(seg, dict) else seg.text
        if text.strip() and start is not None and end is not None:
            segments.append({
                "start": float(start),
                "end":   float(end),
                "text":  text.strip(),
                "words": [],
            })

    if not segments:
        raise ValueError("Whisper returned no usable segments with timestamps.")

    # Attach word-level timestamps to their parent segment
    raw_words = getattr(response, "words", None) or []
    seg_idx = 0
    for w in raw_words:
        ws = w["start"] if isinstance(w, dict) else w.start
        we = w["end"]   if isinstance(w, dict) else w.end
        wt = w["word"]  if isinstance(w, dict) else w.word
        if ws is None or we is None or not wt.strip():
            continue
        ws, we = float(ws), float(we)
        while seg_idx < len(segments) - 1 and ws >= segments[seg_idx]["end"]:
            seg_idx += 1
        segments[seg_idx]["words"].append({"word": wt.strip(), "start": ws, "end": we})

    # Custom lyrics: replace text (drop word timing since text changed)
    if custom_lyrics and custom_lyrics.strip():
        lines = [l.strip() for l in custom_lyrics.strip().splitlines() if l.strip()]
        if len(lines) == len(segments):
            for seg, line in zip(segments, lines):
                seg["text"] = line
                seg["words"] = []

    return segments

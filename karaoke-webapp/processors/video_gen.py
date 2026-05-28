from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from moviepy.editor import AudioFileClip, ColorClip, CompositeVideoClip, ImageClip

WIDTH, HEIGHT = 1280, 720
BG         = (8,   8,  20)
C_CURR     = (255, 255, 255)
C_CTX      = (65,  65,  85)
NEON_AMBER = (255, 180, 40)
NEON_BLUE  = (80, 140, 255)

_FONT_PATHS = [
    ("C:/Windows/Fonts/Nirmala.ttc",   1),
    ("C:/Windows/Fonts/Nirmala.ttc",   0),
    ("C:/Windows/Fonts/segoeuib.ttf",  0),
    ("C:/Windows/Fonts/segoeui.ttf",   0),
    ("C:/Windows/Fonts/arialuni.ttf",  0),
    ("C:/Windows/Fonts/arialbd.ttf",   0),
    ("C:/Windows/Fonts/arial.ttf",     0),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
]

_SYMBOL_FONT_PATHS = [
    "C:/Windows/Fonts/seguisym.ttf",
    "C:/Windows/Fonts/segmdl2.ttf",
    "C:/Windows/Fonts/wingding.ttf",
]

_DUMMY = Image.new("RGB", (1, 1))
_DD    = ImageDraw.Draw(_DUMMY)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path, idx in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()


def _symbol_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _SYMBOL_FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return _font(size)


def _tw(text: str, font) -> float:
    return _DD.textlength(text, font=font)


def _wrap(text: str, font, max_px: int) -> list[str]:
    words = text.split()
    lines, cur, cur_w = [], [], 0.0
    sp = _tw(" ", font)
    for w in words:
        ww = _tw(w, font)
        if cur and cur_w + sp + ww > max_px:
            lines.append(" ".join(cur))
            cur, cur_w = [w], ww
        else:
            cur_w = cur_w + (sp if cur else 0) + ww
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def _neon_overlay(base: Image.Image, text_lines: list[str], font, line_h: int,
                  cx: int, y0: int, color: tuple) -> Image.Image:
    for radius, alpha in ((20, 28), (9, 50), (3, 80)):
        g  = Image.new("RGBA", base.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        y  = y0
        for line in text_lines:
            gd.text((cx - int(_tw(line, font)) // 2, y), line,
                    font=font, fill=(*color[:3], int(255 * alpha / 100)))
            y += line_h
        g    = g.filter(ImageFilter.GaussianBlur(radius))
        base = Image.alpha_composite(base.convert("RGBA"), g).convert("RGB")
    return base


def _lyric_frame(prev: str, curr: str, nxt: str) -> np.ndarray:
    cx, cy  = WIDTH // 2, HEIGHT // 2
    margin  = 100
    max_px  = WIDTH - 2 * margin

    f_curr  = _font(68)
    f_ctx   = _font(38)
    lh_curr = f_curr.size + 10
    lh_ctx  = f_ctx.size  + 8

    curr_lines = _wrap(curr, f_curr, max_px)
    total_curr = len(curr_lines) * lh_curr
    y_curr     = cy - total_curr // 2

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    img  = _neon_overlay(img, curr_lines, f_curr, lh_curr, cx, y_curr, NEON_AMBER)
    draw = ImageDraw.Draw(img)

    if prev:
        prev_lines = _wrap(prev, f_ctx, max_px)
        prev_h     = len(prev_lines) * lh_ctx
        y = y_curr - 28 - prev_h
        for line in prev_lines:
            draw.text((cx - int(_tw(line, f_ctx)) // 2, y), line, font=f_ctx, fill=C_CTX)
            y += lh_ctx

    y = y_curr
    for line in curr_lines:
        draw.text((cx - int(_tw(line, f_curr)) // 2, y), line, font=f_curr, fill=C_CURR)
        y += lh_curr

    if nxt:
        y = y_curr + total_curr + 28
        for line in _wrap(nxt, f_ctx, max_px):
            draw.text((cx - int(_tw(line, f_ctx)) // 2, y), line, font=f_ctx, fill=C_CTX)
            y += lh_ctx

    return np.array(img)


def _gap_frame(label: str = "♪", sub: str = "") -> np.ndarray:
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    f    = _symbol_font(110)
    fs   = _font(36)
    img  = _neon_overlay(img, [label], f, f.size + 10,
                         WIDTH // 2, HEIGHT // 2 - f.size // 2, NEON_BLUE)
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH // 2 - int(_tw(label, f)) // 2,
               HEIGHT // 2 - f.size // 2),
              label, font=f, fill=NEON_BLUE)
    if sub:
        draw.text((WIDTH // 2 - int(_tw(sub, fs)) // 2,
                   HEIGHT // 2 + f.size // 2 + 18),
                  sub, font=fs, fill=C_CTX)
    return np.array(img)


def _countdown_frame(n: int) -> np.ndarray:
    img   = Image.new("RGB", (WIDTH, HEIGHT), BG)
    f     = _font(160)
    fs    = _font(34)
    label = str(n)
    sub   = "get ready..."
    img   = _neon_overlay(img, [label], f, f.size + 10,
                           WIDTH // 2, HEIGHT // 2 - f.size // 2, NEON_AMBER)
    draw  = ImageDraw.Draw(img)
    draw.text((WIDTH // 2 - int(_tw(label, f)) // 2,
               HEIGHT // 2 - f.size // 2),
              label, font=f, fill=C_CURR)
    draw.text((WIDTH // 2 - int(_tw(sub, fs)) // 2,
               HEIGHT // 2 + f.size // 2 + 20),
              sub, font=fs, fill=C_CTX)
    return np.array(img)


_MUSIC_FRAME = None
_CD_FRAMES   = {}


def _get_music_frame():
    global _MUSIC_FRAME
    if _MUSIC_FRAME is None:
        _MUSIC_FRAME = _gap_frame("♪", "instrumental")
    return _MUSIC_FRAME


def _get_cd_frame(n):
    if n not in _CD_FRAMES:
        _CD_FRAMES[n] = _countdown_frame(n)
    return _CD_FRAMES[n]


def create_karaoke_video(instrumental_path: str, segments: list[dict], output_path: str):
    audio    = AudioFileClip(instrumental_path)
    duration = audio.duration
    if duration is None:
        import soundfile as sf
        duration = float(sf.info(instrumental_path).duration)
        audio = audio.set_duration(duration)

    bg    = ColorClip(size=(WIDTH, HEIGHT), color=list(BG)).set_duration(duration)
    clips = [bg]
    MAX_EXT = 3.0

    def _add(frame, t_start, t_end):
        d = max(0.05, t_end - t_start)
        clips.append(ImageClip(frame).set_start(t_start).set_duration(d))

    # gap before first lyric
    if segments:
        first_start = float(segments[0]["start"])
        if first_start >= 1.0:
            music_dur = max(0, first_start - 3.0)
            if music_dur > 0:
                _add(_get_music_frame(), 0, music_dur)
            for beat in (3, 2, 1):
                t = first_start - beat
                if t >= 0:
                    _add(_get_cd_frame(beat), t, min(t + 1.0, first_start - 0.04))

    for i, seg in enumerate(segments):
        seg_start  = float(seg["start"])
        seg_end    = float(seg["end"])
        prev_text  = segments[i - 1]["text"] if i > 0 else ""
        nxt_text   = segments[i + 1]["text"] if i < len(segments) - 1 else ""
        next_start = float(segments[i + 1]["start"]) if i < len(segments) - 1 else duration

        display_end = min(next_start - 0.04, seg_end + MAX_EXT)
        display_end = max(display_end, seg_end)

        frame = _lyric_frame(prev_text, seg["text"], nxt_text)
        _add(frame, seg_start, display_end)

        gap_start = display_end
        gap_end   = next_start
        gap       = gap_end - gap_start

        if gap >= 1.0 and i < len(segments) - 1:
            music_dur = max(0, gap - 3.0)
            if music_dur > 0:
                _add(_get_music_frame(), gap_start, gap_start + music_dur)
            for beat in (3, 2, 1):
                t = gap_end - beat
                if t >= gap_start:
                    _add(_get_cd_frame(beat), t, min(t + 1.0, gap_end - 0.04))

    video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT)).set_audio(audio)
    video.write_videofile(
        output_path, fps=24, codec="libx264", audio_codec="aac", logger=None
    )

import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()

UPLOAD_DIR = Path("uploads")
WORK_DIR = Path("work")
OUTPUT_DIR = Path("outputs")
for _d in [UPLOAD_DIR, WORK_DIR, OUTPUT_DIR]:
    _d.mkdir(exist_ok=True)

jobs: dict[str, dict] = {}


def _update(job_id: str, status: str, progress: int):
    jobs[job_id] = {"status": status, "progress": progress, "error": None}


def run_pipeline(job_id: str, audio_path: Optional[str], custom_lyrics: Optional[str], youtube_url: Optional[str] = None):
    try:
        if youtube_url:
            _update(job_id, "downloading", 5)
            from processors.downloader import download_youtube
            audio_path = download_youtube(youtube_url, job_id, str(UPLOAD_DIR))

        _update(job_id, "separating", 25 if youtube_url else 10)
        from processors.separator import separate_vocals
        instrumental = separate_vocals(audio_path, str(WORK_DIR / job_id))

        _update(job_id, "transcribing", 55 if youtube_url else 50)
        from processors.transcriber import transcribe_audio
        segments = transcribe_audio(audio_path, custom_lyrics)

        _update(job_id, "generating_video", 80 if youtube_url else 75)
        from processors.video_gen import create_karaoke_video
        out = str(OUTPUT_DIR / f"{job_id}.mp4")
        create_karaoke_video(instrumental, segments, out)

        jobs[job_id] = {"status": "done", "progress": 100, "error": None}

    except Exception as exc:
        import traceback
        jobs[job_id] = {"status": "error", "progress": 0, "error": traceback.format_exc()}


@app.post("/process")
async def process_audio(
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    lyrics: Optional[str] = Form(None),
):
    if not audio and not youtube_url:
        return JSONResponse({"error": "Provide an audio file or a YouTube URL."}, status_code=400)

    job_id = str(uuid.uuid4())

    if audio:
        ext = Path(audio.filename).suffix or ".mp3"
        upload_path = UPLOAD_DIR / f"{job_id}{ext}"
        with open(upload_path, "wb") as f:
            f.write(await audio.read())
        audio_path = str(upload_path)
    else:
        audio_path = None

    jobs[job_id] = {"status": "queued", "progress": 0, "error": None}
    background_tasks.add_task(
        run_pipeline, job_id, audio_path, lyrics or None, youtube_url or None
    )

    return {"job_id": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return jobs[job_id]


@app.get("/download/{job_id}")
def download(job_id: str):
    out = OUTPUT_DIR / f"{job_id}.mp4"
    if not out.exists():
        return JSONResponse({"error": "Video not ready"}, status_code=404)
    return FileResponse(str(out), media_type="video/mp4", filename="karaoke.mp4")


app.mount("/", StaticFiles(directory="static", html=True), name="static")

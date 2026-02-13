from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import uvicorn
import sqlite3
import torch
import subprocess
import tempfile
import os
import datetime

DB = "notes.db"
MODEL = "small"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE = "int8_float16"

print("Loading Whisper...")
whisper = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE)
print("Whisper ready.")

app = FastAPI()

# ---- DB ----

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            transcript TEXT,
            summary TEXT,
            audio_path TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---- API ----

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        audio_path = tmp.name

    segments, info = whisper.transcribe(audio_path)
    text = "".join([s.text for s in segments]).strip()

    return {"transcript": text}


@app.post("/summarize")
async def summarize(payload: dict):
    text = payload["text"]

    prompt = f"""
Convert the dictation into structured clinical bullet points.
Normalize language. Do not invent diagnoses.

Dictation:
{text}
"""

    result = subprocess.run(
        ["ollama", "run", "llama3", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    summary = result.stdout.decode(errors="ignore").strip()
    return {"summary": summary}


@app.post("/save")
async def save(payload: dict):
    transcript = payload["transcript"]
    summary = payload["summary"]
    audio_path = payload["audio_path"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO notes (timestamp, transcript, summary, audio_path) VALUES (?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(), transcript, summary, audio_path)
    )
    conn.commit()
    conn.close()

    return {"status": "ok"}


@app.get("/history")
async def history():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, transcript, summary, audio_path FROM notes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return {"notes": rows}


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000)

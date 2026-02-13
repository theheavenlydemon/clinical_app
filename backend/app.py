import os
import sqlite3
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "records.db")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            transcript TEXT,
            summary TEXT,
            audio_file TEXT,
            timestamp INTEGER,
            status TEXT
        )
    """)
    c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    failed_attempts INTEGER DEFAULT 0,
    locked_until INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0
)
""")


    conn.commit()
    conn.close()

init_db()
print("DB INITIALIZED AT:", DB)


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
import sqlite3
import uuid
import time
import os
import subprocess
import torch

app = FastAPI()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set in environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- WHISPER ----------

device = "cuda" if torch.cuda.is_available() else "cpu"
compute = "float16" if device == "cuda" else "int8"

whisper = WhisperModel("small", device=device, compute_type=compute)

print("Whisper using:", device)

# ---------- SUMMARY ----------

def summarize(text):
    try:
        prompt = f"Convert to clinical SOAP notes:\n{text}"

        r = subprocess.run(
            ["ollama", "run", "phi3:mini"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            shell=True  # keep this on Windows
        )

        out = r.stdout.decode("utf-8", errors="ignore").strip()
        return out if out else "Summary unavailable."

    except Exception as e:
        print("Ollama error:", e)
        return "Summary unavailable."


# ---------- ROUTES ----------
from password_validator import PasswordValidator

password_schema = PasswordValidator()
password_schema.min(8).has().uppercase().has().lowercase().has().digits().has().symbols()

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_verification_token(email: str):
    return jwt.encode(
        {
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(401, "Invalid token")


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    patient_id: str = Form(...),
    user = Depends(get_current_user)
):
    sid = str(uuid.uuid4())
    audio_path = f"{AUDIO_DIR}/{sid}.webm"

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    segments, _ = whisper.transcribe(audio_path)
    transcript = "".join([s.text for s in segments]).strip()

    if not transcript:
        transcript = "No speech detected."

    # ✅ Save session with EMPTY summary + pending status
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions VALUES (?,?,?,?,?,?,?)",
        (
            sid,
            patient_id,
            transcript,
            "",                 # summary empty
            audio_path,
            int(time.time()),
            "pending"           # 👈 THIS IS CRITICAL
        )
    )
    conn.commit()
    conn.close()

    return {
        "id": sid,
        "transcript": transcript
    }

@app.get("/summary/{sid}")
def generate_summary(sid: str):
    user = Depends(get_current_user)
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    row = c.execute(
        "SELECT transcript, summary, status FROM sessions WHERE id=?",
        (sid,)
    ).fetchone()

    if not row:
        conn.close()
        return {"summary": "Session not found."}

    transcript, summary, status = row

    if status == "done" and summary:
        conn.close()
        return {"summary": summary}

    if status == "processing":
        conn.close()
        return {"summary": "Summarizing..."}

    # lock
    c.execute(
        "UPDATE sessions SET status=? WHERE id=?",
        ("processing", sid)
    )
    conn.commit()
    conn.close()

    summary = summarize(transcript)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "UPDATE sessions SET summary=?, status=? WHERE id=?",
        (summary, "done", sid)
    )
    conn.commit()
    conn.close()

    return {"summary": summary}

@app.get("/history/{pid}")
def history(pid: str):
    user = Depends(get_current_user)
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if pid == "":
        rows = c.execute(
            "SELECT * FROM sessions ORDER BY timestamp DESC"
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM sessions WHERE patient_id LIKE ? ORDER BY timestamp DESC",
            (f"%{pid}%",)
        ).fetchall()

    conn.close()

    return [
        {
            "id": r[0],
            "patient_id": r[1],
            "transcript": r[2],
            "summary": r[3],
            "audio": r[4],
            "timestamp": r[5]
        }
        for r in rows
    ]

@app.get("/history")
def all_history():
    user = Depends(get_current_user)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute(
        "SELECT * FROM sessions ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "patient_id": r[1],
            "transcript": r[2],
            "summary": r[3],
            "audio": r[4],
            "timestamp": r[5]
        }
        for r in rows
    ]


@app.get("/audio/{filename}")
def audio(filename: str):
    user = Depends(get_current_user)
    return FileResponse(f"{AUDIO_DIR}/{filename}")

@app.delete("/session/{sid}")
def delete_session(sid: str):
    user = Depends(get_current_user)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.post("/register")
def register(email: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Password strength check
    if not password_schema.validate(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be 8+ chars with uppercase, lowercase, number, and symbol"
        )
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
        status_code=400,
        detail="Password too long (max 72 characters)."
    )


    hashed = hash_password(password)

    try:
        c.execute(
            "INSERT INTO users(email,password,role) VALUES (?,?,?)",
            (email, hashed, "doctor")
        )
        conn.commit()
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="User exists")

    conn.close()
    return {"status": "created"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Get user by email
    user = c.execute(
        "SELECT * FROM users WHERE email=?",
        (form_data.username,)
    ).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    import time
    now = int(time.time())

    # ---------- STEP 4: Account Lock Check ----------

    if user[5] and user[5] > now:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Account temporarily locked. Try again later."
        )

    # ---------- Password Check ----------

    if not verify_password(form_data.password, user[2]):

        failed_attempts = user[4] + 1
        lock_time = 0

        if failed_attempts >= 5:
            lock_time = now + 300  # lock for 5 minutes

        c.execute(
            "UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
            (failed_attempts, lock_time, user[0])
        )
        conn.commit()
        conn.close()

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ---------- Reset Failed Attempts on Success ----------

    c.execute(
        "UPDATE users SET failed_attempts=0, locked_until=0 WHERE id=?",
        (user[0],)
    )
    conn.commit()

    # ---------- STEP 5: Email Verification Check ----------

    if user[6] == 0:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in."
        )

    conn.close()

    # ---------- Generate JWT Token ----------

    token = create_token({
        "sub": user[1],
        "role": user[3]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

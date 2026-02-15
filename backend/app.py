import os
import sqlite3
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

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
    c.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    action TEXT,
    patient_id TEXT,
    session_id TEXT,
    timestamp INTEGER
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

def create_reset_token(email: str):
    return jwt.encode(
        {
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def log_action(user_email, action, patient_id=None, session_id=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO audit_logs (user_email, action, patient_id, session_id, timestamp) VALUES (?,?,?,?,?)",
        (
            user_email,
            action,
            patient_id,
            session_id,
            int(time.time())
        )
    )

    conn.commit()
    conn.close()


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_verification_email(to_email, token):
    verification_link = f"http://127.0.0.1:8000/verify/{token}"

    message = MIMEMultipart()
    message["From"] = EMAIL_USER
    message["To"] = to_email
    message["Subject"] = "Verify Your Clinical App Account"

    body = f"""
    Welcome to Clinical Dictation System.

    Please click the link below to verify your account:

    {verification_link}

    This link expires in 24 hours.
    """

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, message.as_string())
        server.quit()
        print("Verification email sent to", to_email)
    except Exception as e:
        print("Email sending failed:", e)

def send_reset_email(to_email, token):
    reset_link = f"http://127.0.0.1:5173/reset/{token}"

    message = MIMEMultipart()
    message["From"] = EMAIL_USER
    message["To"] = to_email
    message["Subject"] = "Reset Your Clinical App Password"

    body = f"""
You requested a password reset.

Click the link below to set a new password:

{reset_link}

This link expires in 1 hour.
"""

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, message.as_string())
        server.quit()
        print("Reset email sent to", to_email)
    except Exception as e:
        print("Reset email failed:", e)


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

    log_action(user["sub"], "transcription_created", patient_id, sid)

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
    log_action(user["sub"], "session_deleted", None, sid)
    return {"status": "deleted"}

@app.post("/register")
def register(email: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Password strength check
    if not password_schema.validate(password):
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Password must be 8+ chars with uppercase, lowercase, number, and symbol"
        )

    # bcrypt limit check
    if len(password.encode("utf-8")) > 72:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 characters)."
        )

    hashed = hash_password(password)

    try:
        c.execute(
            "INSERT INTO users(email,password,role,verified) VALUES (?,?,?,?)",
            (email, hashed, "doctor", 0)
        )
        conn.commit()

    except:
        conn.close()
        raise HTTPException(status_code=400, detail="User exists")

    # Create verification token AFTER successful insert
    token = create_verification_token(email)
    send_verification_email(email, token)

    conn.close()

    return {
    "status": "Registration successful. Check your email to verify."
}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    user = c.execute(
        "SELECT * FROM users WHERE email=?",
        (form_data.username,)
    ).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check password
    if not verify_password(form_data.password, user[2]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 🔥 FIXED VERIFICATION CHECK
    if user[6] == 0:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in."
        )

    token = create_token({
        "sub": user[1],
        "role": user[3]
    })

    log_action(user[1], "login_success")


    conn.close()

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/forgot-password")
def forgot_password(email: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    user = c.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    # Always return same response (security best practice)
    if user:
        token = create_reset_token(email)
        send_reset_email(email, token)

    conn.close()

    return {"status": "If account exists, reset email sent."}

@app.post("/reset-password/{token}")
def reset_password(token: str, new_password: str = Form(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["email"]

        if not password_schema.validate(new_password):
            raise HTTPException(
                status_code=400,
                detail="Password must meet complexity requirements."
            )

        hashed = hash_password(new_password)

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed, email)
        )

        conn.commit()
        conn.close()

        return {"status": "Password reset successful"}

    except Exception as e:
        print("Reset error:", e)
        raise HTTPException(status_code=400, detail="Invalid or expired token")


@app.get("/audit")
def get_audit(user=Depends(get_current_user)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    logs = c.execute(
        "SELECT * FROM audit_logs ORDER BY timestamp DESC"
    ).fetchall()

    conn.close()

    return logs

# MediScript — AI-Driven Clinical Voice Dictation

> Automated clinical documentation platform built for CubeAI Solutions Tech Pvt Ltd.  
> Record a consultation → AI generates SOAP notes → Doctor approves → Patient portal publishes.

![React](https://img.shields.io/badge/React-18-blue?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-green?logo=fastapi)
![Whisper](https://img.shields.io/badge/Whisper-distil--large--v3-purple)
![LLaMA](https://img.shields.io/badge/LLaMA-3.2%20%7C%203.1-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What is MediScript?

MediScript is a web-based clinical dictation system that replaces manual transcription in outpatient consultation settings. A doctor records their consultation, and the system handles the rest:

1. **Transcribes** the audio using a locally hosted Whisper model
2. **Generates** a structured SOAP note using LLaMA via Ollama, with the patient's previous visit history as context (RAG)
3. **Suggests** ICD-10 diagnosis codes and detects drug interactions via Groq API
4. **Presents** everything to the doctor for review and editing
5. **Publishes** the approved report to a patient-facing portal

Patient audio never leaves the clinic machine. All AI processing for transcription and summarisation runs locally on GPU.

---

## Live Demo (when running on local machine)

| Interface | URL |
|---|---|
| Doctor / Admin App | https://clinicalapp-eta.vercel.app |
| Patient Portal | https://clinicalapp-eta.vercel.app/portal |
| Backend API Docs | https://formerly-perforated-scotty.ngrok-free.dev/docs *(requires backend running)* |

---

## Features

### Clinical Workflow
- 🎙️ One-click voice recording directly in the browser
- 📋 Automatic SOAP note generation (Subjective / Objective / Assessment / Plan)
- 🏷️ AI-suggested ICD-10-CM diagnosis codes with doctor editing
- ⚠️ Clinical anomaly detection — drug interactions, missed follow-ups, dosage concerns
- 👤 Longitudinal patient memory — previous visit summaries included in AI context (RAG)
- ✅ Explicit doctor approval before any content reaches patients
- 📄 PDF and DOCX report download

### Indian Language Support
- 🇮🇳 Tamil, Hindi, Telugu, Kannada, Malayalam and more via Sarvam AI saaras:v3
- Auto-translate to English — same pipeline as English consultations

### Patient Portal
- Patients view only their doctor-approved visit reports
- Formatted clinical report with diagnosis codes
- PDF download
- GDPR data export (Article 15 & 20)

### Admin Panel
- Create patient portal accounts with automatic email credential delivery
- Paginated audit log viewer with colour-coded action types
- NHS DSPT 8-year data retention review

### Security & Compliance
- 🔒 AES-256 encryption of all transcripts, summaries, and audio files at rest
- JWT authentication with 8-hour expiry and role-based access control
- bcrypt password hashing with account lockout
- Full audit trail on every API action
- GDPR Article 15 (access), 17 (erasure), 20 (portability) all implemented
- NHS DSPT retention review built into admin panel

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VERCEL (always online)                │
│              React Frontend — clinicalapp-eta.vercel.app │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────────┐
│              NGROK HTTPS TUNNEL                         │
│        formerly-perforated-scotty.ngrok-free.dev        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              LOCAL MACHINE (clinic hardware)             │
│                                                         │
│  FastAPI (port 8000)                                    │
│  ├── Whisper distil-large-v3  ← English STT (GPU)      │
│  ├── Ollama LLaMA 3.2 3B      ← SOAP generation (GPU)  │
│  ├── SQLite (AES-256 encrypted)                         │
│  └── Audio file store (AES-256 encrypted)               │
│                                                         │
│  External APIs (text only, de-identified):              │
│  ├── Groq → LLaMA 3.1 8B  ← ICD-10 + anomaly detection │
│  └── Sarvam AI saaras:v3  ← Indian language STT        │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, React Router DOM, jwt-decode |
| Backend | FastAPI, Uvicorn, Python 3.10+ |
| Database | SQLite (sessions, users, audit_logs) |
| English STT | Whisper distil-large-v3 (HuggingFace Transformers + PyTorch + CUDA) |
| Indian STT | Sarvam AI saaras:v3 (cloud API) |
| SOAP Generation | LLaMA 3.2 3B via Ollama (local) |
| ICD-10 + Anomalies | LLaMA 3.1 8B via Groq API (cloud, de-identified text only) |
| Audio Processing | librosa (16kHz resampling) |
| Encryption | AES-256 Fernet (cryptography library) |
| Authentication | JWT (python-jose) + bcrypt |
| PDF Reports | reportlab |
| DOCX Reports | Node.js docx package (via subprocess) |
| Email | smtplib + Gmail SMTP (TLS) |
| Tunnel | Ngrok static domain |
| Hosting | Vercel (frontend) |

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Conda (for environment management)
- NVIDIA GPU with CUDA support (GTX 1650 4GB minimum)
- CUDA Toolkit installed
- Ollama installed ([ollama.ai](https://ollama.ai))
- Ngrok account with a free static domain ([ngrok.com](https://ngrok.com))

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/mediscript.git
cd mediscript
```

### 2. Backend setup

```bash
cd backend

# Create and activate conda environment
conda create -n whisper python=3.10
conda activate whisper

# Install Python dependencies
pip install fastapi uvicorn python-jose[cryptography] bcrypt cryptography \
  transformers torch torchaudio librosa python-multipart sqlalchemy \
  reportlab requests python-dotenv groq
```

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-secret-key-minimum-32-characters-long
GROQ_API_KEY=your-groq-api-key
SARVAM_API_KEY=your-sarvam-api-key
SMTP_EMAIL=your-gmail-address@gmail.com
SMTP_PASSWORD=your-gmail-app-password
FRONTEND_URL=https://clinicalapp-eta.vercel.app
BACKEND_URL=https://your-ngrok-domain.ngrok-free.dev
```

### 3. Pull the LLaMA model

```bash
ollama pull llama3.2:3b
```

### 4. Frontend setup

```bash
cd frontend
npm install
```

### 5. Deploy frontend to Vercel

```bash
npm install -g vercel
vercel --prod
```

---

## Running the Application

Every time you want the application online, start these three processes in order:

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — Backend:**
```bash
cd backend
conda activate whisper
uvicorn app:app --host 0.0.0.0 --port 8000
```

Wait for:
```
✅ Model loaded!
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 3 — Ngrok:**
```bash
ngrok http 8000 --domain=your-static-domain.ngrok-free.dev
```

Then open `https://your-vercel-url.vercel.app` in the browser.

---

## Database

SQLite database is created automatically on first run at `backend/records.db`.

Schema:

```sql
-- Clinical sessions
sessions (id, patient_id, transcript, summary, audio_file, timestamp,
          status, doctor_name, icd_codes, alerts, report_data)

-- Users (all roles)
users (id, email, password, role, patient_id, name, verified,
       failed_attempts, locked_until)

-- Full audit trail
audit_logs (id, user_email, action, patient_id, session_id, timestamp)
```

Session status flow: `pending` → `done` → `approved`

Only sessions with `status = 'approved'` are visible on the patient portal.

---

## API Routes

### Authentication
| Method | Route | Description |
|---|---|---|
| POST | `/login` | Login, returns JWT |
| POST | `/register` | Register new doctor account |
| GET | `/verify/{token}` | Email verification |
| POST | `/forgot-password` | Send password reset email |
| POST | `/reset-password/{token}` | Reset password |

### Clinical (Doctor)
| Method | Route | Description |
|---|---|---|
| POST | `/transcribe` | Upload audio, start AI pipeline |
| POST | `/transcribe-indian` | Indian language audio |
| GET | `/summary/{sid}` | Poll for SOAP note completion |
| GET | `/history/{pid}` | Patient session history |
| GET | `/patient-brief/{pid}` | Quick patient summary |
| PATCH | `/session/{sid}/approve` | Approve and publish to portal |
| POST | `/icd-codes/{sid}` | Update ICD codes |
| DELETE | `/session/{sid}` | Delete session |
| POST | `/report/{sid}/pdf` | Generate PDF report |
| POST | `/report/{sid}/docx` | Generate DOCX report |
| GET | `/audio-stream/{filename}` | Stream decrypted audio |

### Patient Portal
| Method | Route | Description |
|---|---|---|
| GET | `/portal/my-sessions` | Patient's approved sessions |
| GET | `/portal/session/{sid}` | Single session detail |
| GET | `/portal/export` | GDPR data export (Art. 15 & 20) |

### Admin
| Method | Route | Description |
|---|---|---|
| POST | `/admin/create-patient` | Create patient portal account |
| GET | `/admin/patients` | List all patients |
| DELETE | `/admin/patient/{id}` | GDPR erasure (Art. 17) |
| GET | `/admin/audit-logs` | Paginated audit trail |
| GET | `/admin/retention-review` | NHS DSPT 8-year review |

---

## User Roles

| Role | Access | Login URL |
|---|---|---|
| `doctor` | Main app — dictate, review, approve | `/` |
| `admin` | Main app + admin panel | `/` |
| `patient` | Patient portal only | `/portal` |

Patient accounts are created by admin/doctor through the Admin Panel. Credentials are emailed automatically.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (minimum 32 characters) |
| `GROQ_API_KEY` | Groq cloud API key |
| `SARVAM_API_KEY` | Sarvam AI API key |
| `SMTP_EMAIL` | Gmail address for sending emails |
| `SMTP_PASSWORD` | Gmail app password (not account password) |
| `FRONTEND_URL` | Vercel frontend URL |
| `BACKEND_URL` | Ngrok backend URL |
| `ENCRYPTION_KEY` | Fernet encryption key (generate with `Fernet.generate_key()`) |

---

## Performance

Evaluated on two recorded clinical sessions with human-verified reference transcripts:

| Session | Description | WER | CER |
|---|---|---|---|
| Session 1 | First visit — URTI | 15.09% | 7.31% |
| Session 2 | Follow-up — chest tightness | 9.57% | 4.78% |
| **Overall** | Combined | **12.50%** | **6.08%** |

Clinical concept F1 score: **87.8%**

Primary error source: complex drug names (azithromycin, amoxicillin-clavulanate). Mitigated through Whisper medical vocabulary prompt injection.

---

## Compliance

| Requirement | Status | Implementation |
|---|---|---|
| GDPR Art. 15 — Subject Access | ✅ | `GET /portal/export` |
| GDPR Art. 17 — Right to Erasure | ✅ | `DELETE /admin/patient/{id}` |
| GDPR Art. 20 — Data Portability | ✅ | JSON export |
| NHS DSPT — Audit Trail | ✅ | audit_logs table |
| NHS DSPT — Role-Based Access | ✅ | JWT RBAC at every route |
| NHS DSPT — Retention Review | ✅ | 8-year review in admin panel |
| NHS DSPT — Encryption at Rest | ✅ | AES-256 Fernet |
| Doctor Approval Workflow | ✅ | PATCH /session/approve |

---

## Project Structure

```
mediscript/
├── backend/
│   ├── app.py                  # Main FastAPI application
│   ├── generate_report.js      # DOCX generation (Node.js)
│   ├── records.db              # SQLite database (gitignored)
│   ├── audio/                  # Encrypted audio files (gitignored)
│   └── .env                    # Environment variables (gitignored)
│
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main app + routing
    │   ├── api.js              # All API calls
    │   ├── Reset.jsx           # Password reset page
    │   └── components/
    │       ├── Recorder.jsx        # Audio recording
    │       ├── TranscriptCard.jsx  # 6-tab session card
    │       ├── HistoryPanel.jsx    # Records tab
    │       ├── PatientPortal.jsx   # Patient-facing portal
    │       └── AdminPanel.jsx      # Admin interface
    ├── public/
    │   └── cubeai-logo.jpeg
    ├── vercel.json             # Vercel routing config
    └── package.json
```

---

## Known Limitations

- Backend requires the clinic machine to be running (Ngrok dependency)
- SQLite not suitable for concurrent multi-doctor environments — PostgreSQL migration planned
- 12.5% WER on medical terminology without domain-specific fine-tuning
- Indian language support requires internet connectivity (Sarvam cloud API)

---

## Roadmap

- [ ] Domain-specific Whisper fine-tuning on clinical speech (target: <5% WER)
- [ ] PostgreSQL migration for multi-doctor environments
- [ ] Nginx reverse proxy replacing Ngrok for production
- [ ] NHS login / NHS Identity SSO integration
- [ ] HL7 FHIR R4 output format for EHR interoperability
- [ ] DCB0129 clinical safety case documentation
- [ ] UK cloud hosting (AWS eu-west-2 / Azure UK South) for data residency
- [ ] Formal penetration testing

---

## Team

Developed by students of PSG College of Technology, Coimbatore as part of 23Z611 — Innovation Practices, in collaboration with CubeAI Solutions Tech Pvt Ltd.

| Name | Registration |
|---|---|
| Naghulan Sivamani R V | 23Z238 |
| Shreyaa S V | 23Z264 |
| Vetriselvan V | 23Z276 |
| Vishnu S | 23Z277 |
| Venkatram S S | 23Z437 |

**Guide:** Ms. K S Pavithra, Department of Computer Science and Engineering, PSG College of Technology

---

## License

This project is developed for academic and research purposes under the Innovation Practices program at PSG College of Technology in collaboration with CubeAI Solutions Tech Pvt Ltd.

---

*MediScript — Making clinical documentation faster, safer, and smarter.*

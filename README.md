# SIH26117 Sovereign AI Workbench

An on-premise industrial intelligence workbench for confidential documents,
images, sensor data and governed agent workflows. Core AI inference runs
through local Ollama. The backend stores document metadata, extracted text,
reports and audit events in local SQLite; local Chroma embeddings are used
when available with a lexical retrieval fallback for restricted deployments.

## Run locally

### 1. Start Ollama

```bash
ollama serve
ollama pull qwen2.5vl:3b
```

### 2. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The checked-in `backend/venv` can also be used on the development machine:
`./venv/bin/uvicorn main:app --reload --port 8000`.

### 3. Start the JavaScript frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`. The demo login accepts any operator ID and
passphrase. The frontend never contains an AI API key and only calls the
configured local backend URL.

## API surface

The backend exposes `/health`, `/system/status`, `/documents/upload`,
`/documents`, `/documents/{id}/index`, `/chat`, `/vision/analyze`,
`/maintenance/analyze`, `/failure/analyze`, `/safety/analyze`,
`/analytics/analyze`, `/reports/generate`, `/agents`, `/knowledge`, and
`/audit-logs`. The original `/analyze-pdf`, `/ask-pdf`, `/analyze-image`,
`/voice-to-text`, and `/generate-flowchart` prototype routes remain available.

Air-gapped capability is an application posture, not proof of physical
network isolation. Network controls must be enforced by the deploying
organization.

## Current limitations

- DOC/DOCX files are accepted as text-compatible local inputs; production
  deployments should add a dedicated office parser for binary documents.
- Voice transcription lazily loads the local Whisper model and requires its
  model files to be present or available in the local environment.
- Report download is currently a local text export; PDF rendering can be
  added without changing the report API.

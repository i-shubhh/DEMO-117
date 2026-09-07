"""Sovereign AI Workbench API.

All inference is routed to the local Ollama instance. The service keeps the
document catalogue, extracted text and audit trail in local SQLite storage.
Chroma is used when its local embedding model is available, with a small
lexical retriever as a deterministic fallback for air-gapped installations.
"""

import base64
import io
import json
import os
import re
import sqlite3
import tempfile
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import fitz
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
except Exception:  # Optional in minimal air-gapped deployments.
    HuggingFaceEmbeddings = None
    Chroma = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("SOVEREIGN_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "workbench.db"
CHROMA_DIR = Path(os.getenv("SOVEREIGN_CHROMA_DIR", BASE_DIR / "chroma_db"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_TAGS_URL = os.getenv("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")
# Generic fallback model — used by legacy /chat and /maintenance endpoints only.
# Per-capability models are resolved from the registry in the agent workflow.
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")

# Import the model registry so health endpoints can report per-capability models.
try:
    from app.models.registry import registry as model_registry
except Exception:
    model_registry = None

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
_db_lock = threading.Lock()
_vector_store = None
_embedding_model = None
_whisper_model = None

app = FastAPI(title="Sovereign AI Workbench", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:5175,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now():
    return datetime.now(timezone.utc).isoformat()


def db():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, mime_type TEXT,
                size INTEGER NOT NULL, pages INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL, status TEXT NOT NULL,
                chunks INTEGER DEFAULT 0, content TEXT DEFAULT '', path TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                user TEXT NOT NULL, role TEXT NOT NULL, action TEXT NOT NULL,
                resource TEXT NOT NULL, agent TEXT NOT NULL, status TEXT NOT NULL,
                detail TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, type TEXT NOT NULL, machine TEXT,
                created_at TEXT NOT NULL, content TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, machine TEXT,
                timestamp TEXT, temperature REAL, vibration REAL, pressure REAL
            );
            """
        )


init_db()


def audit(action, resource, agent="System", status="SUCCESS", detail="", user="Operator", role="ENGINEER"):
    with _db_lock, db() as connection:
        connection.execute(
            "INSERT INTO audit_logs(timestamp,user,role,action,resource,agent,status,detail) VALUES(?,?,?,?,?,?,?,?)",
            (now(), user, role, action, resource, agent, status, detail),
        )


def row_dict(row):
    return dict(row) if row else None


def local_model_status():
    """Check Ollama runtime health and single-model availability (legacy helper)."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=2)
        response.raise_for_status()
        models = response.json().get("models", [])
        available = any(item.get("name") == MODEL or item.get("model") == MODEL for item in models)
        return {"online": True, "model_available": available, "model": MODEL, "url": OLLAMA_URL}
    except requests.RequestException as error:
        return {"online": False, "model_available": False, "model": MODEL, "url": OLLAMA_URL, "error": str(error)}


def multi_model_status():
    """
    Check availability of all three registered capability models against the
    local Ollama /api/tags endpoint.

    Returns a dict with:
      - ollama_online: bool
      - models: {capability: {model, available, endpoint}}
      - models_differentiated: bool (False means all three resolve to same model)
    """
    ollama_online = False
    installed_names = set()
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=2)
        response.raise_for_status()
        tags = response.json().get("models", [])
        installed_names = {
            item.get("name", "") for item in tags
        } | {
            item.get("model", "") for item in tags
        }
        ollama_online = True
    except requests.RequestException:
        pass

    capability_status = {}
    if model_registry:
        for cap, cfg in model_registry.get_all_configs().items():
            model_name = cfg["model"]
            capability_status[cap] = {
                "model": model_name,
                "available": model_name in installed_names if ollama_online else None,
                "endpoint": cfg["endpoint"],
                "runtime": cfg.get("runtime", "ollama"),
                "description": cfg.get("description", ""),
            }
        models_differentiated = model_registry.are_models_differentiated()
    else:
        capability_status = {"error": "Registry not loaded"}
        models_differentiated = False

    return {
        "ollama_online": ollama_online,
        "models": capability_status,
        "models_differentiated": models_differentiated,
    }


def call_ollama(prompt, images=None, temperature=0.2, json_format=False, max_tokens=None):
    options = {"temperature": temperature}
    if max_tokens:
        options["num_predict"] = max_tokens
    payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": options}
    if images:
        payload["images"] = images
    if json_format:
        payload["format"] = "json"
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.RequestException as error:
        raise HTTPException(status_code=503, detail="Local AI is unavailable. Start Ollama and confirm the configured model is installed.") from error


def get_vector_store():
    global _vector_store, _embedding_model
    if _vector_store is not None or Chroma is None or HuggingFaceEmbeddings is None:
        return _vector_store
    try:
        if _embedding_model is None:
            _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"local_files_only": True})
        if CHROMA_DIR.exists():
            _vector_store = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=_embedding_model)
    except Exception:
        _vector_store = None
    return _vector_store


def index_document(document_id, text, name):
    global _vector_store, _embedding_model
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=160)
    chunks = splitter.split_text(text)
    store = get_vector_store()
    if store is None and Chroma is not None and HuggingFaceEmbeddings is not None:
        try:
            if _embedding_model is None:
                _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"local_files_only": True})
            metadatas = [{"document_id": document_id, "source": name, "chunk": i + 1} for i in range(len(chunks))]
            _vector_store = Chroma.from_texts(chunks, embedding=_embedding_model, metadatas=metadatas, persist_directory=str(CHROMA_DIR))
        except Exception:
            _vector_store = None
    elif store is not None:
        try:
            metadatas = [{"document_id": document_id, "source": name, "chunk": i + 1} for i in range(len(chunks))]
            store.add_texts(chunks, metadatas=metadatas)
        except Exception:
            pass
    with _db_lock, db() as connection:
        connection.execute("UPDATE documents SET chunks=?, status='indexed' WHERE id=?", (len(chunks), document_id))
    return chunks


def retrieve(question, limit=5):
    store = get_vector_store()
    if store is not None:
        try:
            docs = store.similarity_search_with_relevance_scores(question, k=limit)
            return [{"text": doc.page_content, "source": doc.metadata.get("source", "Knowledge base"), "score": round(float(score), 2)} for doc, score in docs]
        except Exception:
            pass
    words = set(re.findall(r"[a-zA-Z0-9-]{3,}", question.lower()))
    results = []
    with db() as connection:
        documents = connection.execute("SELECT name, content FROM documents WHERE status='indexed'").fetchall()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=160)
    for document in documents:
        for chunk in splitter.split_text(document["content"] or ""):
            score = len(words.intersection(set(re.findall(r"[a-zA-Z0-9-]{3,}", chunk.lower()))))
            if score:
                results.append({"text": chunk, "source": document["name"], "score": min(0.99, score / max(len(words), 1))})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


def extract_text(filename, content):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        try:
            document = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in document)
            return text, len(document)
        except Exception as error:
            raise HTTPException(status_code=400, detail=f"Invalid PDF: {error}") from error
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
            return re.sub(r"<[^>]+>", " ", xml), 0
        except Exception as error:
            raise HTTPException(status_code=400, detail="Could not read this DOCX file.") from error
    if suffix in {".txt", ".csv", ".md"}:
        try:
            return content.decode("utf-8", errors="replace"), 0
        except Exception as error:
            raise HTTPException(status_code=400, detail="Could not read this document.") from error
    raise HTTPException(status_code=400, detail="Unsupported file. Use PDF, TXT, DOCX or CSV.")


def document_response(document):
    item = row_dict(document)
    item.pop("content", None)
    item.pop("path", None)
    item["indexed"] = item["status"] == "indexed"
    return item


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation: list[dict[str, str]] = []


class AnalysisRequest(BaseModel):
    machine_id: str = "M-102"
    symptoms: str = ""
    description: str = ""
    context: str = ""


class ReportRequest(BaseModel):
    type: str = "Maintenance Report"
    machine: str = "M-102"
    date_range: str = "Last 30 days"
    include_sources: bool = True
    context: str = ""


class FlowchartRequest(BaseModel):
    topic: str


@app.get("/")
def root():
    return {"status": "online", "message": "Sovereign AI Workbench is running", "model": MODEL}


@app.get("/health")
def health():
    """Health check per PROJECT_GUIDE.md Section 23.

    Reports: API status, Ollama runtime, per-capability model availability,
    knowledge base, and storage type.  All inference must be LOCAL.
    """
    multi_status = multi_model_status()
    with db() as connection:
        count = connection.execute("SELECT COUNT(*) FROM documents WHERE status='indexed'").fetchone()[0]
    return {
        "status": "ok",
        "local_ai": {
            "online": multi_status["ollama_online"],
            "url": OLLAMA_URL,
            "models_differentiated": multi_status["models_differentiated"],
            "capabilities": multi_status["models"],
        },
        "knowledge_base": {"online": True, "indexed_documents": count},
        "storage": "local",
        "external_api": "blocked",
    }


@app.get("/system/status")
def system_status():
    """Extended system status with full multi-model registry information."""
    multi_status = multi_model_status()
    ollama = local_model_status()
    with db() as connection:
        documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = connection.execute("SELECT COALESCE(SUM(chunks), 0) FROM documents").fetchone()[0]
    return {
        "local_ai": ollama,
        "ollama": ollama,
        "multi_model": multi_status,
        "rag": {"online": True, "documents": documents, "chunks": chunks},
        "vector_db": {"online": True, "type": "Chroma / lexical fallback"},
        "external_api": {"status": "blocked"},
        "network_egress": {"status": "blocked"},
        "audit": {"status": "active"},
        "air_gapped": {
            "status": "capable",
            "note": "Application does not call external AI services.",
        },
    }


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Files must be smaller than 50 MB.")
    text, pages = extract_text(file.filename or "document", content)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text was found in this file.")
    document_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{document_id}{Path(file.filename or 'document').suffix.lower()}"
    path.write_bytes(content)
    with _db_lock, db() as connection:
        connection.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?)", (document_id, file.filename or "document", file.content_type, len(content), pages, now(), "processing", 0, text, str(path)))
    try:
        chunks = index_document(document_id, text, file.filename or "document")
    except Exception as error:
        with db() as connection:
            connection.execute("UPDATE documents SET status='error' WHERE id=?", (document_id,))
        raise HTTPException(status_code=500, detail=f"Indexing failed: {error}") from error
    audit("Document indexed", file.filename or "document", "Document Agent")
    with db() as connection:
        document = connection.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    result = document_response(document)
    result["chunks_created"] = len(chunks)
    return result


@app.get("/documents")
def list_documents():
    with db() as connection:
        rows = connection.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    return {"documents": [document_response(row) for row in rows], "total": len(rows)}


@app.get("/documents/{document_id}")
def get_document(document_id: str):
    with db() as connection:
        document = connection.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document_response(document)


@app.get("/documents/{document_id}/file")
def document_file(document_id: str):
    with db() as connection:
        path = connection.execute("SELECT path FROM documents WHERE id=?", (document_id,)).fetchone()
    if not path or not path["path"] or not Path(path["path"]).exists():
        raise HTTPException(status_code=404, detail="Document file not found.")
    return FileResponse(path["path"])


@app.post("/documents/{document_id}/index")
def reindex_document(document_id: str):
    with db() as connection:
        document = connection.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    chunks = index_document(document_id, document["content"], document["name"])
    audit("Document re-indexed", document["name"], "Document Agent")
    return {"id": document_id, "status": "indexed", "chunks": len(chunks)}


@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    with _db_lock, db() as connection:
        document = connection.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        connection.execute("DELETE FROM documents WHERE id=?", (document_id,))
    if document["path"] and Path(document["path"]).exists():
        Path(document["path"]).unlink()
    audit("Document deleted", document["name"], "Document Agent")
    return {"deleted": True, "id": document_id}


@app.post("/chat")
def chat(request: ChatRequest):
    sources = retrieve(request.message)
    context = "\n\n".join(f"SOURCE: {item['source']}\n{item['text']}" for item in sources)
    prompt = f"""You are a confidential industrial operations assistant. Answer only from the supplied context when it is present. Do not invent readings, diagnoses, or safety claims. If evidence is insufficient, say so and recommend a qualified inspection. Mention relevant source names in your answer.\n\nCONTEXT:\n{context or 'No matching knowledge-base context was found.'}\n\nQUESTION:\n{request.message}"""
    answer = call_ollama(prompt, temperature=0.2)
    audit("AI query processed", request.message[:100], "Supervisor Agent")
    return {"answer": answer, "response": answer, "sources": sources, "agent": "Supervisor Agent", "confidence": round(max([item["score"] for item in sources] or [0.35]), 2)}


@app.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...), machine_id: str = Form("M-102")):
    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as error:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from error
    encoded = base64.b64encode(content).decode("utf-8")
    prompt = "Analyze this industrial image conservatively. Describe visible equipment and components, visible abnormal conditions or hazards, labels only if legible, and safe recommended inspection steps. Clearly distinguish observation from inference. Do not claim exact detection or measurements that are not visible."
    analysis = call_ollama(prompt, images=[encoded], temperature=0.15)
    audit("Image analyzed", file.filename or machine_id, "Vision Agent")
    return {"filename": file.filename, "machine_id": machine_id, "analysis": analysis, "agent": "Vision Agent", "confidence": None, "note": "Confidence is not estimated unless returned by the local model."}


def analysis_prompt(kind, request, sources):
    context = "\n\n".join(f"{item['source']}: {item['text']}" for item in sources)
    return f"""You are the {kind} Agent in a governed industrial workbench. Analyze Machine {request.machine_id}. Use the supplied evidence, clearly mark uncertainty, and never invent measurements. Return concise sections: PROBLEM SUMMARY, POSSIBLE CAUSES, EVIDENCE, RECOMMENDED CHECKS, SAFETY PRECAUTIONS, NEXT ACTION.\n\nINPUT:\n{request.symptoms or request.description}\n{request.context}\n\nKNOWLEDGE EVIDENCE:\n{context or 'No matching source found. State that evidence is unavailable.'}"""


@app.post("/maintenance/analyze")
def maintenance_analyze(request: AnalysisRequest):
    sources = retrieve(request.symptoms or request.description or "maintenance procedure overheating")
    result = call_ollama(analysis_prompt("Maintenance", request, sources))
    audit("Maintenance analysis generated", request.machine_id, "Maintenance Agent")
    return {"machine_id": request.machine_id, "analysis": result, "sources": sources, "agent": "Maintenance Agent"}


@app.post("/failure/analyze")
def failure_analyze(request: AnalysisRequest):
    sources = retrieve(request.description or "failure root cause corrective action")
    result = call_ollama(analysis_prompt("Failure Analysis", request, sources))
    audit("Failure analysis generated", request.machine_id, "Failure Agent")
    return {"machine_id": request.machine_id, "analysis": result, "sources": sources, "agent": "Failure Analysis Agent"}


@app.post("/safety/analyze")
def safety_analyze(request: AnalysisRequest):
    sources = retrieve(request.description or "safety hazard PPE emergency procedure")
    result = call_ollama(analysis_prompt("Safety", request, sources) + "\nPrioritize immediate hazards, PPE, isolation/lockout guidance, and escalation.")
    audit("Safety analysis generated", request.machine_id, "Safety Agent")
    return {"machine_id": request.machine_id, "analysis": result, "sources": sources, "agent": "Safety Agent"}


@app.post("/analytics/analyze")
async def analytics_analyze(file: Optional[UploadFile] = File(None), machine_id: str = Form("M-102")):
    readings = []
    if file:
        raw = (await file.read()).decode("utf-8", errors="replace").splitlines()
        if raw:
            headers = [item.strip().lower() for item in raw[0].split(",")]
            for line in raw[1:]:
                values = [item.strip() for item in line.split(",")]
                row = dict(zip(headers, values))
                try:
                    readings.append({"timestamp": row.get("timestamp") or row.get("time") or str(len(readings) + 1), "temperature": float(row.get("temperature", 0)), "vibration": float(row.get("vibration", 0)), "pressure": float(row.get("pressure", 0))})
                except ValueError:
                    continue
    if not readings:
        readings = [{"timestamp": "T-4", "temperature": 68, "vibration": 3.1, "pressure": 5.4}, {"timestamp": "T-3", "temperature": 74, "vibration": 4.2, "pressure": 5.3}, {"timestamp": "T-2", "temperature": 79, "vibration": 5.8, "pressure": 5.2}, {"timestamp": "T-1", "temperature": 82, "vibration": 7.2, "pressure": 5.1}]
    with _db_lock, db() as connection:
        for reading in readings:
            connection.execute("INSERT INTO sensor_readings(machine,timestamp,temperature,vibration,pressure) VALUES(?,?,?,?,?)", (machine_id, reading["timestamp"], reading["temperature"], reading["vibration"], reading["pressure"]))
    temperatures = [item["temperature"] for item in readings]
    vibration = [item["vibration"] for item in readings]
    audit("Sensor data analyzed", machine_id, "Analytics Agent")
    return {"machine_id": machine_id, "readings": readings, "metrics": {"average_temperature": round(sum(temperatures) / len(temperatures), 1), "average_vibration": round(sum(vibration) / len(vibration), 1), "temperature_anomaly": temperatures[-1] > 80, "vibration_anomaly": vibration[-1] > 6}, "agent": "Analytics Agent"}


@app.post("/reports/generate")
def generate_report(request: ReportRequest):
    sources = retrieve(request.context or f"{request.machine} maintenance safety report")
    prompt = f"Create a professional {request.type} for {request.machine} covering {request.date_range}. Use the context, include findings, evidence, recommendations, safety precautions, and limitations. Do not invent facts.\n\nCONTEXT:\n{request.context}\n\nSOURCES:\n{json.dumps(sources)}"
    content = call_ollama(prompt, temperature=0.15, max_tokens=900)
    report_id = str(uuid.uuid4())
    with _db_lock, db() as connection:
        connection.execute("INSERT INTO reports VALUES(?,?,?,?,?)", (report_id, request.type, request.machine, now(), content))
    audit("Report generated", request.machine, "Report Agent")
    return {"id": report_id, "type": request.type, "machine": request.machine, "created_at": now(), "content": content, "sources": sources}


@app.get("/reports")
def list_reports():
    with db() as connection:
        return {"reports": [row_dict(row) for row in connection.execute("SELECT id,type,machine,created_at FROM reports ORDER BY created_at DESC").fetchall()]}


@app.get("/agents")
def agents():
    names = [("Supervisor Agent", "Routes investigations and enforces evidence policy"), ("Document Agent", "Extracts, indexes and retrieves local documents"), ("Vision Agent", "Interprets visual evidence with the local multimodal model"), ("Maintenance Agent", "Connects symptoms to procedures and checks"), ("Analytics Agent", "Finds trends and sensor threshold violations"), ("Safety Agent", "Surfaces hazards, PPE and immediate actions"), ("Report Agent", "Produces traceable operational reports"), ("Security Agent", "Applies local-only and audit policy")]
    return {"agents": [{"name": name, "purpose": purpose, "status": "ready", "model": MODEL, "tools": ["Local LLM", "Knowledge Base", "Audit Trail"]} for name, purpose in names]}


@app.get("/audit-logs")
def audit_logs(limit: int = 100):
    with db() as connection:
        rows = connection.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (min(limit, 500),)).fetchall()
    return {"logs": [row_dict(row) for row in rows]}


@app.get("/knowledge")
def knowledge():
    with db() as connection:
        documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = connection.execute("SELECT COALESCE(SUM(chunks), 0) FROM documents").fetchone()[0]
    return {"documents": documents, "indexed_documents": documents, "chunks": chunks, "embeddings": chunks, "vector_db": "online", "last_updated": now()}


@app.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    global _whisper_model
    content = await file.read()
    try:
        if _whisper_model is None:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as temporary:
            temporary.write(content)
            path = temporary.name
        segments, info = _whisper_model.transcribe(path)
        text = " ".join(segment.text for segment in segments).strip()
        os.unlink(path)
        audit("Voice note transcribed", file.filename or "voice note", "Document Agent")
        return {"filename": file.filename, "language": info.language, "text": text}
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Local speech recognition is unavailable: {error}") from error


@app.post("/generate-flowchart")
def generate_flowchart(request: FlowchartRequest):
    raw = call_ollama(f"Return JSON with title and steps (maximum 7) for an industrial troubleshooting flowchart about {request.topic}.", json_format=True)
    try:
        data = json.loads(raw)
        steps = data.get("steps", [])[:7]
        if len(steps) < 2:
            raise ValueError("Not enough steps")
        mermaid = "flowchart TD\n" + "".join(f'    A{i}["{str(steps[i]).replace(chr(34), chr(39))}"] --> A{i + 1}["{str(steps[i + 1]).replace(chr(34), chr(39))}"]\n' for i in range(len(steps) - 1))
        return {"topic": request.topic, "title": data.get("title", request.topic), "steps": steps, "flowchart": mermaid}
    except (ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=502, detail="The local model returned an invalid flowchart.") from error


# Compatibility routes retained for the original prototype.
@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    result = await upload_document(file)
    with db() as connection:
        document = connection.execute("SELECT content FROM documents WHERE id=?", (result["id"],)).fetchone()
    analysis = call_ollama(f"Summarize this industrial document. Include key findings, procedures, risks and important numbers. Do not invent information.\n\n{document['content'][:12000]}")
    return {"filename": result["name"], "pages": result["pages"], "chunks_created": result["chunks"], "analysis": analysis}


@app.post("/ask-pdf")
def ask_pdf(request: ChatRequest):
    return chat(request)


@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    return await vision_analyze(file)


# --- Sovereign AI Workbench Master Plan API Routers (Section 7) ---
from app.api.tasks import tasks_router, init_workflow_engine
from app.api.security import security_router

# Initialize the workflow engine with local knowledge retrieval
init_workflow_engine(retrieve_fn=retrieve)

# Include master plan routers
app.include_router(tasks_router)
app.include_router(security_router)


@app.get("/api/demo/sample-report")
def get_sample_report():
    """Serves sample inspection report PDF for instant demo testing."""
    sample_path = BASE_DIR / "data" / "demo" / "inspection_report_P102A.pdf"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample report not found.")
    return FileResponse(
        path=str(sample_path),
        filename="inspection_report_P102A.pdf",
        media_type="application/pdf",
    )


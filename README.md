# 🏭 Sovereign AI Workbench

### Problem Statement ID: **PS-26117** — SIH 2026

> **An AI-powered assistant for industrial plant operations that runs 100% offline — no data ever leaves your computer.**

---

## 📌 What Is This Project?

```mermaid
graph LR
    PROBLEM["🏭 Industrial Plant<br/>Challenges"]
    
    PROBLEM --> P1["📄 100s of inspection<br/>reports to read"]
    PROBLEM --> P2["🔧 Strict safety rules<br/>(SOPs) to follow"]
    PROBLEM --> P3["📊 Sensor data with<br/>hidden anomalies"]
    PROBLEM --> P4["🖼️ Equipment photos<br/>needing expert eyes"]
    PROBLEM --> P5["📝 Reports that take<br/>hours to write"]

    SOLUTION["🤖 Sovereign AI<br/>Workbench"]

    P1 --> SOLUTION
    P2 --> SOLUTION
    P3 --> SOLUTION
    P4 --> SOLUTION
    P5 --> SOLUTION

    SOLUTION --> R1["✅ AI reads & analyzes<br/>documents in seconds"]
    SOLUTION --> R2["✅ Auto-checks against<br/>safety procedures"]
    SOLUTION --> R3["✅ Detects anomalies<br/>& threshold violations"]
    SOLUTION --> R4["✅ Analyzes images<br/>for damage & hazards"]
    SOLUTION --> R5["✅ Generates reports<br/>automatically"]

    style PROBLEM fill:#da3633,stroke:#f85149,color:#fff
    style SOLUTION fill:#238636,stroke:#2ea043,color:#fff
    style P1 fill:#161b22,stroke:#f78166,color:#fff
    style P2 fill:#161b22,stroke:#f78166,color:#fff
    style P3 fill:#161b22,stroke:#f78166,color:#fff
    style P4 fill:#161b22,stroke:#f78166,color:#fff
    style P5 fill:#161b22,stroke:#f78166,color:#fff
    style R1 fill:#0d1117,stroke:#3fb950,color:#fff
    style R2 fill:#0d1117,stroke:#3fb950,color:#fff
    style R3 fill:#0d1117,stroke:#3fb950,color:#fff
    style R4 fill:#0d1117,stroke:#3fb950,color:#fff
    style R5 fill:#0d1117,stroke:#3fb950,color:#fff
```

> ### 🔒 The #1 Rule: Everything stays on YOUR computer. Zero data goes to the internet.

---

## 🎯 Features At A Glance

| # | Feature | Input | Output | Agent |
|---|---------|-------|--------|-------|
| 1 | 📄 **Document Analysis** | PDF inspection report | Official approval note (.docx) | Document Agent |
| 2 | 💬 **Knowledge Q&A** | Plain English question | Answer with cited sources | Knowledge Assistant |
| 3 | 👁️ **Vision Analysis** | Photo of equipment | Damage/hazard description | Vision Agent |
| 4 | 🔧 **Maintenance Help** | Symptom description | Procedures + safety checks | Maintenance Agent |
| 5 | ⚠️ **Safety Analysis** | Situation description | PPE + emergency procedures | Safety Agent |
| 6 | 📊 **Sensor Analytics** | CSV sensor data | Anomaly detection + metrics | Analytics Agent |
| 7 | 📝 **Report Generator** | Machine + date range | Professional report | Report Agent |
| 8 | 🎤 **Voice Notes** | Audio recording | Transcribed text | Whisper Model |
| 9 | 💻 **Code Execution** | Engineering task | Python script + results | Coding Agent |
| 10 | 🛡️ **Security Monitor** | — (always active) | Live zero-egress dashboard | Security Agent |

---

## 🧠 AI Models — All Running Locally

```mermaid
graph TB
    OLLAMA["🖥️ Ollama Server<br/>localhost:11434<br/><i>Runs on YOUR computer</i>"]

    OLLAMA --> VIS["👁️ VISION<br/>qwen2.5vl:3b"]
    OLLAMA --> REASON["🤔 REASONING<br/>qwen2.5vl:3b"]
    OLLAMA --> CODE["💻 CODING<br/>qwen2.5vl:3b"]

    HF["📦 Cached Locally<br/><i>Downloaded once, no internet needed after</i>"]

    HF --> EMBED["📚 EMBEDDINGS<br/>all-MiniLM-L6-v2"]
    HF --> SPEECH["🎤 SPEECH<br/>faster-whisper base"]

    VIS --> VIS_USE["Reads images, scanned PDFs,<br/>gauges, labels, equipment photos"]
    REASON --> REASON_USE["Answers questions, analyzes reports,<br/>checks SOP compliance"]
    CODE --> CODE_USE["Writes & runs Python scripts<br/>for engineering calculations"]
    EMBED --> EMBED_USE["Converts documents into vectors<br/>for meaning-based search"]
    SPEECH --> SPEECH_USE["Converts spoken audio<br/>into written text"]

    style OLLAMA fill:#1a1a2e,stroke:#e94560,color:#fff
    style HF fill:#1a1a2e,stroke:#8957e5,color:#fff
    style VIS fill:#1f6feb,stroke:#388bfd,color:#fff
    style REASON fill:#e3b341,stroke:#d29922,color:#000
    style CODE fill:#f78166,stroke:#ea6045,color:#fff
    style EMBED fill:#8957e5,stroke:#a371f7,color:#fff
    style SPEECH fill:#3fb950,stroke:#56d364,color:#000
```

| Model | Name | Task | Runtime | Size |
|-------|------|------|---------|------|
| 👁️ Vision | `qwen2.5vl:3b` | Image + PDF understanding | Ollama (localhost) | ~2 GB |
| 🤔 Reasoning | `qwen2.5vl:3b` | Q&A, SOP checks, analysis | Ollama (localhost) | ~2 GB |
| 💻 Coding | `qwen2.5vl:3b` | Python code generation | Ollama (localhost) | ~2 GB |
| 📚 Embedding | `all-MiniLM-L6-v2` | Document similarity search | HuggingFace (cached) | ~80 MB |
| 🎤 Speech | `faster-whisper (base)` | Voice → Text | CPU (local) | ~150 MB |

---

## 🏗️ System Architecture

```mermaid
graph TB
    USER["👤 User"]

    subgraph BROWSER["🖥️ Frontend — localhost:5173"]
        UI["React + Vite Dashboard"]
    end

    subgraph SERVER["⚙️ Backend — localhost:8000"]
        API["FastAPI Server"]
        ROUTER["🔀 Smart Router"]
        
        subgraph AGENTS["🤖 8 AI Agents"]
            A1["📄 Document"]
            A2["💬 Knowledge"]
            A3["👁️ Vision"]
            A4["🔧 Maintenance"]
            A5["⚠️ Safety"]
            A6["📊 Analytics"]
            A7["📝 Report"]
            A8["💻 Coding"]
        end
        
        subgraph DATA["💾 Local Storage"]
            DB["SQLite DB"]
            VECTOR["ChromaDB"]
            FS["File System"]
        end
    end

    subgraph AI["🧠 AI — localhost:11434"]
        OLLAMA["Ollama"]
        MODEL["qwen2.5vl:3b"]
        EMB["MiniLM-L6-v2"]
    end

    subgraph SEC["🛡️ Security"]
        MON["Network Monitor"]
        AUDIT["Audit Logger"]
        SAND["Code Sandbox"]
    end

    USER --> UI
    UI -->|HTTP| API
    API --> ROUTER
    ROUTER --> AGENTS
    AGENTS -->|Inference| OLLAMA
    OLLAMA --> MODEL
    AGENTS -->|Search| VECTOR
    VECTOR --> EMB
    AGENTS -->|Store| DB
    AGENTS -->|Files| FS
    MON -->|Verify| SERVER
    AUDIT --> DB
    A8 -->|Isolated| SAND

    style BROWSER fill:#0d1117,stroke:#58a6ff,color:#fff
    style SERVER fill:#161b22,stroke:#f78166,color:#fff
    style AI fill:#1a1a2e,stroke:#e94560,color:#fff
    style SEC fill:#0d1117,stroke:#3fb950,color:#fff
```

---

## 📄 Flow 1: Document Agent (Hero Demo)

> Upload a scanned inspection report → Get a professional approval note

```mermaid
graph TD
    S1["📤 STEP 1<br/>Upload PDF Report"]
    S2["📖 STEP 2<br/>Extract Text<br/><i>PyMuPDF reads every page</i>"]
    S3["🔍 STEP 3<br/>Search Knowledge Base<br/><i>Model: all-MiniLM-L6-v2</i>"]
    S4["🧠 STEP 4<br/>AI Reasoning<br/><i>Model: qwen2.5vl:3b</i><br/>Compare vs SOP rules"]
    S5["📝 STEP 5<br/>Generate .docx<br/><i>Approval Note with findings</i>"]
    S6["🛡️ STEP 6<br/>Security Verify<br/><i>Confirm zero data leaked</i>"]
    S7["✅ STEP 7<br/>Download<br/><i>Official Approval Note</i>"]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7

    style S1 fill:#238636,stroke:#2ea043,color:#fff
    style S2 fill:#1f6feb,stroke:#388bfd,color:#fff
    style S3 fill:#8957e5,stroke:#a371f7,color:#fff
    style S4 fill:#e3b341,stroke:#d29922,color:#000
    style S5 fill:#f78166,stroke:#ea6045,color:#fff
    style S6 fill:#3fb950,stroke:#56d364,color:#000
    style S7 fill:#238636,stroke:#2ea043,color:#fff
```

| Step | What Happens | Model/Tool Used |
|------|-------------|-----------------|
| 1 | User uploads a PDF inspection report | — |
| 2 | System reads every page and extracts all text | PyMuPDF |
| 3 | Finds matching SOPs & safety procedures by *meaning* | all-MiniLM-L6-v2 + ChromaDB |
| 4 | AI compares inspection findings vs SOP rules | qwen2.5vl:3b (Ollama) |
| 5 | Generates a professional `.docx` Approval Note | python-docx |
| 6 | Verifies no data left the local machine | Network Monitor (lsof) |
| 7 | User downloads the finished document | — |

---

## 💬 Flow 2: Knowledge Assistant

> Ask a question → Get an answer grounded in your documents (or a clear refusal)

```mermaid
graph TD
    Q["❓ User asks:<br/>'What is the vibration limit<br/>for pump P-102A?'"]
    
    SEARCH["🔍 Search uploaded documents<br/><i>Model: all-MiniLM-L6-v2</i>"]
    
    CHECK{"📋 Matching<br/>sources found?"}
    
    YES_PATH["🧠 AI generates answer<br/>citing exact sources<br/><i>Model: qwen2.5vl:3b</i>"]
    
    NO_PATH["🚫 AI REFUSES to answer<br/>'No supporting local source found'"]
    
    ANSWER["✅ Answer + Source Citations"]
    SAFE["🛡️ Prevents dangerous<br/>made-up answers"]

    Q --> SEARCH --> CHECK
    CHECK -->|"Yes ✅"| YES_PATH --> ANSWER
    CHECK -->|"No ❌"| NO_PATH --> SAFE

    style Q fill:#1f6feb,stroke:#388bfd,color:#fff
    style SEARCH fill:#8957e5,stroke:#a371f7,color:#fff
    style CHECK fill:#e3b341,stroke:#d29922,color:#000
    style YES_PATH fill:#238636,stroke:#2ea043,color:#fff
    style NO_PATH fill:#da3633,stroke:#f85149,color:#fff
    style ANSWER fill:#238636,stroke:#2ea043,color:#fff
    style SAFE fill:#da3633,stroke:#f85149,color:#fff
```

> ⚠️ **Anti-Hallucination Policy**: If the AI can't find the answer in your documents, it **refuses to guess**. Critical for safety-sensitive environments.

---

## 👁️ Flow 3: Vision Analysis

```mermaid
graph LR
    IMG["📸 Upload Equipment Photo"] --> ENCODE["🔄 Encode Image<br/><i>Base64</i>"]
    ENCODE --> AI["🧠 Vision Model<br/><i>qwen2.5vl:3b</i>"]
    AI --> OUT["📋 Analysis Output"]
    
    OUT --> D1["🔍 Visible components"]
    OUT --> D2["⚠️ Abnormal conditions"]
    OUT --> D3["🏷️ Legible labels"]
    OUT --> D4["📝 Recommended inspections"]

    style IMG fill:#1f6feb,stroke:#388bfd,color:#fff
    style AI fill:#e3b341,stroke:#d29922,color:#000
    style OUT fill:#238636,stroke:#2ea043,color:#fff
```

---

## 💻 Flow 4: Coding Agent (Sandboxed)

```mermaid
graph TD
    TASK["📋 Task: 'Calculate pump<br/>degradation index'"]
    GEN["🧠 AI generates Python code<br/><i>Model: qwen2.5vl:3b</i>"]
    SANDBOX["🔒 Execute in Sandbox<br/><b>--network none</b><br/><i>Zero internet access</i>"]
    RESULT["📊 Output: Results printed<br/>to screen + code shown"]

    TASK --> GEN --> SANDBOX --> RESULT

    style TASK fill:#1f6feb,stroke:#388bfd,color:#fff
    style GEN fill:#e3b341,stroke:#d29922,color:#000
    style SANDBOX fill:#da3633,stroke:#f85149,color:#fff
    style RESULT fill:#238636,stroke:#2ea043,color:#fff
```

| Property | Value |
|----------|-------|
| **Network Access** | ❌ Completely blocked (`--network none`) |
| **Can code leak data?** | ❌ Impossible — no socket access |
| **Language** | Python |
| **Output** | Printed to stdout, shown to user |

---

## 🔧 Flow 5: Maintenance / Safety / Failure Agents

```mermaid
graph LR
    INPUT["📝 Describe Symptoms<br/><i>'Machine vibrating,<br/>temperature rising'</i>"]
    
    INPUT --> ROUTE{"🔀 Router"}
    
    ROUTE -->|"Mechanical issue"| MAINT["🔧 Maintenance Agent"]
    ROUTE -->|"Safety concern"| SAFE["⚠️ Safety Agent"]
    ROUTE -->|"Equipment failure"| FAIL["💥 Failure Agent"]
    
    MAINT --> M_OUT["Procedures + Checks"]
    SAFE --> S_OUT["PPE + Emergency Steps"]
    FAIL --> F_OUT["Root Cause + Fixes"]

    M_OUT --> RAG["🔍 All answers backed<br/>by local documents"]
    S_OUT --> RAG
    F_OUT --> RAG

    style INPUT fill:#1f6feb,stroke:#388bfd,color:#fff
    style ROUTE fill:#e3b341,stroke:#d29922,color:#000
    style MAINT fill:#f78166,stroke:#ea6045,color:#fff
    style SAFE fill:#da3633,stroke:#f85149,color:#fff
    style FAIL fill:#8957e5,stroke:#a371f7,color:#fff
    style RAG fill:#238636,stroke:#2ea043,color:#fff
```

---

## 📊 Flow 6: Sensor Analytics

```mermaid
graph TD
    CSV["📊 Upload Sensor CSV<br/><i>temperature, vibration, pressure</i>"]
    PARSE["🔄 Parse Readings"]
    STORE["💾 Store in SQLite"]
    CALC["🧮 Calculate Metrics"]
    
    CALC --> AVG["📈 Average Temperature"]
    CALC --> VIB["📈 Average Vibration"]
    CALC --> T_ANOM["🔴 Temperature Anomaly?<br/><i>above 80°C = alert</i>"]
    CALC --> V_ANOM["🔴 Vibration Anomaly?<br/><i>above 6 mm/s = alert</i>"]

    CSV --> PARSE --> STORE --> CALC

    style CSV fill:#1f6feb,stroke:#388bfd,color:#fff
    style CALC fill:#e3b341,stroke:#d29922,color:#000
    style T_ANOM fill:#da3633,stroke:#f85149,color:#fff
    style V_ANOM fill:#da3633,stroke:#f85149,color:#fff
```

---

## 🛡️ Security Architecture

```mermaid
graph TB
    subgraph LOCAL["🔒 YOUR COMPUTER — Security Boundary"]
        APP["⚙️ App Server"]
        OLLAMA["🧠 Ollama AI"]
        DB["💾 Database"]
        FILES["📁 Files"]
        SANDBOX["🔒 Code Sandbox"]
    end

    INTERNET["🌐 Internet"]
    
    APP -.->|"❌ BLOCKED"| INTERNET
    OLLAMA -.->|"❌ BLOCKED"| INTERNET
    DB -.->|"❌ BLOCKED"| INTERNET
    SANDBOX -.->|"❌ BLOCKED"| INTERNET
    
    APP <-->|"✅ 127.0.0.1"| OLLAMA
    APP <-->|"✅ local file"| DB
    APP <-->|"✅ local file"| FILES

    MONITOR["🛡️ Network Monitor<br/><i>Scans connections via lsof</i><br/><i>Flags non-localhost traffic</i>"]
    MONITOR -->|"Continuously verifies"| LOCAL

    style LOCAL fill:#0d1117,stroke:#3fb950,color:#fff
    style INTERNET fill:#da3633,stroke:#f85149,color:#fff
    style MONITOR fill:#238636,stroke:#2ea043,color:#fff
```

| Security Feature | Status | How |
|-----------------|--------|-----|
| AI runs locally | ✅ | Ollama on `localhost:11434` |
| Data stored locally | ✅ | SQLite + local files |
| No cloud API calls | ✅ | No OpenAI/Google/Azure imports |
| Network monitoring | ✅ | `lsof` scans active connections |
| Code sandbox isolation | ✅ | `--network none` blocks all sockets |
| Full audit trail | ✅ | Every action logged with timestamp |
| External telemetry | ❌ Blocked | No analytics sent anywhere |

---

## 🤖 Agent Routing — How Tasks Get Assigned

```mermaid
graph TD
    INPUT["📥 New Task Arrives"]
    
    ROUTER["🔀 Smart Router<br/><i>Analyzes input type + keywords</i>"]
    
    INPUT --> ROUTER
    
    ROUTER -->|"Has PDF/image<br/>or visual keywords"| VIS_MODEL["👁️ Vision Model<br/><b>qwen2.5vl:3b</b>"]
    ROUTER -->|"Has code/calculate/<br/>script keywords"| CODE_MODEL["💻 Coding Model<br/><b>qwen2.5vl:3b</b>"]
    ROUTER -->|"General question"| REASON_MODEL["🤔 Reasoning Model<br/><b>qwen2.5vl:3b</b>"]

    VIS_MODEL --> DOC_FLOW["📄 Document Agent Flow"]
    CODE_MODEL --> CODE_FLOW["💻 Coding Agent Flow"]
    REASON_MODEL --> KNOW_FLOW["💬 Knowledge Flow"]

    style INPUT fill:#1f6feb,stroke:#388bfd,color:#fff
    style ROUTER fill:#e3b341,stroke:#d29922,color:#000
    style VIS_MODEL fill:#8957e5,stroke:#a371f7,color:#fff
    style CODE_MODEL fill:#f78166,stroke:#ea6045,color:#fff
    style REASON_MODEL fill:#3fb950,stroke:#56d364,color:#000
```

| Input Signal | Detected By | Routes To |
|-------------|------------|-----------|
| PDF, PNG, JPG file attached | File extension check | 👁️ Vision → Document Agent |
| Words: *inspection, scanned, diagram, gauge* | Regex pattern match | 👁️ Vision → Document Agent |
| Words: *code, script, python, calculate, compute* | Regex pattern match | 💻 Coding Agent |
| Everything else | Default fallback | 🤔 Knowledge Assistant |

---

## 📂 Project Structure

```mermaid
graph TD
    ROOT["📁 DEMO-117/"]
    
    ROOT --> BE["📁 backend/"]
    ROOT --> FE["📁 frontend/"]
    ROOT --> README["📄 README.md"]

    BE --> MAIN["📄 main.py<br/><i>API server — 559 lines</i>"]
    BE --> REQ["📄 requirements.txt"]
    BE --> ENV["📄 .env.example"]
    BE --> APP["📁 app/"]

    APP --> AGENT["📁 agent/<br/><i>graph, router, prompts, state</i>"]
    APP --> APID["📁 api/<br/><i>tasks, security endpoints</i>"]
    APP --> MODELS["📁 models/<br/><i>registry, local_client</i>"]
    APP --> SBOX["📁 sandbox/<br/><i>docker_runner</i>"]
    APP --> SECU["📁 security/<br/><i>network_check</i>"]
    APP --> SCHEMA["📁 schemas/<br/><i>tasks, events</i>"]
    APP --> TOOLS["📁 tools/<br/><i>document_tools</i>"]

    FE --> SRC["📁 src/"]
    SRC --> APPJSX["📄 App.jsx<br/><i>Main dashboard</i>"]
    SRC --> SWJSX["📄 SovereignWorkbench.jsx<br/><i>Advanced workbench</i>"]
    SRC --> CSS["📄 styles.css"]
    SRC --> LIB["📁 lib/api.js"]

    style ROOT fill:#0d1117,stroke:#58a6ff,color:#fff
    style BE fill:#161b22,stroke:#f78166,color:#fff
    style FE fill:#161b22,stroke:#58a6ff,color:#fff
    style APP fill:#1a1a2e,stroke:#8957e5,color:#fff
```

---

## 🧩 Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| 🖥️ **Frontend** | React + Vite | Dashboard UI |
| ⚙️ **Backend** | Python FastAPI | API server |
| 💾 **Database** | SQLite | Documents, reports, audit logs |
| 🔍 **Vector DB** | ChromaDB | Semantic document search |
| 📄 **PDF Reader** | PyMuPDF | Extract text from PDFs |
| 📝 **Doc Writer** | python-docx | Generate .docx approval notes |
| 🧠 **AI Runtime** | Ollama | Local model serving |
| 👁️ **Main Model** | Qwen 2.5 VL (3B) | Vision + Language |
| 📚 **Embeddings** | all-MiniLM-L6-v2 | Document search |
| 🎤 **Speech** | faster-whisper | Voice-to-text |

---

## 🚀 Setup — 4 Steps

### Step 1: Clone

```bash
git clone https://github.com/i-shubhh/DEMO-117.git
cd DEMO-117
```

### Step 2: Start Local AI

```bash
# Install Ollama → https://ollama.com
ollama serve
ollama pull qwen2.5vl:3b       # ~2GB download, only once
```

### Step 3: Start Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Start Frontend

```bash
cd frontend                     # new terminal
npm install
npm run dev
```

> 🎉 Open **http://localhost:5173** in your browser!

---

## ⚙️ Configuration

| Variable | Default | What It Does |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Where the AI model runs |
| `OLLAMA_MODEL` | `qwen2.5vl:3b` | Which AI model to use |
| `SOVEREIGN_DATA_DIR` | `./data` | Where files are stored |
| `WHISPER_MODEL` | `base` | Speech-to-text model size |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend URLs |

---

## 🔌 API Endpoints

### Core APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status check |
| `/health` | GET | Full system health |
| `/system/status` | GET | AI model + storage status |
| `/agents` | GET | List all 8 AI agents |
| `/audit-logs` | GET | Complete audit trail |

### Document & Knowledge APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/upload` | POST | Upload & index a document |
| `/documents` | GET | List all documents |
| `/documents/{id}` | GET | Get document details |
| `/documents/{id}/file` | GET | Download original file |
| `/chat` | POST | Ask the Knowledge Assistant |
| `/knowledge` | GET | Knowledge base stats |

### Analysis APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vision/analyze` | POST | Analyze equipment photo |
| `/maintenance/analyze` | POST | Maintenance recommendations |
| `/safety/analyze` | POST | Safety & PPE analysis |
| `/failure/analyze` | POST | Root cause analysis |
| `/analytics/analyze` | POST | Sensor anomaly detection |

### Report & Advanced APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/generate` | POST | Generate professional report |
| `/reports` | GET | List all reports |
| `/voice-to-text` | POST | Speech → text |
| `/generate-flowchart` | POST | AI troubleshooting flowchart |
| `/api/tasks` | POST | Start agentic task workflow |
| `/api/tasks/{id}` | GET | Check task progress |
| `/api/tasks/{id}/result` | GET | Get results + artifacts |
| `/api/tasks/{id}/events` | GET | Real-time execution trace |
| `/api/security/status` | GET | Zero-egress verification |

---

## 🔄 Complete Data Flow — End to End

```mermaid
sequenceDiagram
    actor User
    participant Frontend as 🖥️ Frontend
    participant API as ⚙️ FastAPI
    participant Router as 🔀 Router
    participant Agent as 🤖 Agent
    participant Ollama as 🧠 Ollama
    participant ChromaDB as 🔍 ChromaDB
    participant SQLite as 💾 SQLite
    participant Security as 🛡️ Security

    User->>Frontend: Upload PDF + Click "Analyze"
    Frontend->>API: POST /api/tasks
    API->>Router: Classify task type
    Router->>Agent: Route to Document Agent
    Agent->>Agent: Extract text (PyMuPDF)
    Agent->>ChromaDB: Search for matching SOPs
    ChromaDB-->>Agent: Return relevant sources
    Agent->>Ollama: Send prompt + context
    Ollama-->>Agent: Return analysis
    Agent->>Agent: Generate .docx Approval Note
    Agent->>Security: Verify zero-egress
    Security-->>Agent: ✅ VERIFIED
    Agent->>SQLite: Log audit trail
    Agent-->>API: Return result + artifacts
    API-->>Frontend: Task completed
    Frontend-->>User: Show results + download link
```

---

## 📜 License

Built for **Smart India Hackathon 2026** — Problem Statement PS-26117.

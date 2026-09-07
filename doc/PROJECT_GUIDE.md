---
title: |
  MRPL SOVEREIGN AI WORKBENCH\
  **Project Guide --- PS 26117**
---

*Single source of truth for implementation, testing, security, and demo
requirements.*

# 1. PROJECT IDENTITY

Problem Statement: SIH26117

Organization: Mangalore Refinery and Petrochemicals Limited (MRPL)

Category: Software

Theme: Smart Automation

Project:

Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal
LLMs for Confidential Industrial Work.

# 2. CORE OBJECTIVE

Build a self-hosted AI workbench that runs entirely on organizational
hardware for confidential industrial knowledge work.

The system must provide:

-   local open-weight AI models

-   multiple model support

-   automatic model selection

-   agentic multi-step execution

-   local tool execution

-   local document/knowledge retrieval

-   multimodal document understanding

-   real file deliverables

-   sandboxed code execution

-   provable absence of external network calls

Core principle:

CONFIDENTIAL DATA MUST REMAIN INSIDE THE ORGANIZATION\'S INFRASTRUCTURE.

# 3. NON-NEGOTIABLE SOVEREIGNTY RULE

The application must operate without external network access.

Allowed:

-   localhost / 127.0.0.1

-   local FastAPI services

-   local Ollama or vLLM

-   local ChromaDB/Qdrant

-   local filesystem

-   local Docker

-   local model files

-   local embeddings

-   local OCR

-   local document generation

Forbidden:

-   OpenAI, Anthropic, Gemini or other cloud inference APIs

-   Azure/AWS/Google AI services

-   cloud OCR

-   cloud embeddings

-   hosted vector databases

-   external search APIs

-   external inference APIs

-   telemetry that transmits project data

-   cloud fallback for model inference

A URL such as http://localhost:11434 is LOCAL and is allowed.

The project must have NO EXTERNAL NETWORK DEPENDENCY.

# 4. SOURCE OF TRUTH

Priority order:

1\. Official MRPL PS 26117 requirements

2\. This PROJECT_GUIDE.md

3\. Existing working architecture

4\. Implementation decisions

If implementation conflicts with this guide, change the implementation.

Do not weaken requirements merely to make development easier.

# 5. REQUIREMENTS VS IMPLEMENTATION CHOICES

MRPL-level requirements include:

-   self-hosted/on-premise deployment

-   air-gapped operation

-   multiple open-weight models

-   automatic model selection

-   adding models without redesign

-   agentic multi-step workflows

-   local file operations

-   sandboxed code execution

-   spreadsheet work

-   internal document search

-   scanned PDFs

-   handwritten notes

-   engineering drawings

-   photographs

-   local OCR/vision

-   local organizational knowledge

-   real deliverables

-   Word/Excel/PowerPoint outputs

-   working code

-   calculations with steps

-   visible proof of zero external calls

Implementation choices may include:

-   Ollama

-   vLLM

-   Qwen/Qwen2.5-VL

-   LangGraph

-   ChromaDB

-   Docker

-   PyMuPDF

-   python-docx

-   openpyxl

-   python-pptx

-   FastAPI

-   React

-   Vite

These implementation choices are NOT themselves MRPL requirements.

Do not describe them as mandated by MRPL.

# 6. HIGH-LEVEL ARCHITECTURE

USER

\|

v

FRONTEND

\|

v

FASTAPI BACKEND

\|

v

AGENT / ORCHESTRATOR

\|

+\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

\| \|

v v

MODEL ROUTER TOOL REGISTRY

\| \|

\| +\-- File Tools

\| +\-- Document Tools

\| +\-- Spreadsheet Tools

\| +\-- Code Sandbox

\| +\-- Calculation Tools

\|

+\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

\| \| \|

v v v

REASONING CODING VISION/OCR

MODEL MODEL MODEL

\| \| \|

+\-\-\-\-\-\-\-\-\-\-\-\-\-\--+\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

\|

v

LOCAL RAG

\|

v

LOCAL KNOWLEDGE

\|

v

DELIVERABLES

Everything must remain inside the local machine/server boundary.

# 7. MODEL ARCHITECTURE

Do NOT design the backend around one model.

Conceptual structure:

Model Registry

+\-- Reasoning Model

+\-- Coding Model

+\-- Vision/OCR Model

+\-- Optional fallback model

The registry should store:

-   model identifier

-   capability

-   runtime

-   context size if relevant

-   vision capability

-   coding capability

-   reasoning capability

-   hardware requirements

-   fallback priority

Adding a model should not require rewriting the agent system.

# 8. MODEL ROUTING

Routing must be real backend behavior, not a UI label.

Examples:

\"Summarize this inspection report.\"

-\> reasoning/document model

\"Write Python code to calculate this.\"

-\> coding model

\"Analyze this scanned inspection page.\"

-\> vision model

The final demo should visibly show:

TASK RECEIVED -\> CLASSIFICATION -\> MODEL SELECTED -\> LOCAL INFERENCE

# 9. CURRENT MODEL IMPLEMENTATION

Current prototype vision model:

qwen2.5vl:3b

Runtime:

Ollama

Local endpoint:

http://localhost:11434

This is an implementation choice, not a fixed MRPL requirement.

The architecture must allow the model to be upgraded later without
rewriting the document pipeline.

Prioritize reliable local execution over a large model that cannot run
during the demo.

# 10. AGENTIC ARCHITECTURE

The system must behave as an agent, not merely a chatbot.

Target loop:

TASK RECEIVED

-\> UNDERSTAND TASK

-\> CREATE PLAN

-\> SELECT MODEL

-\> SELECT TOOLS

-\> EXECUTE STEP

-\> OBSERVE RESULT

-\> DECIDE NEXT STEP

-\> COMPLETE TASK

-\> GENERATE DELIVERABLE

The agent must support multi-step execution.

# 11. HERO AGENT WORKFLOW

Primary demonstration:

SCANNED INSPECTION REPORT

-\> PDF PROCESSING

-\> TEXT / IMAGE DETECTION

-\> VISION MODEL

-\> FINDINGS EXTRACTION

-\> LOCAL KNOWLEDGE SEARCH

-\> SOP RETRIEVAL

-\> REASONING MODEL

-\> APPROVAL NOTE

-\> DOCX OUTPUT

The complete flow must run locally.

# 12. MULTIMODAL PROCESSING

Required targets:

-   scanned PDFs

-   handwritten notes

-   engineering drawings

-   photographs

-   image-based documents

Text PDF:

PDF -\> PyMuPDF get_text() -\> native text

Scanned PDF:

PDF page -\> get_text()

-\> insufficient text

-\> render page

-\> image bytes

-\> local vision model

-\> extracted findings

Prefer in-memory image processing.

Do not create unnecessary temporary image files.

Handwriting:

Support local vision/OCR processing, but do not claim production-grade
accuracy unless tested.

P&IDs / engineering drawings:

Support image/document understanding where demonstrated.

Do not overclaim precise P&ID interpretation.

If uncertain, report uncertainty rather than fabricate findings.

# 13. LOCAL OCR / VISION

Forbidden:

PDF -\> external OCR API

Allowed:

PDF -\> local renderer -\> local vision model

or:

PDF -\> local OCR -\> local reasoning model

All visual processing must remain local.

# 14. LOCAL KNOWLEDGE / RAG

Target:

DOCUMENTS

-\> INGESTION

-\> CHUNKING

-\> LOCAL EMBEDDINGS

-\> LOCAL VECTOR DATABASE

-\> RETRIEVAL

-\> AGENT / REASONING MODEL

Possible knowledge:

-   SOPs

-   manuals

-   public sample documents

-   sample inspection reports

-   public/open reference material

-   synthetic industrial documents

For the prototype, use public/open or synthetic data.

Do not commit confidential MRPL data.

RAG must:

-   ingest local documents

-   create local embeddings

-   store vectors locally

-   retrieve relevant chunks

-   return source information

-   pass grounded context to the agent

Never pretend retrieval occurred when it did not.

# 15. TOOL SYSTEM

Minimum local tool categories:

File:

-   read

-   write

-   inspect

-   artifact management

Document:

-   DOCX generation

-   formatting

-   approval-note generation

Spreadsheet:

-   XLSX creation

-   calculations

-   structured data manipulation

Calculation:

-   mathematical calculation

-   step-by-step output

-   result verification

Code:

-   code generation

-   code execution

-   sandbox verification

Knowledge:

-   local document search

-   RAG retrieval

# 16. CODE EXECUTION SANDBOX

Generated code must never execute directly on the host.

Required:

AGENT

-\> GENERATED CODE

-\> DOCKER SANDBOX

\- network disabled

\- resource limits

\- restricted filesystem

-\> EXECUTION RESULT

-\> AGENT VERIFICATION

Do not expose the host filesystem unnecessarily.

# 17. REAL DELIVERABLES

The system must generate real files:

-   DOCX

-   XLSX

-   PPTX

-   source code

-   calculation reports

A frontend preview is not equivalent to successful file generation.

Primary hero deliverable:

Inspection Report -\> Findings -\> SOP Grounding -\> Approval_Note.docx

The generated artifact must be downloadable from the frontend.

# 18. FRONTEND RULES

The frontend is a real workbench, not a fake demo.

Mock data may be used during early UI development.

However:

MOCK DATA MUST NEVER MASK A REAL BACKEND FAILURE.

Bad:

Backend fails -\> fake successful task is shown.

Correct:

Backend fails -\> actual error is shown -\> failed dependency is
identified.

Before final demo, real backend data must replace mock task data.

# 19. OBSERVABILITY / EVENTS

The UI should show actual agent progress:

-   TASK RECEIVED

-   MODEL SELECTED

-   DOCUMENT PROCESSED

-   VISION EXTRACTION

-   KNOWLEDGE RETRIEVED

-   TOOL STARTED

-   TOOL COMPLETED

-   OUTPUT GENERATED

-   TASK COMPLETED

Events must correspond to real backend events.

Never fabricate success events.

# 20. SECURITY / SOVEREIGNTY

LOCAL:

-   localhost

-   127.0.0.1

-   local filesystem

-   local Docker

-   local model runtime

-   local vector database

EXTERNAL:

-   public internet

-   cloud APIs

-   remote inference

-   hosted databases

-   external OCR

-   external embeddings

External connections are prohibited.

# 21. NETWORK PROOF

This is mandatory.

The final demonstration must provide real evidence that no external
calls occur.

Example:

WORKFLOW RUNNING

-\> NETWORK MONITOR

-\> NO EXTERNAL TRAFFIC

Possible methods:

-   connection inspection

-   packet capture

-   Wireshark

-   local egress monitoring

-   OS-level network monitoring

Do not merely display \"AIR-GAPPED: YES\".

The proof must be independently observable.

# 22. SOVEREIGNTY TEST

1\. Start network monitoring.

2\. Start AI workbench.

3\. Upload a sample document.

4\. Run the complete agent workflow.

5\. Generate the output.

6\. Inspect network activity.

Expected:

NO EXTERNAL AI/API/NETWORK CALLS.

Document the result.

# 23. HEALTH CHECK

Health must distinguish:

-   API health

-   model runtime

-   model availability

-   knowledge base

-   sandbox

-   security/network

Example:

API -\> OK

OLLAMA -\> OK

MODEL -\> AVAILABLE

CHROMA -\> OK

SANDBOX -\> OK

NETWORK -\> NO EXTERNAL EGRESS

Do not report healthy unless actually checked.

# 24. API DESIGN

Expected categories:

-   /api/health

-   /api/tasks

-   /api/tasks/{id}

-   /api/tasks/{id}/events

-   /api/tasks/{id}/result

-   /api/knowledge/\...

-   /api/security/\...

Exact endpoints may differ if justified by architecture.

Frontend calls must map to real backend functionality.

No fake success responses.

# 25. FAILURE HANDLING

The system must fail honestly.

Never hide:

-   model connection failure

-   missing model

-   missing dependency

-   RAG failure

-   sandbox failure

-   document generation failure

-   network verification failure

Bad:

Model unavailable -\> fake AI response

Correct:

Model unavailable -\> task FAILED -\> clear diagnostic error.

# 26. DEMONSTRATION REQUIREMENTS

DEMO 1 --- MODEL AUTO-SELECTION

Show at least two task types and their actual different local model
routes.

DEMO 2 --- HERO AGENTIC WORKFLOW

Scanned inspection report -\> Vision -\> Findings -\> Local RAG -\>
Reasoning -\> Approval Note -\> DOCX.

DEMO 3 --- CODING SANDBOX

Request -\> Coding model -\> Code -\> Docker sandbox -\> Execution -\>
Verification -\> Result.

DEMO 4 --- MULTIMODAL INPUT

Use a real scanned/image document and prove that the vision model
actually receives and processes it.

DEMO 5 --- SOVEREIGNTY

Run the workflow while showing network monitoring and zero external
traffic.

# 27. DEMO DATA

Use:

-   public sample inspection reports

-   public sample PDFs

-   public sample P&IDs where appropriate

-   synthetic industrial documents

-   public manuals/SOP-like material

Do NOT use:

-   confidential MRPL files

-   private company documents

-   personal data

-   credentials

-   API keys

-   proprietary documents

# 28. SECURITY OF REPOSITORY

Never commit:

-   model weights

-   .env files

-   API keys

-   credentials

-   private documents

-   private datasets

-   generated sensitive files

-   temporary model caches

Model files must remain local and be excluded from Git.

# 29. DEPENDENCY RULES

Before adding any package ask:

1\. Is it necessary?

2\. Can it run locally?

3\. Does it introduce external network requirements?

4\. Does it send telemetry?

5\. Does it conflict with air-gapped deployment?

6\. Can the project work without it?

Avoid unnecessary dependencies and cloud SDKs.

# 30. CURRENT IMPLEMENTATION STATUS

Working / substantially implemented:

-   FastAPI backend foundation

-   frontend foundation

-   local model client

-   model registry foundation

-   agent workflow foundation

-   local RAG / ChromaDB foundation

-   DOCX generation

-   PDF native text extraction

-   scanned-page detection

-   scanned-page rendering

-   local vision payload generation

-   local Ollama integration

Implemented but requiring live verification:

-   qwen2.5vl:3b vision inference

-   complete scanned-PDF -\> vision workflow

-   complete agent workflow

-   local model routing

-   sandbox execution

-   full frontend/backend integration

-   zero external network calls

Must be completed / verified:

-   real multi-model routing

-   coding model integration

-   reasoning model integration

-   coding sandbox end-to-end test

-   multimodal demo

-   local RAG end-to-end demo

-   XLSX generation

-   PPTX generation where required for demo

-   step-by-step calculation workflow

-   network egress proof

-   final integrated hero workflow

Update this section as development progresses.

# 31. CURRENT VISION PIPELINE

PDF

\|

v

PyMuPDF

\|

v

page.get_text()

\|

+\-- sufficient text \--\> Native Text

\|

+\-- insufficient text \--\> get_pixmap()

\|

v

Base64 image

\|

v

LocalModelClient

\|

v

qwen2.5vl:3b

\|

v

extracted findings

The vision model must remain local.

# 32. IMPORTANT LIMITATION

Code-path verification is not the same as live verification.

Example:

\"Code sends image to Ollama\"

does NOT prove:

\"Vision inference works end-to-end.\"

A feature is DONE only after:

1\. implementation

2\. local execution

3\. test

4\. output verification

# 33. TESTING STRATEGY

Unit tests:

-   parsers

-   routers

-   model clients

-   tools

-   document generators

-   RAG functions

-   security checks

Integration tests:

frontend -\> backend -\> agent -\> model -\> tool -\> output

Model tests:

-   model available

-   correct model selected

-   inference succeeds

-   vision input works

-   coding model works

Agent tests:

-   plan created

-   model selected

-   tools selected

-   tools executed

-   results observed

-   final output generated

Sandbox tests:

-   code executes

-   network disabled

-   resource limits enforced

-   unwanted filesystem access prevented

Sovereignty tests:

-   no external network calls

-   no cloud model calls

-   no external OCR

-   no external embeddings

-   no hidden fallback

# 34. DEFINITION OF DONE

A feature is DONE only when:

CODE EXISTS

AND

DEPENDENCIES EXIST

AND

LOCAL EXECUTION WORKS

AND

TESTS PASS

AND

OUTPUT IS VERIFIED

AND

NO SOVEREIGNTY RULE IS VIOLATED

\"File exists\" does not mean \"feature complete.\"

# 35. AI CODING AGENT RULES

Any AI coding agent working on this repository MUST:

1\. Read docs/PROJECT_GUIDE.md completely before making changes.

2\. Understand the existing architecture first.

3\. Search the repository before creating duplicate functionality.

4\. Reuse existing abstractions where possible.

5\. Avoid unnecessary rewrites.

6\. Avoid cloud dependencies.

7\. Avoid hardcoded fake outputs.

8\. Avoid silent fallbacks.

9\. Keep model configuration separate from application logic.

10\. Keep local/offline execution as the default.

11\. Test every meaningful change.

12\. Report failures honestly.

13\. Never claim PASS when a live dependency was not tested.

14\. Never download or use external services without explicit approval.

15\. Never modify unrelated files.

16\. Preserve working functionality.

Before modifying code:

1\. inspect implementation

2\. identify relevant files

3\. explain planned changes

4\. modify only necessary files

5\. run appropriate tests

6\. report actual results

# 36. WHAT NOT TO BUILD

Do not prioritize:

-   cloud deployment

-   cloud databases

-   cloud AI APIs

-   cloud OCR

-   cloud embeddings

-   Kubernetes

-   unnecessary microservices

-   distributed infrastructure

-   custom LLM training

-   unnecessary custom OCR models

-   excessive UI animations

-   large enterprise abstractions

-   unsupported production claims

Focus on a working, demonstrable prototype satisfying PS 26117.

# 37. PRIORITY ORDER

P0 --- MUST WORK

1\. Local model runtime

2\. Model routing

3\. Agent loop

4\. Scanned document processing

5\. Local RAG

6\. DOCX generation

7\. Coding sandbox

8\. Zero external network proof

P1 --- REQUIRED / IMPORTANT

9\. Multimodal image processing

10\. Spreadsheet functionality

11\. Calculation workflow

12\. Real frontend/backend integration

13\. Task/event visibility

P2 --- DEMO ENHANCEMENT

14\. PPTX generation

15\. Additional visual workflows

16\. Better UI observability

17\. Additional model options

# 38. HERO DEMO TARGET

USER UPLOADS SCANNED INSPECTION REPORT

\|

v

TASK CLASSIFICATION

\|

v

MODEL ROUTING

\|

v

VISION MODEL

\|

v

FINDINGS EXTRACTION

\|

v

LOCAL KNOWLEDGE

RETRIEVAL

\|

v

REASONING MODEL

\|

v

APPROVAL NOTE DRAFT

\|

v

DOCX GENERATION

\|

v

DOWNLOADABLE FILE

The UI should simultaneously show:

-   model selected

-   agent steps

-   tool execution

-   RAG sources

-   output file

Then show:

NETWORK MONITOR -\> ZERO EXTERNAL CALLS

# 39. JUDGE-FACING CLAIMS

Only claim capabilities that can be demonstrated.

Valid examples:

-   \"The system runs local open-weight models through a local
    runtime.\"

-   \"The router selects models based on task type.\"

-   \"The inspection workflow uses a local vision model for scanned
    pages.\"

-   \"The knowledge base is stored and searched locally.\"

-   \"The approval note is generated locally.\"

-   \"Network monitoring shows no external calls during the workflow.\"

Avoid unsupported claims such as:

-   \"The system understands every P&ID perfectly.\"

-   \"The system is production-ready.\"

-   \"The system supports every industrial workflow.\"

-   \"The model is equivalent to GPT-5.\"

-   \"The system is secure because we have a security page.\"

Claims must be backed by actual demonstrations.

# 40. FINAL ACCEPTANCE CHECKLIST

SOVEREIGNTY

-   [ ] No cloud AI API

-   [ ] No external OCR

-   [ ] No external embeddings

-   [ ] No hosted vector database

-   [ ] No hidden network dependency

-   [ ] Local models run successfully

-   [ ] Network proof completed

MODELS

-   [ ] Multiple local models available

-   [ ] Model registry works

-   [ ] Router works

-   [ ] At least two task types route differently

-   [ ] Vision model works

-   [ ] Coding model works

-   [ ] Reasoning model works

-   [ ] Fallback model available

AGENT

-   [ ] Agent creates a plan

-   [ ] Agent calls tools

-   [ ] Agent observes results

-   [ ] Agent performs multiple steps

-   [ ] Agent generates final deliverable

MULTIMODAL

-   [ ] Text PDF works

-   [ ] Scanned PDF works

-   [ ] Image input works

-   [ ] Vision inference works

-   [ ] Handwritten capability tested or honestly marked limited

-   [ ] Engineering drawing capability tested or honestly marked limited

RAG

-   [ ] Documents can be ingested

-   [ ] Local embeddings work

-   [ ] Vector database works

-   [ ] Retrieval works

-   [ ] Retrieved context reaches the model

-   [ ] Sources/citations visible where appropriate

TOOLS

-   [ ] File read/write

-   [ ] DOCX generation

-   [ ] XLSX generation

-   [ ] Calculation tool

-   [ ] Docker sandbox

-   [ ] Network-disabled sandbox

FRONTEND

-   [ ] Real backend connected

-   [ ] No silent fake fallback

-   [ ] Task status visible

-   [ ] Agent events visible

-   [ ] Model selection visible

-   [ ] Artifacts downloadable

-   [ ] Security status visible

DEMO

-   [ ] Model auto-selection demo

-   [ ] Scanned inspection workflow

-   [ ] RAG grounding

-   [ ] DOCX output

-   [ ] Coding sandbox

-   [ ] Multimodal input

-   [ ] Zero-network proof

# 41. FINAL PRINCIPLE

This project is NOT:

\"A local chatbot.\"

It is:

A sovereign, on-premise, multi-model, multimodal, agentic AI workbench
that can execute useful industrial knowledge-work workflows without
sending confidential data outside the organization.

Every technical decision should support:

SOVEREIGNTY

\+

MODEL CAPABILITY

\+

AGENTIC EXECUTION

\+

MULTIMODAL UNDERSTANDING

\+

LOCAL KNOWLEDGE GROUNDING

\+

REAL DELIVERABLES

If a feature does not improve these core capabilities, it should not
take priority over the core implementation.

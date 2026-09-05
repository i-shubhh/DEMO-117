"""Ingest knowledge files from data/knowledge into SQLite and Chroma vector store per Section 8 & 10."""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from main import db, _db_lock, index_document, now


def ingest_file(file_path: Path):
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    name = file_path.name
    content = file_path.read_text(encoding="utf-8", errors="replace")
    doc_id = str(uuid.uuid4())

    with _db_lock, db() as conn:
        # Check if already indexed by name
        existing = conn.execute("SELECT id FROM documents WHERE name=?", (name,)).fetchone()
        if existing:
            doc_id = existing["id"]
            conn.execute("UPDATE documents SET content=?, status='processing' WHERE id=?", (content, doc_id))
        else:
            conn.execute(
                "INSERT INTO documents(id, name, mime_type, size, pages, uploaded_at, status, chunks, content, path) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (doc_id, name, "text/plain", len(content.encode("utf-8")), 1, now(), "processing", 0, content, str(file_path)),
            )

    chunks = index_document(doc_id, content, name)
    print(f"Successfully indexed '{name}' (ID: {doc_id}) with {len(chunks)} chunks.")


if __name__ == "__main__":
    knowledge_dir = backend_dir / "data" / "knowledge"
    if knowledge_dir.exists():
        for item in knowledge_dir.glob("*.txt"):
            ingest_file(item)

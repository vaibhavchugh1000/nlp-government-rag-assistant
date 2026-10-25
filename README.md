# Government Document RAG Assistant

A multilingual Retrieval-Augmented Generation (RAG) system for intelligent retrieval and question answering over government documents in PDF, DOCX, and TXT formats.

The system lets citizens ask questions about government documents in their own language — even when the source document is written in a different language — and returns a grounded answer with source/page traceability.

## Key Idea

> **Document Language ≠ Query Language** — and that's fine.

A citizen can ask a question in Hindi about a document written in English (or vice versa). A multilingual embedding model places both document chunks and queries in a shared semantic vector space, so retrieval works across languages. The detected query language is then passed to the LLM so the final answer is generated in the same language the citizen asked in.

**Example:**

| | |
|---|---|
| Document | `unemployment_pension.pdf` (English) |
| Citizen question | "बेरोजगारी पेंशन के लिए पात्रता क्या है?" (Hindi) |
| Retrieved chunk | English eligibility clause |
| Generated answer | Hindi |

## Features

- **Multi-format ingestion** — PDF, Microsoft Word (`.docx`), and plain text (`.txt`)
- **OCR for scanned PDFs** — uses native PDF text extraction where available and Tesseract OCR for pages with no or very little selectable text
- **Multilingual embeddings** — documents and queries in different languages (English, Hindi, Tamil, Bengali, etc.) share one semantic vector space
- **Cross-lingual semantic retrieval** — relevant content is retrieved regardless of the language it was written in
- **Query language detection** — the citizen's question language is detected and used to control the response language
- **Source traceability** — answers are linked back to document name, page number (where available), and optional official source URL
- **Role-based demo GUI** — a single HTML page with Admin and Citizen views
- **Lightweight backend** — a minimal Flask layer connects the GUI to the Python RAG pipeline; the focus stays on NLP/retrieval, not web engineering

## Architecture

```
Government Documents
        ↓
Document Loading (PDF / DOCX / TXT)
        ↓
PDF: Native Text Extraction → OCR fallback for scanned pages
        ↓
Text Extraction
        ↓
Cleaning
        ↓
Chunking
        ↓
Multilingual Embeddings
        ↓
ChromaDB
        ↓
Semantic Retrieval
        ↓
Context Construction
        ↓
LLM
        ↓
Answer in Citizen's Language
        ↓
Source / Page Information
```

The system is split into two independent pipelines that meet at ChromaDB:

- **Admin pipeline** — loads, cleans, chunks, embeds, and stores documents. It ends once data is in ChromaDB; it never performs retrieval or answer generation.
- **Citizen pipeline** — detects query language, embeds the question, searches ChromaDB, builds context, and calls the LLM to produce a grounded, traceable answer.

## Roles

### Admin
Builds and maintains the knowledge base:
1. Select a government document (PDF / DOCX / TXT)
2. Extract text (preserving page numbers where applicable)
3. Clean the text
4. Split into chunks
5. Generate multilingual embeddings
6. Store chunks + embeddings + metadata in ChromaDB

### Citizen
Queries the knowledge base:
1. Enter a natural-language question in any supported language
2. Language is detected automatically
3. Question is embedded with the same multilingual model used for documents
4. Top-K relevant chunks are retrieved from ChromaDB
5. Context is assembled and sent to the LLM along with the detected response language
6. Answer is generated in the citizen's own language, with source document/page shown

## Directory Structure

```
Government-RAG/
│
├── app.py                  # Flask entry point, coordinates GUI ↔ RAG pipeline
│
├── pdf_loader.py            # PDF text extraction + OCR fallback
├── ocr_processor.py         # Tesseract OCR helper
├── docx_loader.py           # Word document text extraction
├── txt_loader.py            # Plain text loading
├── cleaner.py                # Text cleaning
├── chunker.py                # Splits text into chunks
├── language_detector.py     # Detects citizen query language
├── embedding_model.py       # Multilingual embeddings (docs + queries)
├── vector_store.py          # ChromaDB storage interface
├── retriever.py              # Semantic search over ChromaDB
├── prompt_builder.py        # Combines question + context + response language
├── llm_engine.py              # Sends prompt to LLM, returns answer
│
├── gui/
│   └── app.html              # Single-page GUI: login, admin, citizen views
│
├── data/
│   └── documents/            # Original source documents (retained for traceability)
│       ├── unemployment_pension.pdf
│       ├── pm_kisan.docx
│       └── senior_citizen_scheme.txt
│
├── vector_db/
│   └── chroma/                # Persistent ChromaDB storage
│
├── .env
└── requirements.txt
```

## Data Model

**Document (after loading), format-independent:**
```json
{
    "document_id": "PENSION_001",
    "document_name": "unemployment_pension.pdf",
    "document_type": "pdf",
    "language": "en",
    "content": [ ... ]
}
```

**Chunk stored in ChromaDB:**
```json
{
    "text": "The applicant must satisfy the income criteria...",
    "metadata": {
        "document_id": "PENSION_001",
        "document_name": "unemployment_pension.pdf",
        "document_type": "pdf",
        "page_number": 12,
        "chunk_id": "PENSION_001_P12_C03",
        "language": "en",
        "source_url": "..."
    }
}
```

Downstream modules never need to know whether a chunk originally came from a PDF, DOCX, or TXT file — all three loaders converge on the same representation before entering the common cleaning/chunking/embedding pipeline.

## API Endpoints (Flask)

| Endpoint | Role | Purpose |
|---|---|---|
| `POST /login` | Both | Authenticate as Admin or Citizen |
| `POST /admin/process` | Admin | Process and store a document |
| `POST /citizen/query` | Citizen | Ask a question and get an answer |

**Example Admin request:**
```json
{ "document_path": "data/documents/pm_kisan.docx" }
```

**Example Citizen request:**
```json
{ "question": "बेरोजगारी पेंशन के लिए पात्रता क्या है?" }
```

**Example Citizen response:**
```json
{
    "answer": "बेरोजगारी पेंशन के लिए...",
    "language": "hi",
    "sources": [
        { "document": "unemployment_pension.pdf", "page": 12 }
    ]
}
```

## Authentication (Demo Only)

The demo GUI uses simple hardcoded credentials for illustration purposes only — **not** intended for production:

- `admin / admin`
- `citizen / citizen`

## Three Language Concepts

It's important not to conflate these:

| Concept | Meaning | Example |
|---|---|---|
| Document Language | Language the source document is written in | English |
| Query Language | Language used by the citizen | Hindi |
| Response Language | Language the LLM generates the answer in | = Query Language (v1) |

## Version 1 Scope

**Included:**
- Admin and Citizen login, single HTML GUI, minimal Flask backend
- PDF, DOCX, TXT document support
- Manual document repository, text extraction, cleaning, chunking
- Multilingual embeddings and cross-language retrieval
- Query language detection and ChromaDB-backed semantic search
- Context construction, LLM generation, answer in query language
- Document/page metadata and source traceability

**Excluded (candidates for future work):**
- Citizen document uploads
- Voice input/output (ASR/TTS)
- Advanced Bhashini integration
- LangChain / LangGraph
- Long-term conversation memory
- Production-grade authentication and deployment

## Future Extensions

- **OCR** — support scanned documents by feeding OCR output into the existing text pipeline
- **Bhashini integration** — for Indian-language speech recognition, synthesis, and translation
- **Voice** — ASR → RAG → TTS loop
- **Conversation memory** — incorporate relevant prior turns into retrieval
- **Advanced retrieval** — query rewriting, multiple retrieval strategies, reranking
- **Advanced traceability** — link answers down to exact page/section and official government URL

## Recommended Implementation Order

1. Document loading (`pdf_loader.py`, `ocr_processor.py`, `docx_loader.py`, `txt_loader.py`)
2. Text processing (`cleaner.py`, `chunker.py`)
3. Multilingual embedding (`embedding_model.py`) — verify cross-language similarity
4. Vector database (`vector_store.py`) — Admin pipeline complete at this point
5. Retrieval (`retriever.py`)
6. Language detection (`language_detector.py`)
7. Prompt construction (`prompt_builder.py`)
8. LLM integration (`llm_engine.py`) — verify answers follow the requested language
9. UI (`gui/app.html`)
10. Flask integration (`app.py`) — wire GUI to the RAG pipeline last, so UI work doesn't interfere with core NLP development

## Design Philosophy

The GUI and Flask layers are intentionally kept minimal. This is not a web-development project — the core focus is:

- Multilingual NLP
- Semantic embeddings
- Vector retrieval
- Retrieval-Augmented Generation
- Grounded LLM generation
- Source traceability


## OCR Setup (Windows)

The Python packages are installed from `requirements.txt`, but `pytesseract` also
requires the separate Tesseract OCR application.

1. Install the Tesseract OCR Windows application.
2. Ensure `tesseract.exe` is on your system `PATH` (or configure
   `pytesseract.pytesseract.tesseract_cmd` in `pdf_loader.py` with its installed path).
3. Open a new PowerShell terminal and verify that `tesseract --version` works.
4. Install project dependencies with `pip install -r requirements.txt`.
5. Run the app normally with `python app.py`.

The loader checks every PDF page. Pages with enough selectable text use normal
PDF extraction; pages with little or no selectable text are rendered and passed
through OCR. OCR is local and does not require a Gemini API key. English OCR is
the default; additional Tesseract language data is needed for other document
languages.

If a document produces no usable text, processing now returns an error instead
of silently reporting success with zero chunks.

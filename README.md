<div align="center">

# 🎓 Quizora

**Autonomous, Source-Grounded Academic Quiz Generation System powered by Multi-Stage RAG.**

Turn any textbook chapter, syllabus, or lecture PDF into university-grade multiple-choice examinations with strict difficulty calibration, grounded semantic verification, and one-click PDF exports.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render&logoColor=black)](https://quizora-api-z38n.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Vector%20DB-Supabase%20pgvector-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![LLM](https://img.shields.io/badge/LLM-Groq%20(GPT--OSS--120B)-F55036?logo=groq&logoColor=white)](https://groq.com/)
[![Embeddings](https://img.shields.io/badge/Embeddings-Jina%20AI%20v3-000000)](https://jina.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

### 🔗 [Live Web App & API on Render](https://quizora-api-z38n.onrender.com/)

</div>

---

## ✨ Overview

Studying and drafting exam-grade assessments manually is time-consuming and prone to coverage bias. **Quizora** parses academic materials and executes a deterministic **7-stage RAG generation and self-correction pipeline** to produce authentic assessment papers.

Every generated question is backed by source chunk retrieval, pedagogical sanity checks, and semantic grounding verifications.

---

## ⚡ Key Highlights

- **🧠 Multi-Stage RAG Architecture:** Eliminates hallucination through sequential planning, topic coverage analysis, focused chunk retrieval, generation, structural filtering, and semantic grounding.
- **☁️ Cloud & Free-Tier Optimized:** Integrated with **Jina AI (`jina-embeddings-v3`)** API for embeddings (0 MB local RAM footprint) and **Groq** high-speed inference, keeping the backend featherlight within Render's 512 MB memory constraint.
- **🐘 Enterprise Vector Storage:** Managed PostgreSQL with **`pgvector`** (Supabase connection pooler with IPv4 compatibility).
- **🎚️ Calibrated Difficulty Controls:** Specify exact Easy, Medium, and Hard distributions with real-time feedback.
- **📄 Dual PDF Exports:** Instantly compile and download:
  - **Question Paper (PDF):** Clean exam format with student metadata fields, instructions, and formatted questions.
  - **Answer Key & Explanations (PDF):** Solution sheet with correct options, detailed rationales, and source page citations.
- **🌐 Unified Monorepo:** Seamless modern dark-mode web interface served directly via FastAPI static mounts.

---

## 🏛️ Pipeline Architecture

```mermaid
flowchart TD
    PDF["📄 Upload Study PDF"] --> S1["1. Ingestion (Chunking & pgvector Indexing)"]
    S1 --> S2["2. Document Analyzer (Curriculum & Multi-Topic Discovery)"]
    S2 --> S3["3. Question Planner (Difficulty & Topic Distribution)"]
    S3 --> S4["4. Retrieval Engine (Targeted Chunk Extraction)"]
    S4 --> S5["5. Generation Engine (Groq LLM Batch MCQ Generation)"]
    S5 --> S6["6. Structural Check (Pattern & Form Validation)"]
    S6 --> S7["7. Semantic Correction (Grounding & Non-contradiction Verification)"]
    S7 --> OUT["📦 Final Quiz & Dual PDF Compilation"]
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend & REST API** | [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), Pydantic v2 |
| **Frontend** | Vanilla ES6+ JavaScript, CSS3, Modern Dark Mode UI (Served via FastAPI `StaticFiles`) |
| **LLM Inference** | [Groq](https://groq.com/) (`openai/gpt-oss-120b`) |
| **Vector Embeddings** | [Jina AI](https://jina.ai/) (`jina-embeddings-v3`, 1024-dim) / [HuggingFace](https://huggingface.co/) `all-MiniLM-L6-v2` fallback |
| **Vector Database** | [Supabase](https://supabase.com/) PostgreSQL + `pgvector` |
| **RAG Framework** | [LlamaIndex](https://www.llamaindex.ai/) |
| **Document Processing** | `pypdf`, `reportlab` |

---

## 🚀 Live Deployment

The application is deployed on Render and combines the REST API and the interactive frontend:

👉 **[https://quizora-api-z38n.onrender.com/](https://quizora-api-z38n.onrender.com/)**

API Health Check:
```bash
curl https://quizora-api-z38n.onrender.com/api/health
```

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.10+
- PostgreSQL with `pgvector` extension (or a free [Supabase](https://supabase.com) database)
- [Groq API Key](https://console.groq.com/)
- [Jina AI API Key](https://jina.ai/embeddings/) *(Optional for local dev; falls back to local MiniLM)*

### 2. Clone and Install Dependencies
```bash
git clone https://github.com/JITENDRASHEKHAWAT44/Quizora.git
cd Quizora

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```dotenv
# LLM Provider
GROQ_API_KEY="gsk_your_groq_api_key_here"

# Vector Embeddings (Recommended for cloud/low memory)
JINA_API_KEY="jina_your_jina_key_here"

# Database Connection (Supabase Session Pooler or Local PostgreSQL)
# Format: postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
DATABASE_URL="postgresql://postgres:password@localhost:5432/quizora"
```

### 4. Enable `pgvector` in your Database
Run this in your database's SQL query tool:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Start the Server
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Visit **`http://localhost:8000`** in your browser.

---

## 📖 Usage Guide

1. **Upload Document:** Drag-and-drop any lecture notes, research paper, or textbook PDF.
2. **Configure Assessment:**
   - Choose total questions (e.g., 5 to 50 questions).
   - Balance difficulty percentages (e.g., 30% Easy, 50% Medium, 20% Hard).
3. **Generate:** Click **Generate Quiz** to trigger the 7-stage pipeline.
4. **Review & Download:**
   - Inspect interactive questions, distractors, and explanations with cited pages.
   - Click **Question Paper (PDF)** for student examination handouts.
   - Click **Answer Key (PDF)** for complete solutions with pedagogical reasoning.

---

## 📁 Repository Structure

```
Quizora/
├── api/
│   └── main.py              # FastAPI application & REST endpoints
├── frontend/                # Interactive web frontend
│   ├── css/styles.css       # Clean dark-mode stylesheet
│   ├── js/app.js            # Reactive application logic
│   └── index.html           # Main user interface
├── db_and_models.py         # Unified embedding & vector store provider
├── groq_client.py           # Robust direct Groq client wrapper
├── ingestion_1.py           # Step 1: Chunking & pgvector ingestion
├── document_analyzer_2.py   # Step 2: Topic & curriculum analysis
├── questionplanner3.py      # Step 3: Difficulty & coverage distribution
├── retrieval_engine4.py     # Step 4: Semantic RAG retrieval
├── generationEngine5.py     # Step 5: Batch MCQ generation
├── check6.py                # Step 6: Structural quality filtering
├── correction7.py           # Step 7: Grounding & semantic validation
├── pdf_generator.py         # PDF compilation for questions and answer keys
├── pipeline.py              # End-to-end pipeline orchestrator
├── Procfile                 # Process file for cloud container deployment
├── render.yaml              # Render blueprint deployment specification
└── requirements.txt         # Production dependencies
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for new features, bug fixes, or enhancements.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

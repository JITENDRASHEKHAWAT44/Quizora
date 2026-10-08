"""
Quizora REST API

Run:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Open http://localhost:8000 for the web UI (static frontend).
"""

import asyncio
import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Pipeline deps (LlamaIndex, etc.) are imported only when generating.

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(
    title="Quizora API",
    version="1.0.0",
    description="Generate source-grounded MCQs from PDF study material.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def _validate_difficulty(easy: float, medium: float, hard: float) -> None:
    total = easy + medium + hard
    if abs(total - 100.0) > 0.01:
        raise HTTPException(
            status_code=422,
            detail=f"Easy, medium, and hard must sum to 100% (got {total}%).",
        )


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "quizora"}


@app.post("/api/v1/generate")
async def generate_quiz(
    file: UploadFile = File(..., description="Study material PDF"),
    number_of_questions: int = Form(10, ge=1, le=100),
    easy_percent: float = Form(30, ge=0, le=100),
    medium_percent: float = Form(50, ge=0, le=100),
    hard_percent: float = Form(20, ge=0, le=100),
):
    _validate_difficulty(easy_percent, medium_percent, hard_percent)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Upload must be a PDF file.")

    quiz_id = uuid.uuid4().hex[:12]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    quiz_dir = OUTPUT_DIR / quiz_id
    quiz_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    pdf_path = DATA_DIR / f"{quiz_id}_{safe_name}"

    try:
        with open(pdf_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        def run_pipeline_and_export():
            from pdf_generator import create_answer_pdf, create_question_pdf
            from pipeline import generate_quiz_pipeline

            quiz = generate_quiz_pipeline(
                pdf_path=str(pdf_path),
                number_of_questions=number_of_questions,
                easy_percent=easy_percent,
                medium_percent=medium_percent,
                hard_percent=hard_percent,
            )
            json_path = quiz_dir / "quiz.json"
            question_pdf = quiz_dir / "question_paper.pdf"
            answer_pdf = quiz_dir / "answer_key.pdf"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(quiz, f, indent=2, ensure_ascii=False)
            create_question_pdf(quiz=quiz, output_path=str(question_pdf))
            create_answer_pdf(quiz=quiz, output_path=str(answer_pdf))
            return quiz

        result = await asyncio.to_thread(run_pipeline_and_export)

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        if quiz_dir.exists():
            shutil.rmtree(quiz_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quiz generation failed: {exc}",
        ) from exc
    finally:
        await file.close()

    base = f"/api/v1/quizzes/{quiz_id}/files"
    return {
        "quiz_id": quiz_id,
        "meta": {
            "source_filename": safe_name,
            "requested_questions": number_of_questions,
            "easy_percent": easy_percent,
            "medium_percent": medium_percent,
            "hard_percent": hard_percent,
        },
        "quiz": result,
        "downloads": {
            "json": f"{base}/quiz.json",
            "question_paper": f"{base}/question_paper.pdf",
            "answer_key": f"{base}/answer_key.pdf",
        },
    }


@app.get("/api/v1/quizzes/{quiz_id}/files/{filename}")
def download_quiz_file(quiz_id: str, filename: str):
    allowed = {
        "quiz.json": "application/json",
        "question_paper.pdf": "application/pdf",
        "answer_key.pdf": "application/pdf",
    }
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="File not found.")

    path = OUTPUT_DIR / quiz_id / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Quiz or file not found.")

    return FileResponse(
        path,
        media_type=allowed[filename],
        filename=filename,
    )


if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )

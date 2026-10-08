@echo off
title Quizora Server
echo.
echo  =============================================
echo    Quizora ^| Starting server...
echo  =============================================
echo.

REM Always use the RAG venv — it has llama_index, groq, torch, etc.
set PYTHON=%~dp0RAG\Scripts\python.exe
set UVICORN=%~dp0RAG\Scripts\uvicorn.exe

REM Check the venv exists
if not exist "%UVICORN%" (
    echo  [ERROR] RAG venv not found at: %UVICORN%
    echo  Run:  pip install -r requirements.txt  inside the RAG venv first.
    pause
    exit /b 1
)

echo  Python  : %PYTHON%
echo  Uvicorn : %UVICORN%
echo  URL     : http://localhost:8000
echo.

cd /d "%~dp0"
"%UVICORN%" api.main:app --reload --host 0.0.0.0 --port 8000

pause

"""
ExamForge — config.py
All settings, thresholds, and paths in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "chroma_db"
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# --- Document handling ---------------------------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# --- Chunking (Unit 3) -----------------------------------------------------
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# --- Embeddings (Unit 4) -----------------------------------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Reranking (Unit 8) -----------------------------------------------------
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- Vector store (Unit 5) -----------------------------------------------------
CHROMA_COLLECTION_PREFIX = "doc_"

# --- Self-correction (Unit 10) -----------------------------------------------
MAX_SELFCHECK_RETRIES = 2

# --- OCR (Unit 11 fallback for vector-drawn/scanned tables) -----------------
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Grading (Phase 7) -------------------------------------------------
PASSING_THRESHOLD = 0.6  # fraction correct to NOT be flagged as a weak topic

# --- Evaluation (Unit 14) -----------------------------------------------
GOLDEN_SET_PATH = "eval/golden_set.json"

# --- LLM (Groq) — Unit 13+ ---------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
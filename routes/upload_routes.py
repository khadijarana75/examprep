"""
routes/upload_routes.py
POST /api/upload -> ingest a document into the vector store
"""

from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

import config
from controllers import upload_controller

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'.")

    contents = await file.read()
    try:
        return upload_controller.handle_upload(file.filename, contents)
    except Exception as e:
        raise HTTPException(400, str(e))
"""
routes/generate_routes.py
POST /api/generate -> retrieve + rerank + generate MCQ questions for a topic
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from controllers import generate_controller

router = APIRouter(prefix="/api/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    source_name: str
    topic: str
    num_questions: int = 3
    final_top_k: int = 5


@router.post("")
def generate(req: GenerateRequest):
    try:
        return generate_controller.handle_generate(
            req.source_name, req.topic, req.num_questions, req.final_top_k
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
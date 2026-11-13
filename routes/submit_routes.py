"""
routes/submit_routes.py
POST /api/submit   -> grade answers, identify weak topics
POST /api/followup -> regenerate questions targeting weak topics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from controllers import submit_controller

router = APIRouter(prefix="/api", tags=["submit"])


class SubmitRequest(BaseModel):
    source_name: str
    verified_questions: list[dict]  # pass back the questions the learner was given
    submitted_answers: dict         # {"0": 2, "1": 0, ...}


class FollowupRequest(BaseModel):
    source_name: str
    weak_topics: list[str]
    num_questions: int = 3


@router.post("/submit")
def submit(req: SubmitRequest):
    try:
        return submit_controller.handle_submit(req.source_name, req.verified_questions, req.submitted_answers)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/followup")
def followup(req: FollowupRequest):
    try:
        return submit_controller.handle_followup(req.source_name, req.weak_topics, req.num_questions)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
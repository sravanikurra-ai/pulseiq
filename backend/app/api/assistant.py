from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.llm_schemas import AssistantQuery, AssistantResponse
from app.services.llm_service import ask_assistant

router = APIRouter(prefix="/analytics", tags=["Assistant"], dependencies=[Depends(require_role("VIEWER"))])


@router.post("/query", response_model=AssistantResponse)
async def query_assistant(body: AssistantQuery, db: Session = Depends(get_db)):
    result = ask_assistant(db, body.question)
    return AssistantResponse(**result)
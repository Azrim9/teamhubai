import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models import Job, Match, User

router = APIRouter(prefix="/matches", tags=["matches"])

# --- Pydantic Schemas ---

class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_id: uuid.UUID
    agent_id: uuid.UUID
    rank: int
    score: float
    reasoning: str
    created_at: datetime
    updated_at: datetime

# --- Endpoints ---

@router.get("", response_model=List[MatchResponse])
async def list_matches(
    job_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all matches for the current user's jobs, with an optional filter for a specific job.
    """
    query = select(Match).join(Job).where(Job.user_id == current_user.id)
    
    if job_id:
        query = query.where(Match.job_id == job_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}", response_model=List[MatchResponse])
async def get_job_matches(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all matches for a specific job belonging to the current user.
    """
    # Verify job belongs to user
    job_query = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    job_result = await db.execute(job_query)
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    query = select(Match).where(Match.job_id == job_id)
    result = await db.execute(query)
    return result.scalars().all()

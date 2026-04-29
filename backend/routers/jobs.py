import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from ..dependencies import get_current_user, get_db
from ..models import Job, JobStatus, User

router = APIRouter(prefix="/jobs", tags=["jobs"])

# --- Pydantic Schemas ---

class JobBase(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    status: JobStatus = JobStatus.open

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    status: Optional[JobStatus] = None

class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID

class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    pages: int

# --- Endpoints ---

@router.get("", response_model=JobListResponse)
async def list_jobs(
    search: Optional[str] = None,
    status: Optional[JobStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).where(Job.user_id == current_user.id)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_filter),
                Job.description.ilike(search_filter)
            )
        )
    
    if status:
        query = query.where(Job.status == status)

    # Count total for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    pages = math.ceil(total / limit) if total > 0 else 1
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_job = Job(
        **job_in.model_dump(),
        user_id=current_user.id
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    return new_job

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    job_in: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(job)
    await db.commit()
    return None

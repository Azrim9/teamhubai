import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from dependencies import get_current_user, get_db
from models import Agent, AgentStatus, User

router = APIRouter(prefix="/agents", tags=["agents"])

# --- Pydantic Schemas ---

class AgentBase(BaseModel):
    name: str
    role: str
    skills: List[str]
    status: AgentStatus = AgentStatus.idle

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[List[str]] = None
    status: Optional[AgentStatus] = None

class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID

class AgentListResponse(BaseModel):
    items: List[AgentResponse]
    total: int
    page: int
    pages: int

# --- Endpoints ---

@router.get("", response_model=AgentListResponse)
async def list_agents(
    search: Optional[str] = None,
    status: Optional[AgentStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Agent).where(Agent.user_id == current_user.id)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Agent.name.ilike(search_filter),
                Agent.role.ilike(search_filter)
            )
        )
    
    if status:
        query = query.where(Agent.status == status)

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

@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_in: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_agent = Agent(
        **agent_in.model_dump(),
        user_id=current_user.id
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    agent_in: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.commit()
    await db.refresh(agent)
    return agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(agent)
    await db.commit()
    return None

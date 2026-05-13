import json
import os
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from models import Agent, Job, Match, User

router = APIRouter(prefix="/match", tags=["match"])

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

async def get_current_user_from_query(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/stream/{job_id}")
async def match_stream(
    job_id: uuid.UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_from_query(token, db)
    
    # Load job
    job_result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user.id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Load agents
    agents_result = await db.execute(
        select(Agent).where(Agent.user_id == user.id)
    )
    agents = agents_result.scalars().all()
    if not agents:
        raise HTTPException(status_code=400, detail="No agents found. Please create agents first.")

    agent_descriptions = "\n".join([
        f"- AGENT_ID={str(a.id)} | Name: {a.name} | Role: {a.role} | Skills: {', '.join(a.skills)}"
        for a in agents
    ])
    
    prompt = f"""
You are an expert AI recruiter. Analyze the following job and find the top 3 best matching agents from the list.

JOB:
Title: {job.title}
Description: {job.description}
Required Skills: {', '.join(job.required_skills)}

AVAILABLE AGENTS:
{agent_descriptions}

INSTRUCTIONS:
CRITICAL: Copy each AGENT_ID value exactly as shown above. 
These are UUIDs and must not be shortened or modified in any way.
1. Analyze each agent's skills against the job requirements.
2. Select exactly the top 3 agents ranked by skill match.
3. Provide your reasoning first.
4. Then output a JSON block with EXACTLY this format, using the 
   COMPLETE agent IDs exactly as provided above (do not truncate them):

```json
[
  {{"agent_id": "FULL-UUID-HERE", "rank": 1, "score": 0.95}},
  {{"agent_id": "FULL-UUID-HERE", "rank": 2, "score": 0.80}},
  {{"agent_id": "FULL-UUID-HERE", "rank": 3, "score": 0.65}}
]
```

IMPORTANT: Use the exact full UUID strings from the AVAILABLE AGENTS 
list above. Do not shorten or truncate any ID.
"""

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a specialized agent matching assistant."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            async for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    full_response += content
                    yield f"data: {content}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Post-stream processing: Parse JSON and save to database
            try:
                if "```json" in full_response:
                    json_str = full_response.split("```json")[1].split("```")[0].strip()
                    match_results = json.loads(json_str)
                    
                    # Delete existing matches for this job before saving new ones
                    from sqlalchemy import delete
                    await db.execute(delete(Match).where(Match.job_id == job.id))
                    await db.commit()
                    
                    for m in match_results[:3]:
                        new_match = Match(
                            job_id=job.id,
                            agent_id=uuid.UUID(m["agent_id"]),
                            rank=m["rank"],
                            score=m["score"],
                            reasoning=full_response
                        )
                        db.add(new_match)
                    
                    await db.commit()
            except Exception as parse_error:
                print(f"Error parsing or saving matches: {parse_error}")
                
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .models import Base, engine
from .routers.agents import router as agents_router
from .routers.jobs import router as jobs_router
from .routers.match import router as match_router
from .routers.matches import router as matches_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="TeamHub AI API",
    description="Backend API for TeamHub AI - AI-powered agent matching platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != [""] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(matches_router, prefix="/api")
app.include_router(match_router, prefix="/api")

@app.get("/")
async def health_check():
    return {"status": "ok"}

"""FastAPI application entrypoint for the multi-agent workflow engine."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Multi-Agent Workflow Engine",
    description=(
        "Specialized agents (Planner, Researcher, Critic, Formatter) "
        "collaborate via a LangGraph state machine to complete tasks "
        "such as report generation. Submit a task and poll for results "
        "and full agent traces."
    ),
    version="0.1.0",
)

app.include_router(router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": "Multi-Agent Workflow Engine",
        "docs": "/docs",
        "health": "/health",
    }

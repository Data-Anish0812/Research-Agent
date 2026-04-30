"""
Pydantic models and LangGraph state for the AI Research Agent.
Single source of truth for all data shapes.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field


# ── Planner ──────────────────────────────────────────────────────────────────

class PlanStep(BaseModel):
    step_number: int
    description: str
    status: str = "pending"


class PlannerOutput(BaseModel):
    plan_steps: list[PlanStep]
    search_queries: list[str]


# ── Sources ───────────────────────────────────────────────────────────────────

class RawSource(BaseModel):
    title: str = ""
    url: str
    snippet: str = ""
    date: str = ""
    scraped_content: str = ""


class SourceScore(BaseModel):
    relevance: int = Field(..., ge=1, le=5)
    authority: int = Field(..., ge=1, le=5)
    recency: int = Field(..., ge=1, le=5)
    depth: int = Field(..., ge=1, le=5)


class GradedSource(BaseModel):
    title: str = ""
    url: str
    snippet: str = ""
    date: str = ""
    scraped_content: str = ""
    scores: SourceScore
    overall_score: float


# ── Conflict Detection ────────────────────────────────────────────────────────

class ClaimPosition(BaseModel):
    claim: str
    source_urls: list[str] = Field(default_factory=list)


class Dispute(BaseModel):
    topic: str
    position_a: ClaimPosition
    position_b: ClaimPosition
    reason_for_difference: str


class ConflictReport(BaseModel):
    agreed: list[str] = Field(default_factory=list)
    disputed: list[Dispute] = Field(default_factory=list)
    unclear: list[str] = Field(default_factory=list)


# ── Findings & Output ─────────────────────────────────────────────────────────

class Finding(BaseModel):
    claim: str
    source_urls: list[str] = Field(default_factory=list)
    verified: bool = False
    evidence_snippets: list[str] = Field(default_factory=list)


class ToolCallLog(BaseModel):
    tool_name: str
    input: str
    success: bool = True
    latency_ms: int = 0
    error: str | None = None


class SourceUsed(BaseModel):
    title: str = ""
    url: str
    quality_score: float


class ResearchOutput(BaseModel):
    request_id: str = ""
    question: str
    short_answer: str
    key_findings: list[Finding]
    conflict_report: ConflictReport
    sources_used: list[SourceUsed]
    confidence_level: Literal["high", "medium", "low"]
    confidence_reasoning: str
    limitations: list[str]
    assumptions: list[str]
    suggested_next_steps: list[str]
    plan_used: list[PlanStep]
    tools_called: list[ToolCallLog]
    total_latency_ms: int


class ErrorResponse(BaseModel):
    request_id: str = ""
    error: str
    error_type: Literal["validation", "timeout", "pipeline", "internal"] = "internal"
    detail: str = ""
    question: str = ""


# ── LangGraph State ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    request_id: str
    question: str
    plan_steps: list[dict[str, Any]]
    search_queries: list[str]
    raw_sources: Annotated[list[dict[str, Any]], operator.add]
    graded_sources: list[dict[str, Any]]
    conflict_report: dict[str, Any] | None
    findings: list[dict[str, Any]]
    short_answer: str
    confidence_level: str
    confidence_reasoning: str
    limitations: list[str]
    assumptions: list[str]
    suggested_next_steps: list[str]
    tools_called: Annotated[list[dict[str, Any]], operator.add]
    current_node: str
    error: str | None

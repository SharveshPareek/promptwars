"""Pydantic models for intake parsing and structured output."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class IntakeResult(BaseModel):
    """Structured output from Pipeline 1: multimodal intake parsing."""

    situation_type: Literal["medical", "accident", "disaster", "general"] = Field(
        description="Category of the emergency situation"
    )
    severity: Literal["critical", "high", "medium", "low"] = Field(
        description="Overall severity assessment"
    )
    entities: list[str] = Field(
        description="People, medications, objects, or vehicles detected"
    )
    symptoms_or_damage: list[str] = Field(
        description="Observed symptoms, injuries, or damage indicators"
    )
    location_cues: list[str] = Field(
        description="Any location hints from the input"
    )
    time_sensitivity: str = Field(
        description="How urgently action is needed"
    )
    raw_summary: str = Field(
        description="Plain-language summary of the situation"
    )

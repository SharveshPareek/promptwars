"""Pydantic models for the verified action plan output."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class ActionItem(BaseModel):
    """A single verified action with confidence score."""

    priority: int = Field(description="Priority order (1 = highest)")
    action: str = Field(description="Clear, actionable instruction")
    reasoning: str = Field(description="Why this action is recommended")
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0"
    )
    source: str = Field(
        description="Medical protocol or guideline reference"
    )
    do_not: str = Field(
        description="Related action to AVOID, or empty string if none"
    )


class ReasoningResult(BaseModel):
    """Structured output from Pipeline 2: deep reasoning analysis."""

    situation_analysis: str = Field(
        description="Detailed analysis of the situation"
    )
    risk_factors: list[str] = Field(
        description="Identified risk factors"
    )
    recommended_actions: list[str] = Field(
        description="Actions based on medical/emergency protocols"
    )
    contraindications: list[str] = Field(
        description="Actions that should NOT be taken"
    )
    protocols_referenced: list[str] = Field(
        description="Medical or emergency protocols used for analysis"
    )
    urgency_assessment: str = Field(
        description="Detailed urgency evaluation"
    )


class ActionPlan(BaseModel):
    """Final verified action plan - the main output of CrisisLens."""

    situation_summary: str = Field(
        description="Clear, concise summary of the situation"
    )
    triage_level: Literal["RED", "YELLOW", "GREEN", "BLACK"] = Field(
        description="Triage classification: RED=immediate, YELLOW=delayed, GREEN=minor, BLACK=expectant"
    )
    verified_actions: list[ActionItem] = Field(
        description="Ordered list of verified actions to take"
    )
    what_not_to_do: list[str] = Field(
        description="Critical actions to AVOID"
    )
    call_emergency: bool = Field(
        description="Whether to call emergency services immediately"
    )
    emergency_number: str = Field(
        description="Emergency number to call"
    )
    verification_sources: list[str] = Field(
        description="Sources used to verify the action plan"
    )
    confidence_overall: float = Field(
        description="Overall confidence in the action plan from 0.0 to 1.0"
    )

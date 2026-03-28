"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from app.models.intake import IntakeResult
from app.models.actions import ActionItem, ActionPlan


class TestIntakeResult:
    """Test IntakeResult validation."""

    def test_valid_intake(self):
        result = IntakeResult(
            situation_type="medical",
            severity="high",
            entities=["elderly woman", "aspirin", "ibuprofen"],
            symptoms_or_damage=["dizziness", "nausea"],
            location_cues=["home"],
            time_sensitivity="Urgent - within 1 hour",
            raw_summary="Elderly woman took multiple medications and feels dizzy.",
        )
        assert result.situation_type == "medical"
        assert result.severity == "high"
        assert len(result.entities) == 3

    def test_invalid_situation_type(self):
        with pytest.raises(ValidationError):
            IntakeResult(
                situation_type="unknown",
                severity="high",
                entities=[],
                symptoms_or_damage=[],
                time_sensitivity="Urgent",
                raw_summary="Test",
            )

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            IntakeResult(
                situation_type="medical",
                severity="extreme",
                entities=[],
                symptoms_or_damage=[],
                time_sensitivity="Urgent",
                raw_summary="Test",
            )

    def test_empty_entities_allowed(self):
        result = IntakeResult(
            situation_type="general",
            severity="low",
            entities=[],
            symptoms_or_damage=[],
            time_sensitivity="Non-urgent",
            raw_summary="General inquiry.",
        )
        assert result.entities == []


class TestActionItem:
    """Test ActionItem validation."""

    def test_valid_action(self):
        action = ActionItem(
            priority=1,
            action="Call 911 immediately",
            reasoning="Patient showing signs of cardiac event",
            confidence=0.95,
            source="AHA ACLS Guidelines",
        )
        assert action.confidence == 0.95

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ActionItem(
                priority=1,
                action="Test",
                reasoning="Test",
                confidence=1.5,
                source="Test",
            )

    def test_confidence_lower_bound(self):
        with pytest.raises(ValidationError):
            ActionItem(
                priority=1,
                action="Test",
                reasoning="Test",
                confidence=-0.1,
                source="Test",
            )


class TestActionPlan:
    """Test ActionPlan validation."""

    def test_valid_plan(self):
        plan = ActionPlan(
            situation_summary="Patient experiencing drug interaction symptoms",
            triage_level="YELLOW",
            verified_actions=[
                ActionItem(
                    priority=1,
                    action="Discontinue medications",
                    reasoning="Potential interaction",
                    confidence=0.9,
                    source="FDA Drug Interactions DB",
                )
            ],
            what_not_to_do=["Do not give additional medication"],
            call_emergency=False,
            emergency_number="911",
            verification_sources=["FDA", "WebMD"],
            confidence_overall=0.85,
        )
        assert plan.triage_level == "YELLOW"
        assert len(plan.verified_actions) == 1

    def test_invalid_triage_level(self):
        with pytest.raises(ValidationError):
            ActionPlan(
                situation_summary="Test",
                triage_level="PURPLE",
                verified_actions=[],
                what_not_to_do=[],
                call_emergency=False,
                emergency_number="911",
                verification_sources=[],
                confidence_overall=0.5,
            )

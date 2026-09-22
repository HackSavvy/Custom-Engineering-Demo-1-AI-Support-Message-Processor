"""Tests for the structured-output schema and validation layer."""

import pytest
from pydantic import ValidationError

from src.schema import ProcessingResult, SupportTicket


# ── SupportTicket validation ──────────────────────────────────────────────────

def test_valid_ticket_billing():
    ticket = SupportTicket(
        category="billing",
        intent="refund_request",
        urgency="normal",
        summary="Customer wants a refund for an unintended subscription renewal.",
        recommended_action="Review refund eligibility per policy.",
    )
    assert ticket.category == "billing"
    assert ticket.intent == "refund_request"
    assert ticket.urgency == "normal"


def test_valid_ticket_technical():
    ticket = SupportTicket(
        category="technical",
        intent="bug_report",
        urgency="high",
        summary="App crashes on file uploads over 5 MB.",
        recommended_action="Escalate to engineering with reproduction steps.",
    )
    assert ticket.category == "technical"
    assert ticket.urgency == "high"


def test_valid_ticket_account():
    ticket = SupportTicket(
        category="account",
        intent="password_reset",
        urgency="high",
        summary="Customer cannot log in and is not receiving reset emails.",
        recommended_action="Manually trigger password reset and check email delivery logs.",
    )
    assert ticket.category == "account"


def test_valid_ticket_other():
    ticket = SupportTicket(
        category="other",
        intent="general_inquiry",
        urgency="low",
        summary="Customer asked a vague question about their account.",
        recommended_action="Request more details — message is unclear.",
    )
    assert ticket.category == "other"
    assert ticket.urgency == "low"


def test_model_dump_returns_expected_keys():
    ticket = SupportTicket(
        category="billing",
        intent="refund_request",
        urgency="normal",
        summary="Customer wants a refund.",
        recommended_action="Review eligibility.",
    )
    data = ticket.model_dump()
    assert set(data.keys()) == {"category", "intent", "urgency", "summary", "recommended_action"}


def test_invalid_category_raises():
    with pytest.raises(ValidationError):
        SupportTicket(
            category="finance",  # not a valid literal
            intent="refund_request",
            urgency="normal",
            summary="...",
            recommended_action="...",
        )


def test_invalid_urgency_raises():
    with pytest.raises(ValidationError):
        SupportTicket(
            category="billing",
            intent="refund_request",
            urgency="critical",  # not a valid literal
            summary="...",
            recommended_action="...",
        )


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        SupportTicket(  # type: ignore[call-arg]
            category="billing",
            urgency="normal",
            summary="...",
            recommended_action="...",
            # intent is missing
        )


def test_empty_summary_allowed():
    # Pydantic does not reject empty strings by default — the model decides content
    ticket = SupportTicket(
        category="other",
        intent="general_inquiry",
        urgency="low",
        summary="",
        recommended_action="Request more details.",
    )
    assert ticket.summary == ""


# ── ProcessingResult ──────────────────────────────────────────────────────────

def test_processing_result_success():
    ticket = SupportTicket(
        category="billing",
        intent="refund_request",
        urgency="normal",
        summary="Customer wants a refund.",
        recommended_action="Review eligibility.",
    )
    result = ProcessingResult(
        success=True,
        ticket=ticket,
        provider="openai",
        model="gpt-4o",
    )
    assert result.success is True
    assert result.ticket is not None
    assert result.error is None


def test_processing_result_failure():
    result = ProcessingResult(success=False, error="API authentication failed.")
    assert result.success is False
    assert result.ticket is None
    assert result.error == "API authentication failed."


def test_processing_result_no_ticket_on_failure():
    result = ProcessingResult(success=False, error="Timeout")
    assert result.ticket is None


def test_processing_result_provider_and_model_optional():
    result = ProcessingResult(success=False, error="Unknown error")
    assert result.provider is None
    assert result.model is None

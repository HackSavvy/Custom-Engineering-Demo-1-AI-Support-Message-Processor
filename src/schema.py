from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class SupportTicket(BaseModel):
    category: Literal["billing", "technical", "account", "other"]
    intent: str
    urgency: Literal["low", "normal", "high"]
    summary: str
    recommended_action: str


class ProcessingResult(BaseModel):
    success: bool
    ticket: Optional[SupportTicket] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

from __future__ import annotations

import os
from typing import Any

from pydantic import ValidationError

from .schema import ProcessingResult, SupportTicket

SYSTEM_PROMPT = (
    "You are a customer support classifier for a SaaS business. "
    "Analyse the customer message and classify it into the structured fields. "
    "For ambiguous or incomplete messages, make the most reasonable inference "
    "you can and reflect any uncertainty in the recommended_action field "
    "(e.g. 'Request more details — message is unclear')."
)

_TOOL_PROPERTIES: dict[str, Any] = {
    "category": {
        "type": "string",
        "enum": ["billing", "technical", "account", "other"],
        "description": "Primary category of the support request.",
    },
    "intent": {
        "type": "string",
        "description": (
            "Specific intent in snake_case, e.g. refund_request, "
            "password_reset, bug_report, general_inquiry."
        ),
    },
    "urgency": {
        "type": "string",
        "enum": ["low", "normal", "high"],
        "description": (
            "high if the customer is blocked or expresses strong frustration; "
            "low if minor or informational; normal otherwise."
        ),
    },
    "summary": {
        "type": "string",
        "description": "One-sentence summary of the customer's issue.",
    },
    "recommended_action": {
        "type": "string",
        "description": "Recommended first action for the support team.",
    },
}

_TOOL_NAME = "classify_support_ticket"
_REQUIRED = list(_TOOL_PROPERTIES.keys())

# Anthropic tool definition
_ANTHROPIC_TOOL = {
    "name": _TOOL_NAME,
    "description": "Classify and structure a customer support message.",
    "input_schema": {
        "type": "object",
        "properties": _TOOL_PROPERTIES,
        "required": _REQUIRED,
    },
}


def _validate(data: dict[str, Any], provider: str, model: str) -> ProcessingResult:
    try:
        ticket = SupportTicket(**data)
        return ProcessingResult(success=True, ticket=ticket, provider=provider, model=model)
    except ValidationError as exc:
        return ProcessingResult(
            success=False,
            error=f"Schema validation failed: {exc}",
            provider=provider,
            model=model,
        )


class SupportProcessor:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider.lower()
        self._client = self._build_client()

    def _build_client(self) -> Any:
        if self.provider == "anthropic":
            try:
                import anthropic  # type: ignore[import]
            except ImportError:
                raise RuntimeError("anthropic package not installed — run: pip install anthropic")
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
            return anthropic.Anthropic(api_key=api_key)

        if self.provider == "openai":
            try:
                import openai  # type: ignore[import]
            except ImportError:
                raise RuntimeError("openai package not installed — run: pip install openai")
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            return openai.OpenAI(api_key=api_key)

        raise ValueError(f"Unknown provider '{self.provider}'. Choose 'anthropic' or 'openai'.")

    def process(self, message: str) -> ProcessingResult:
        if self.provider == "anthropic":
            return self._process_anthropic(message)
        return self._process_openai(message)

    def _process_anthropic(self, message: str) -> ProcessingResult:
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=[_ANTHROPIC_TOOL],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=[{"role": "user", "content": message}],
            )
            for block in response.content:
                if block.type == "tool_use" and block.name == _TOOL_NAME:
                    return _validate(block.input, "anthropic", model)
            return ProcessingResult(
                success=False,
                error="Model did not return structured output.",
                provider="anthropic",
                model=model,
            )
        except Exception as exc:
            return ProcessingResult(success=False, error=str(exc), provider="anthropic", model=model)

    def _process_openai(self, message: str) -> ProcessingResult:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        try:
            completion = self._client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format=SupportTicket,
            )
            choice = completion.choices[0]
            if choice.finish_reason == "refusal":
                return ProcessingResult(
                    success=False,
                    error=f"Model refused to classify message: {choice.message.refusal}",
                    provider="openai",
                    model=model,
                )
            ticket = choice.message.parsed
            if ticket is None:
                return ProcessingResult(
                    success=False,
                    error="Model did not return structured output.",
                    provider="openai",
                    model=model,
                )
            return ProcessingResult(success=True, ticket=ticket, provider="openai", model=model)
        except Exception as exc:
            return ProcessingResult(success=False, error=str(exc), provider="openai", model=model)

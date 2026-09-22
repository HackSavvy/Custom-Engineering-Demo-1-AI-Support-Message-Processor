# AI Support Message Processor

A working demo of a Custom Engineering integration pattern: an LLM transforms unstructured customer support messages into validated structured data, ready to drive downstream workflows.

> **All examples use synthetic data. No real customer information is included or processed.**

---

## What this demonstrates

Support teams receive messages in natural language. Routing, ticketing, and triage systems need structured fields. Traditionally that gap is bridged by human effort or brittle keyword rules.

This demo shows the alternative: pass the raw message through a Claude (or OpenAI) model with a defined output schema. Validate the result. Surface it to the next system.

The same pattern — *unstructured input → LLM → validated structured output* — applies to any domain where natural language needs to drive a structured workflow: intake forms, sales notes, maintenance reports, legal correspondence.

---

## Architecture

```
User (browser)
     │
     ▼
Streamlit UI  (app.py)
     │
     ▼
SupportProcessor  (src/processor.py)
     │
     ├─── Anthropic API  (Claude, tool-use forcing)
     │         │
     └─── OpenAI API     (GPT, function-calling)
               │
               ▼
      Pydantic schema validation  (src/schema.py)
               │
               ▼
      ProcessingResult  →  UI displays validated output
                           or a clear error
```

Components are separated so the business logic (`processor.py`, `schema.py`) is independent of the UI and trivially importable into any other Python application.

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/HackSavvy/Custom-Engineering-Demo-1-AI-Support-Message-Processor.git
cd Custom-Engineering-Demo-1-AI-Support-Message-Processor
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Open .env and add your OPENAI_API_KEY
```

### 3. Run

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

---

## Configuration

| Variable | Required | Default | Notes |
|---|---|---|---|
| `OPENAI_API_KEY` | **Yes** | — | [Get a key](https://platform.openai.com/) |
| `OPENAI_MODEL` | No | `gpt-4o` | Any OpenAI model that supports Structured Outputs |
| `ANTHROPIC_API_KEY` | No | — | Optional; enables switching to Claude in the UI |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-6` | Any Claude model ID |

`OPENAI_API_KEY` is the only required key. If an `ANTHROPIC_API_KEY` is also present the UI exposes both providers.

For Anthropic support, uncomment the `anthropic` line in `requirements.txt` and run `pip install anthropic`.

---

## Structured output schema

Every successful response is validated against this schema before being displayed:

```python
class SupportTicket(BaseModel):
    category:           Literal["billing", "technical", "account", "other"]
    intent:             str   # e.g. refund_request, bug_report, password_reset
    urgency:            Literal["low", "normal", "high"]
    summary:            str   # one-sentence description
    recommended_action: str   # first action for the support team
```

The OpenAI path uses `client.beta.chat.completions.parse(response_format=SupportTicket)` — the SDK enforces the schema strictly and returns an already-validated Pydantic model instance. The Anthropic path uses tool-use forcing. Both paths run through the same `ProcessingResult` wrapper so the UI handles them identically.

---

## Validation and error handling

| Scenario | Behaviour |
|---|---|
| Valid structured response | Displayed with a green "Validated" badge |
| Model returns wrong field values | Pydantic `ValidationError` caught; red error shown |
| No API key configured | App stops at startup with a clear message |
| Network / API error | Exception caught; error detail shown |
| Ambiguous or incomplete message | Model still returns valid structure; `recommended_action` notes the ambiguity |

---

## Synthetic examples

Four examples are bundled in `src/examples.py`:

| Label | Category | Demonstrates |
|---|---|---|
| Billing — Refund Request | `billing` | Standard well-formed message |
| Technical — App Crash | `technical` | Urgency escalation (`high`) |
| Account — Locked Out | `account` | Time-sensitive account issue |
| Ambiguous — Incomplete | `other` | Graceful handling of insufficient information |

---

## Running the tests

The test suite covers the schema and validation layer (no API calls required):

```bash
pytest tests/ -v
```

---

## Project layout

```
├── app.py              # Streamlit UI
├── src/
│   ├── schema.py       # Pydantic models: SupportTicket, ProcessingResult
│   ├── processor.py    # LLM service (Anthropic + OpenAI)
│   └── examples.py     # Bundled synthetic examples
├── tests/
│   └── test_schema.py  # Validation layer tests
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Synthetic data notice

All messages included in this repository are invented for demonstration purposes. No real customer names, account details, or support conversations are included anywhere in this project.

---

## Custom Engineering

This demo is part of the [QCA Custom Engineering](https://qcacos.com/build) service — fixed-fee AI integrations for businesses that want a working system, not a prototype.

import os

import streamlit as st
from dotenv import load_dotenv

from src.examples import EXAMPLES
from src.processor import SupportProcessor
from src.schema import ProcessingResult

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Support Message Processor",
    page_icon="🎫",
    layout="centered",
)

# ── Header ───────────────────────────────────────────────────────────────────

st.title("AI Support Message Processor")
st.markdown(
    "> **Demo using synthetic data** — no real customer information is used "
    "or stored in this application."
)

# ── Session state init ────────────────────────────────────────────────────────

if "selected_message" not in st.session_state:
    st.session_state.selected_message = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "processed_message" not in st.session_state:
    st.session_state.processed_message = None

# ── Configuration ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("Configuration")

available_providers = []
if os.environ.get("OPENAI_API_KEY"):
    available_providers.append("openai")
if os.environ.get("ANTHROPIC_API_KEY"):
    available_providers.append("anthropic")

if not available_providers:
    st.error(
        "No API key found. Add `OPENAI_API_KEY` to a `.env` file "
        "in the project root, then restart the app."
    )
    st.stop()

col_p, col_m = st.columns(2)
with col_p:
    provider = st.selectbox("Provider", available_providers, index=0)
with col_m:
    if provider == "anthropic":
        model_display = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    else:
        model_display = os.environ.get("OPENAI_MODEL", "gpt-4o")
    st.text_input("Model", value=model_display, disabled=True)

# ── Synthetic examples ────────────────────────────────────────────────────────

st.divider()
st.subheader("Synthetic Examples")
st.caption("Click a button to load an example into the message field.")

ex_cols = st.columns(2)
for i, example in enumerate(EXAMPLES):
    with ex_cols[i % 2]:
        if st.button(example["label"], key=f"ex_{i}", use_container_width=True):
            st.session_state.selected_message = example["message"]

# ── Message input ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("Customer Message")

message = st.text_area(
    "message",
    value=st.session_state.selected_message,
    height=130,
    placeholder=(
        "Enter a customer support message, or choose a synthetic example above…"
    ),
    label_visibility="collapsed",
)

btn_col, clear_col = st.columns([4, 1])
with btn_col:
    process_clicked = st.button("Process Message", type="primary", use_container_width=True)
with clear_col:
    if st.button("Clear", use_container_width=True):
        st.session_state.result = None
        st.session_state.processed_message = None
        st.session_state.selected_message = ""
        st.rerun()

# ── Processing ────────────────────────────────────────────────────────────────

if process_clicked:
    if not message.strip():
        st.warning("Please enter a message before clicking Process.")
    else:
        with st.spinner("Calling LLM and validating structured output…"):
            try:
                processor = SupportProcessor(provider=provider)
                result = processor.process(message.strip())
            except Exception as exc:
                result = ProcessingResult(success=False, error=str(exc))
        st.session_state.result = result
        st.session_state.processed_message = message.strip()

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.result is not None:
    st.divider()
    st.subheader("Results")

    result: ProcessingResult = st.session_state.result

    st.markdown("**Input message**")
    st.code(st.session_state.processed_message, language=None)

    if result.success and result.ticket:
        st.success(
            f"✅ Validated  ·  provider: `{result.provider}`  ·  model: `{result.model}`"
        )
        st.markdown("**Structured output**")
        st.json(result.ticket.model_dump())
    else:
        st.error("❌ Processing failed — structured output could not be validated.")
        if result.error:
            st.markdown("**Error detail**")
            st.code(result.error, language=None)

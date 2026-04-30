"""Sidebar component — API key status + pipeline overview."""

import streamlit as st
from config.settings import get_settings


def render_sidebar() -> None:
    cfg = get_settings()
    with st.sidebar:
        st.markdown("## Configuration")
        st.markdown("---")

        st.markdown("**API Key Status**")
        _key_status("Gemini API", cfg.has_gemini)
        _key_status("Groq API", cfg.has_groq)
        _key_status("Tavily API", cfg.has_tavily)

        missing = cfg.validate_keys()
        for msg in missing:
            st.warning(f"Missing: {msg}")

        st.markdown("---")
        st.markdown("**Pipeline**")
        st.markdown("""
1. Planner
2. Web Search
3. Source Grader
4. Conflict Detector
5. Synthesizer
6. Citation Validator
7. Confidence Scorer
        """)

        st.markdown("---")
        st.markdown("**About**")
        st.caption(
            "Agentic research pipeline powered by LangGraph. "
            "Primary LLM: Gemini 2.5 Flash. Fallback: Groq Llama 3.3 70B. "
            "Web search via Tavily. Page scraping via Jina Reader."
        )


def _key_status(label: str, is_set: bool) -> None:
    dot = "&#9899;" if is_set else "&#9898;"
    status = "Set" if is_set else "Not set"
    st.markdown(f"{dot} {label} — {status}", unsafe_allow_html=True)

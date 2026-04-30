"""
AI Research Agent — Streamlit entrypoint.

This file is intentionally thin:
  - Page config + CSS injection
  - Calls UI components from app/ui/
  - Calls pipeline runner from app/core/
  - Zero business logic here
"""

import streamlit as st
from dotenv import load_dotenv

from utils.logging import setup_logging
from config.settings import get_settings

# ── Bootstrap ────────────────────────────────────────────────────────────────
load_dotenv()
cfg = get_settings()
setup_logging(cfg.log_level)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title=cfg.app_title,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Late imports (after page config) ─────────────────────────────────────────
from app.ui import CUSTOM_CSS, PipelineProgress, render_result, render_sidebar
from app.core.runner import run_pipeline

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    render_sidebar()

    st.markdown(f"# {cfg.app_title}")
    st.markdown(
        "Enter a research question. The agent will plan, search, grade sources, "
        "detect conflicts, synthesise findings, and score confidence — automatically."
    )
    st.markdown("---")

    question = st.text_area(
        "Research Question",
        placeholder="e.g. What are the latest advancements in quantum computing?",
        height=100,
        key="question_input",
    )

    run_btn = st.button("🔍 Run Research", type="primary", disabled=not question.strip())

    if run_btn and question.strip():
        st.markdown("---")
        st.markdown("**Pipeline Progress**")
        progress_placeholder = st.empty()
        progress = PipelineProgress(progress_placeholder)

        with st.spinner("Running agentic research pipeline..."):
            result, error = run_pipeline(
                question.strip(),
                on_node_start=progress.start,
                on_node_done=progress.complete,
            )

        if error:
            st.error(f"Research failed: {error}")
        elif result:
            st.markdown("---")
            st.markdown("## Results")
            render_result(result)


if __name__ == "__main__":
    main()

"""Results renderer — displays the full research output in structured sections."""

import streamlit as st


def render_result(result: dict) -> None:
    """Render a research result dict in a structured, readable Streamlit layout."""
    _render_metrics(result)
    st.markdown("---")
    _render_summary(result)
    st.markdown("---")
    _render_findings(result)
    st.markdown("---")
    _render_consensus_and_sources(result)
    st.markdown("---")
    _render_plan(result)
    _render_meta_columns(result)
    _render_tool_log(result)
    _render_download(result)


# ── Private section renderers ─────────────────────────────────────────────────

def _render_metrics(result: dict) -> None:
    conf = result.get("confidence_level", "low")
    latency_s = result.get("total_latency_ms", 0) / 1000
    n_sources = len(result.get("sources_used", []))
    findings = result.get("key_findings", [])
    verified = sum(1 for f in findings if f.get("verified"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Confidence", conf.capitalize())
    c2.metric("Sources Used", n_sources)
    c3.metric("Findings", f"{verified}/{len(findings)} verified")
    c4.metric("Time Taken", f"{latency_s:.1f}s")


def _render_summary(result: dict) -> None:
    st.markdown("<div class='section-header'>Summary</div>", unsafe_allow_html=True)
    st.info(result.get("short_answer") or "No summary available.")
    if result.get("confidence_reasoning"):
        with st.expander("Confidence Reasoning", expanded=False):
            st.write(result["confidence_reasoning"])


def _render_findings(result: dict) -> None:
    findings = result.get("key_findings", [])
    if not findings:
        return
    st.markdown("<div class='section-header'>Key Findings</div>", unsafe_allow_html=True)
    for i, f in enumerate(findings, 1):
        claim = f.get("claim", "")
        verified = f.get("verified", False)
        label = f"{i}. {claim[:100]}{'...' if len(claim) > 100 else ''}"
        with st.expander(label, expanded=False):
            st.markdown(f"**Claim:** {claim}")
            st.markdown(f"**Status:** {'✅ Verified (2+ sources)' if verified else '⚠️ Unverified (1 source)'}")
            urls = f.get("source_urls", [])
            if urls:
                st.markdown("**Sources:**")
                for url in urls:
                    st.markdown(f"- [{url}]({url})")
            for snippet in f.get("evidence_snippets", []):
                st.caption(snippet)


def _render_consensus_and_sources(result: dict) -> None:
    left, right = st.columns(2)

    with left:
        conflict = result.get("conflict_report", {})
        st.markdown("<div class='section-header'>Source Consensus</div>", unsafe_allow_html=True)

        agreed = conflict.get("agreed", [])
        if agreed:
            st.markdown(f"**Agreed ({len(agreed)})**")
            for item in agreed:
                st.markdown(f"<div class='agreed-item'>{item}</div>", unsafe_allow_html=True)

        disputed = conflict.get("disputed", [])
        if disputed:
            st.markdown(f"**Disputed ({len(disputed)})**")
            for d in disputed:
                with st.expander(d.get("topic", "Dispute"), expanded=False):
                    pa, pb = d.get("position_a", {}), d.get("position_b", {})
                    st.markdown(f"**Position A:** {pa.get('claim', '')}")
                    if pa.get("source_urls"):
                        st.caption("Sources: " + ", ".join(pa["source_urls"]))
                    st.markdown(f"**Position B:** {pb.get('claim', '')}")
                    if pb.get("source_urls"):
                        st.caption("Sources: " + ", ".join(pb["source_urls"]))
                    if d.get("reason_for_difference"):
                        st.markdown(f"**Why they differ:** {d['reason_for_difference']}")

        unclear = conflict.get("unclear", [])
        if unclear:
            st.markdown(f"**Unclear ({len(unclear)})**")
            for item in unclear:
                st.markdown(f"<div class='unclear-item'>{item}</div>", unsafe_allow_html=True)

        if not agreed and not disputed and not unclear:
            st.caption("No conflict analysis available.")

    with right:
        sources = result.get("sources_used", [])
        st.markdown("<div class='section-header'>Sources Used</div>", unsafe_allow_html=True)
        if sources:
            for src in sources:
                title = src.get("title") or src.get("url", "")
                url = src.get("url", "")
                score = src.get("quality_score", 0)
                stars = "★" * int(round(score)) + "☆" * (5 - int(round(score)))
                st.markdown(
                    f"<div class='source-card'>"
                    f"<a href='{url}' target='_blank'>{title[:70]}{'...' if len(title) > 70 else ''}</a><br>"
                    f"<small style='color:#6c757d;'>{stars} ({score:.1f}/5)</small>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No sources recorded.")


def _render_plan(result: dict) -> None:
    plan = result.get("plan_used", [])
    if not plan:
        return
    with st.expander("Research Plan", expanded=False):
        for step in plan:
            st.markdown(f"**Step {step.get('step_number', '?')}:** {step.get('description', '')}")


def _render_meta_columns(result: dict) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        items = result.get("limitations", [])
        if items:
            st.markdown("<div class='section-header'>Limitations</div>", unsafe_allow_html=True)
            for item in items:
                st.markdown(f"- {item}")
    with c2:
        items = result.get("assumptions", [])
        if items:
            st.markdown("<div class='section-header'>Assumptions</div>", unsafe_allow_html=True)
            for item in items:
                st.markdown(f"- {item}")
    with c3:
        items = result.get("suggested_next_steps", [])
        if items:
            st.markdown("<div class='section-header'>Suggested Next Steps</div>", unsafe_allow_html=True)
            for item in items:
                st.markdown(f"- {item}")


def _render_tool_log(result: dict) -> None:
    tools = result.get("tools_called", [])
    if not tools:
        return
    with st.expander(f"Tool Call Log ({len(tools)} calls)", expanded=False):
        for t in tools:
            icon = "✅" if t.get("success") else "❌"
            status = "Success" if t.get("success") else f"Failed: {t.get('error', '')}"
            st.markdown(
                f"{icon} **{t.get('tool_name', 'unknown')}** &mdash; "
                f"`{str(t.get('input', ''))[:80]}` &mdash; "
                f"{t.get('latency_ms', 0)}ms &mdash; {status}",
                unsafe_allow_html=True,
            )


def _render_download(result: dict) -> None:
    import json
    st.download_button(
        label="⬇ Download Full Result (JSON)",
        data=json.dumps(result, indent=2, default=str),
        file_name="research_result.json",
        mime="application/json",
    )

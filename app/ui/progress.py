"""Pipeline progress component — live node-by-node status display."""

import streamlit as st
from app.core.runner import NODE_LABELS

_NODE_ORDER = list(NODE_LABELS.keys())


class PipelineProgress:
    """
    Manages live pipeline progress rendering inside a Streamlit placeholder.

    Usage:
        progress = PipelineProgress(st.empty())
        progress.start("planner")
        progress.complete("planner")
    """

    def __init__(self, placeholder):
        self._placeholder = placeholder
        self._completed: list[str] = []
        self._current: str | None = None
        self._render()

    def start(self, node_name: str) -> None:
        self._current = node_name
        self._render()

    def complete(self, node_name: str) -> None:
        if node_name not in self._completed:
            self._completed.append(node_name)
        self._current = None
        self._render()

    def _render(self) -> None:
        lines = []
        for node in _NODE_ORDER:
            label = NODE_LABELS[node]
            if node in self._completed:
                lines.append(f"<div class='step-done'>&#10003; {label}</div>")
            elif node == self._current:
                lines.append(f"<div class='step-running'>&#9654; {label} ...</div>")
            else:
                lines.append(f"<div class='step-pending'>&#9679; {label}</div>")
        self._placeholder.markdown("\n".join(lines), unsafe_allow_html=True)

"""All custom CSS for the Streamlit UI, in one place."""

CUSTOM_CSS = """
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
    }

    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid #e9ecef;
    }

    .finding-card {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-left: 4px solid #0d6efd;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    .finding-card.verified  { border-left-color: #198754; }
    .finding-card.unverified { border-left-color: #ffc107; }

    .source-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.4rem;
        font-size: 0.9rem;
    }

    .badge-high   { background:#d1e7dd; color:#0f5132; padding:3px 10px; border-radius:12px; font-size:0.85rem; font-weight:600; }
    .badge-medium { background:#fff3cd; color:#664d03; padding:3px 10px; border-radius:12px; font-size:0.85rem; font-weight:600; }
    .badge-low    { background:#f8d7da; color:#842029; padding:3px 10px; border-radius:12px; font-size:0.85rem; font-weight:600; }

    .step-done    { color: #198754; font-weight: 500; }
    .step-running { color: #0d6efd; font-weight: 500; }
    .step-pending { color: #6c757d; }

    .agreed-item   { background:#d1e7dd; border-radius:4px; padding:4px 10px; margin:3px 0; font-size:0.9rem; }
    .disputed-item { background:#fff3cd; border-radius:4px; padding:4px 10px; margin:3px 0; font-size:0.9rem; }
    .unclear-item  { background:#e2e3e5; border-radius:4px; padding:4px 10px; margin:3px 0; font-size:0.9rem; }

    section[data-testid="stSidebar"] { background: #f8f9fa; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
"""

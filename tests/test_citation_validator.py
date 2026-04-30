"""
Unit tests for Citation Validator.
Run with: pytest tests/
"""

from agent.nodes.citation_validator import _validate, _normalise


def _make_source(url: str, content: str = "test content") -> dict:
    return {"url": url, "scraped_content": content, "snippet": ""}


def test_normalise_strips_trailing_slash():
    assert _normalise("https://example.com/path/") == _normalise("https://example.com/path")


def test_valid_url_kept():
    sources = [_make_source("https://example.com/page")]
    findings = [{"claim": "test", "source_urls": ["https://example.com/page"], "verified": False}]
    result = _validate(findings, sources)
    assert result[0]["source_urls"] == ["https://example.com/page"]


def test_invented_url_stripped():
    sources = [_make_source("https://real.com/page")]
    findings = [{"claim": "test", "source_urls": ["https://invented.com/fake"], "verified": False}]
    result = _validate(findings, sources)
    assert result[0]["source_urls"] == []
    assert result[0]["verified"] is False


def test_verified_requires_two_urls():
    sources = [_make_source("https://a.com"), _make_source("https://b.com")]
    findings = [{"claim": "test", "source_urls": ["https://a.com", "https://b.com"], "verified": False}]
    result = _validate(findings, sources)
    assert result[0]["verified"] is True


def test_single_url_not_verified():
    sources = [_make_source("https://a.com")]
    findings = [{"claim": "test", "source_urls": ["https://a.com"], "verified": True}]
    result = _validate(findings, sources)
    assert result[0]["verified"] is False


def test_evidence_snippet_attached():
    sources = [_make_source("https://a.com", content="important evidence here")]
    findings = [{"claim": "test", "source_urls": ["https://a.com"], "verified": False}]
    result = _validate(findings, sources)
    assert "important evidence here" in result[0].get("evidence_snippets", [""])[0]

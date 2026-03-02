"""Quality guardrails — rule-based checks to reduce low-quality output.

These guardrails are meant to:
- Flag missing trust/structure elements (sources, FAQs, takeaways)
- Flag common AI "tells" and risky claims (numbers with no citation)
- Provide a structured report that an LLM (or a human) can fix

Guardrails are intentionally conservative. They produce warnings and issues
rather than hard-failing, unless QUALITY_STRICT_MODE is enabled.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

from app.config import QUALITY_MIN_CITATIONS, QUALITY_MIN_FAQS

BANNED_PHRASES = [
    "as an ai language model",
    "i can't browse the web",
    "i do not have access to the internet",
]

REQ_SECTIONS = [
    "Quick Answer",
    "Key Takeaways",
    "FAQs",
    "Sources",
]


def _lower(s: str) -> str:
    return (s or "").lower()


def _extract_h2_titles(md: str) -> list[str]:
    titles = []
    for m in re.finditer(r"^##\s+(.+?)\s*$", md, flags=re.MULTILINE):
        titles.append(m.group(1).strip())
    return titles


def _count_sources(md: str) -> int:
    # Count URLs in Sources section, or footnote definitions
    urls = re.findall(r"https?://[^\s\)\]]+", md)
    return len(set(urls))


def _extract_faq_questions(md: str) -> list[str]:
    # Expect format:
    # ## FAQs
    # ### Question?
    # Answer...
    if "## FAQs" not in md:
        return []
    # get block from FAQs to next H2
    block = md.split("## FAQs", 1)[1]
    block = re.split(r"^##\s+", block, flags=re.MULTILINE)[0]
    qs = []
    for m in re.finditer(r"^###\s+(.+?)\s*$", block, flags=re.MULTILINE):
        qs.append(m.group(1).strip())
    return qs


def _find_number_sentences_without_citation(md: str) -> list[str]:
    # Heuristic: any sentence with a digit should contain a footnote marker [^n]
    # or a URL in the same sentence.
    # This is imperfect but catches many risky claims.
    text = re.sub(r"```.*?```", "", md, flags=re.DOTALL)  # strip code blocks
    # Split into sentences (simple)
    parts = re.split(r"(?<=[\.\?\!])\s+", text)
    flagged = []
    for s in parts:
        if re.search(r"\d", s) and not re.search(r"\[\^\d+\]", s) and not re.search(r"https?://", s):
            # ignore small obvious ones like "Step 1" in headings
            if re.search(r"^\s*#+\s*\d", s.strip()):
                continue
            if len(s.strip()) > 20:
                flagged.append(s.strip()[:220])
    return flagged[:10]


@dataclass
class GuardrailReport:
    passed: bool
    issues: list[str]
    warnings: list[str]
    scores: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_quality_guardrails(article_md: str) -> GuardrailReport:
    """Run rule-based checks over the article markdown."""
    issues: list[str] = []
    warnings: list[str] = []
    scores: dict[str, Any] = {}

    md = article_md or ""
    h2s = _extract_h2_titles(md)

    # Required sections
    missing = [s for s in REQ_SECTIONS if s not in h2s]
    if missing:
        issues.append(f"Missing required sections (H2): {', '.join(missing)}")

    # Banned phrases (AI tells)
    lower_md = _lower(md)
    found_banned = [p for p in BANNED_PHRASES if p in lower_md]
    if found_banned:
        issues.append(f"Contains banned phrases: {', '.join(found_banned)}")

    # Sources / citations
    source_count = _count_sources(md)
    scores["source_count"] = source_count
    if source_count < QUALITY_MIN_CITATIONS:
        issues.append(f"Not enough citations/sources: found {source_count}, need {QUALITY_MIN_CITATIONS}+")

    # FAQs
    faq_qs = _extract_faq_questions(md)
    scores["faq_count"] = len(faq_qs)
    if len(faq_qs) < QUALITY_MIN_FAQS:
        issues.append(f"Not enough FAQs: found {len(faq_qs)}, need {QUALITY_MIN_FAQS}+")

    # Risky numeric claims without citations
    risky = _find_number_sentences_without_citation(md)
    scores["risky_number_sentences"] = len(risky)
    if risky:
        warnings.append("Numeric claims without nearby citations (review): " + " | ".join(risky))

    passed = len(issues) == 0
    return GuardrailReport(passed=passed, issues=issues, warnings=warnings, scores=scores)

"""AI visibility tools (GEO/AI-overview readiness).

This module generates:
- A lightweight "visibility score" based on structural signals
- JSON-LD blocks (Article + FAQPage) when FAQs are present

This is not a guarantee of ranking or inclusion in AI summaries.
It's a best-practice checklist for clarity and machine-readability.
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any


def _extract_h2_titles(md: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", md, flags=re.MULTILINE)]


def _extract_faq(md: str) -> list[dict[str, str]]:
    if "## FAQs" not in md:
        return []
    block = md.split("## FAQs", 1)[1]
    block = re.split(r"^##\s+", block, flags=re.MULTILINE)[0]
    items: list[dict[str, str]] = []
    # Split by ### headings
    parts = re.split(r"^###\s+", block, flags=re.MULTILINE)
    # parts[0] is preface
    for p in parts[1:]:
        lines = p.strip().splitlines()
        if not lines:
            continue
        q = lines[0].strip()
        a = "\n".join(lines[1:]).strip()
        a = re.sub(r"\n{3,}", "\n\n", a)
        if q and a:
            items.append({"question": q, "answer": a})
    return items


def compute_ai_visibility_score(article_md: str) -> dict[str, Any]:
    md = article_md or ""
    h2s = _extract_h2_titles(md)
    has_quick = "Quick Answer" in h2s
    has_takeaways = "Key Takeaways" in h2s
    has_faq = "FAQs" in h2s
    has_sources = "Sources" in h2s
    has_table = "|" in md and "---" in md  # crude markdown table signal
    has_lists = "- " in md or "* " in md

    score = 0
    score += 20 if has_quick else 0
    score += 20 if has_takeaways else 0
    score += 20 if has_faq else 0
    score += 20 if has_sources else 0
    score += 10 if has_lists else 0
    score += 10 if has_table else 0

    return {
        "score": min(score, 100),
        "signals": {
            "has_quick_answer": has_quick,
            "has_key_takeaways": has_takeaways,
            "has_faqs": has_faq,
            "has_sources_section": has_sources,
            "has_lists": has_lists,
            "has_table": has_table,
        },
        "suggestions": _suggestions(has_quick, has_takeaways, has_faq, has_sources, has_lists),
    }


def _suggestions(has_quick: bool, has_takeaways: bool, has_faq: bool, has_sources: bool, has_lists: bool) -> list[str]:
    s = []
    if not has_quick:
        s.append("Add a 'Quick Answer' section near the top (3–5 sentences).")
    if not has_takeaways:
        s.append("Add 'Key Takeaways' with 5–8 bullet points.")
    if not has_faq:
        s.append("Add an FAQ section with clear Q (H3) / A format.")
    if not has_sources:
        s.append("Add a 'Sources' section with at least 2–3 reputable URLs.")
    if not has_lists:
        s.append("Add more bullet lists for scanability.")
    return s


def build_jsonld(article_md: str, title: str, brand_profile: dict[str, Any], meta_description: str = "") -> dict[str, str]:
    """Return JSON-LD strings for Article and FAQPage (when possible)."""
    company = brand_profile.get("company_name") or "Brand"
    today = date.today().isoformat()

    faqs = _extract_faq(article_md)
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": meta_description or "",
        "datePublished": today,
        "dateModified": today,
        "author": {"@type": "Organization", "name": company},
        "publisher": {"@type": "Organization", "name": company},
    }

    faq_schema = None
    if faqs:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                }
                for item in faqs
            ],
        }

    out = {
        "article_jsonld": json.dumps(article_schema, ensure_ascii=False, indent=2),
    }
    if faq_schema:
        out["faq_jsonld"] = json.dumps(faq_schema, ensure_ascii=False, indent=2)
    return out

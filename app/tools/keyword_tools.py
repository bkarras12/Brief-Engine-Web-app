"""Keyword analysis utilities."""

import re
from collections import Counter


def count_keyword_occurrences(text: str, keyword: str) -> int:
    """Count how many times a keyword appears in text (case-insensitive)."""
    return len(re.findall(re.escape(keyword.lower()), text.lower()))


def calculate_keyword_density(text: str, keyword: str) -> float:
    """Calculate keyword density as a percentage."""
    words = text.split()
    if not words:
        return 0.0
    count = count_keyword_occurrences(text, keyword)
    # Count keyword as N words where N = number of words in keyword
    kw_words = len(keyword.split())
    return (count * kw_words / len(words)) * 100


def extract_headings(markdown_text: str) -> list[dict]:
    """Extract H2 and H3 headings from markdown text."""
    headings = []
    for line in markdown_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("### "):
            headings.append({"level": 3, "text": stripped[4:].strip()})
        elif stripped.startswith("## "):
            headings.append({"level": 2, "text": stripped[3:].strip()})
    return headings


def check_keyword_in_headings(markdown_text: str, keyword: str) -> dict:
    """Check if the keyword appears in headings."""
    headings = extract_headings(markdown_text)
    h2_with_kw = [h for h in headings if h["level"] == 2 and keyword.lower() in h["text"].lower()]
    h3_with_kw = [h for h in headings if h["level"] == 3 and keyword.lower() in h["text"].lower()]
    return {
        "total_h2": len([h for h in headings if h["level"] == 2]),
        "total_h3": len([h for h in headings if h["level"] == 3]),
        "h2_with_keyword": len(h2_with_kw),
        "h3_with_keyword": len(h3_with_kw),
    }


def get_word_frequency(text: str, top_n: int = 20) -> list[tuple[str, int]]:
    """Get the most common words in text (excluding common stop words)."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "that", "this", "these", "those", "and", "but", "or", "nor",
        "not", "so", "very", "just", "about", "up", "it", "its", "you", "your",
        "we", "our", "they", "their", "he", "she", "him", "her", "his",
        "i", "me", "my", "myself", "which", "who", "whom", "what", "where",
        "when", "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "only", "own", "same", "than",
        "too", "also", "if", "while",
    }
    words = re.findall(r'\b[a-z]+\b', text.lower())
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    return Counter(filtered).most_common(top_n)

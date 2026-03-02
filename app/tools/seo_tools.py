"""SEO scoring and metadata utilities."""

from app.tools.keyword_tools import (
    calculate_keyword_density,
    check_keyword_in_headings,
    count_keyword_occurrences,
    extract_headings,
)


def compute_seo_score(article: str, keyword: str, title: str) -> dict:
    """Compute a basic SEO score for an article.

    Returns a dict with score (0-100) and individual checks.
    """
    checks = {}
    score = 0

    # 1. Keyword in title (15 points)
    kw_in_title = keyword.lower() in title.lower()
    checks["keyword_in_title"] = kw_in_title
    if kw_in_title:
        score += 15

    # 2. Title length (10 points)
    title_len = len(title)
    checks["title_length"] = title_len
    if 30 <= title_len <= 65:
        score += 10
    elif title_len > 0:
        score += 5

    # 3. Keyword density (15 points)
    density = calculate_keyword_density(article, keyword)
    checks["keyword_density"] = round(density, 2)
    if 0.5 <= density <= 2.5:
        score += 15
    elif density > 0:
        score += 7

    # 4. Keyword in first 100 words (10 points)
    first_100 = " ".join(article.split()[:100])
    kw_in_intro = keyword.lower() in first_100.lower()
    checks["keyword_in_intro"] = kw_in_intro
    if kw_in_intro:
        score += 10

    # 5. Heading structure (15 points)
    headings = extract_headings(article)
    h2_count = len([h for h in headings if h["level"] == 2])
    checks["h2_count"] = h2_count
    if h2_count >= 3:
        score += 10
    elif h2_count >= 1:
        score += 5
    kw_headings = check_keyword_in_headings(article, keyword)
    if kw_headings["h2_with_keyword"] >= 1:
        score += 5

    # 6. Word count (15 points)
    word_count = len(article.split())
    checks["word_count"] = word_count
    if word_count >= 1500:
        score += 15
    elif word_count >= 1000:
        score += 10
    elif word_count >= 500:
        score += 5

    # 7. Paragraph structure (10 points)
    paragraphs = [p.strip() for p in article.split("\n\n") if p.strip()]
    checks["paragraph_count"] = len(paragraphs)
    avg_para_words = (
        sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1)
    )
    checks["avg_paragraph_words"] = round(avg_para_words)
    if 20 <= avg_para_words <= 100:
        score += 10
    elif paragraphs:
        score += 5

    # 8. Content length bonus (10 points)
    if word_count >= 2000:
        score += 10
    elif word_count >= 1500:
        score += 5

    checks["total_score"] = min(score, 100)
    return checks


def generate_meta_description(title: str, keyword: str, article_intro: str) -> str:
    """Generate a meta description (150-160 chars) from article content."""
    # Take first sentence of article as base
    first_sentence = article_intro.split(".")[0].strip() if article_intro else ""

    if len(first_sentence) > 160:
        first_sentence = first_sentence[:157] + "..."
    elif len(first_sentence) < 120:
        first_sentence += f" Learn everything about {keyword}."
        if len(first_sentence) > 160:
            first_sentence = first_sentence[:157] + "..."

    return first_sentence


def estimate_read_time(word_count: int, wpm: int = 250) -> int:
    """Estimate read time in minutes."""
    return max(1, round(word_count / wpm))

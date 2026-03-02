"""Tests for BriefEngine tools — no API key required."""

import pytest

from app.tools.keyword_tools import (
    count_keyword_occurrences,
    calculate_keyword_density,
    extract_headings,
    check_keyword_in_headings,
    get_word_frequency,
)
from app.tools.seo_tools import compute_seo_score, estimate_read_time
from app.tools.writing_tools import (
    count_words,
    count_sentences,
    avg_sentence_length,
    flesch_reading_ease,
    detect_filler_phrases,
    analyze_readability,
)


# ── Keyword Tools ─────────────────────────────────────────────────────

class TestKeywordTools:
    def test_count_keyword_occurrences(self):
        text = "Running shoes are great. The best running shoes for flat feet."
        assert count_keyword_occurrences(text, "running shoes") == 2

    def test_count_keyword_case_insensitive(self):
        text = "Running Shoes are the best RUNNING SHOES."
        assert count_keyword_occurrences(text, "running shoes") == 2

    def test_calculate_keyword_density(self):
        text = "running shoes " * 5 + "other words " * 45  # 10/100 = 10% but kw is 2 words
        density = calculate_keyword_density(text, "running shoes")
        assert density > 0

    def test_extract_headings(self):
        md = "## Introduction\n\nSome text\n\n### Sub heading\n\n## Conclusion"
        headings = extract_headings(md)
        assert len(headings) == 3
        assert headings[0]["level"] == 2
        assert headings[0]["text"] == "Introduction"
        assert headings[1]["level"] == 3

    def test_check_keyword_in_headings(self):
        md = "## Best Running Shoes\n\n### Running Shoes for Beginners\n\n## Price Guide"
        result = check_keyword_in_headings(md, "running shoes")
        assert result["h2_with_keyword"] == 1
        assert result["h3_with_keyword"] == 1
        assert result["total_h2"] == 2

    def test_get_word_frequency(self):
        text = "python python python java java code"
        freq = get_word_frequency(text, top_n=3)
        assert freq[0][0] == "python"
        assert freq[0][1] == 3


# ── SEO Tools ─────────────────────────────────────────────────────────

class TestSEOTools:
    def test_compute_seo_score_basic(self):
        article = "## Running Shoes Guide\n\n" + ("running shoes are great. " * 50)
        result = compute_seo_score(article, "running shoes", "Best Running Shoes Guide")
        assert "total_score" in result
        assert result["total_score"] > 0
        assert result["keyword_in_title"] is True

    def test_compute_seo_score_missing_keyword_in_title(self):
        article = "Some article about fitness. " * 100
        result = compute_seo_score(article, "running shoes", "Fitness Guide")
        assert result["keyword_in_title"] is False

    def test_estimate_read_time(self):
        assert estimate_read_time(250) == 1
        assert estimate_read_time(500) == 2
        assert estimate_read_time(2000) == 8


# ── Writing Tools ─────────────────────────────────────────────────────

class TestWritingTools:
    def test_count_words(self):
        assert count_words("Hello world how are you") == 5

    def test_count_sentences(self):
        assert count_sentences("Hello. How are you? Fine!") == 3

    def test_avg_sentence_length(self):
        text = "Hello world. How are you today friend."  # 2 + 5 = 7 words / 2 sentences
        avg = avg_sentence_length(text)
        assert 2 <= avg <= 5

    def test_flesch_reading_ease(self):
        # Simple text should have high readability
        simple = "The cat sat on the mat. It was a good cat. The cat liked to play."
        score = flesch_reading_ease(simple)
        assert score > 50  # Should be fairly easy

    def test_detect_filler_phrases(self):
        text = "In order to succeed, it is important to note that we should try."
        fillers = detect_filler_phrases(text)
        assert "in order to" in fillers
        assert "it is important to note" in fillers

    def test_analyze_readability(self):
        text = "This is a simple test. It has two sentences. And a third one."
        result = analyze_readability(text)
        assert result["word_count"] > 0
        assert result["sentence_count"] == 3
        assert "flesch_reading_ease" in result


# ── Sanity Checks ─────────────────────────────────────────────────────

class TestSanityChecks:
    def test_empty_text_handling(self):
        assert count_words("") == 0
        assert count_sentences("") == 0
        assert calculate_keyword_density("", "test") == 0.0
        assert extract_headings("") == []

    def test_seo_score_empty_article(self):
        result = compute_seo_score("", "keyword", "Title")
        assert result["total_score"] >= 0

    def test_readability_empty_text(self):
        result = analyze_readability("")
        assert result["word_count"] == 0

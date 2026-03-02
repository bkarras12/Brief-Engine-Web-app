"""Writing quality and readability utilities."""

import re


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def count_sentences(text: str) -> int:
    """Count sentences in text (approximate)."""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def avg_sentence_length(text: str) -> float:
    """Average number of words per sentence."""
    words = count_words(text)
    sentences = count_sentences(text)
    return words / max(sentences, 1)


def flesch_reading_ease(text: str) -> float:
    """Approximate Flesch Reading Ease score.

    90-100: Very easy (5th grade)
    80-89: Easy (6th grade)
    70-79: Fairly easy (7th grade)
    60-69: Standard (8th-9th grade)
    50-59: Fairly difficult (10th-12th grade)
    30-49: Difficult (college)
    0-29: Very difficult (graduate)
    """
    words = count_words(text)
    sentences = count_sentences(text)
    syllables = _count_syllables(text)

    if words == 0 or sentences == 0:
        return 0.0

    return (
        206.835
        - 1.015 * (words / sentences)
        - 84.6 * (syllables / words)
    )


def flesch_grade_level(text: str) -> float:
    """Approximate Flesch-Kincaid Grade Level."""
    words = count_words(text)
    sentences = count_sentences(text)
    syllables = _count_syllables(text)

    if words == 0 or sentences == 0:
        return 0.0

    return (
        0.39 * (words / sentences)
        + 11.8 * (syllables / words)
        - 15.59
    )


def _count_syllables(text: str) -> int:
    """Approximate syllable count."""
    text = text.lower()
    words = re.findall(r'[a-z]+', text)
    total = 0
    for word in words:
        count = 0
        if word[0] in "aeiouy":
            count += 1
        for i in range(1, len(word)):
            if word[i] in "aeiouy" and word[i - 1] not in "aeiouy":
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        total += count
    return total


def detect_filler_phrases(text: str) -> list[str]:
    """Detect common filler phrases that weaken writing."""
    fillers = [
        "in order to", "it is important to note", "it should be noted",
        "needless to say", "it goes without saying", "at the end of the day",
        "when all is said and done", "the fact of the matter is",
        "in today's world", "in this day and age", "as a matter of fact",
        "for all intents and purposes", "each and every", "first and foremost",
        "in the event that", "due to the fact that", "at this point in time",
        "on the other hand", "it is worth mentioning",
    ]
    found = []
    lower_text = text.lower()
    for filler in fillers:
        if filler in lower_text:
            found.append(filler)
    return found


def analyze_readability(text: str) -> dict:
    """Full readability analysis of text."""
    return {
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
        "avg_sentence_length": round(avg_sentence_length(text), 1),
        "flesch_reading_ease": round(flesch_reading_ease(text), 1),
        "flesch_grade_level": round(flesch_grade_level(text), 1),
        "filler_phrases": detect_filler_phrases(text),
    }

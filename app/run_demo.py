"""BriefEngine Demo Runner.

Usage:
    python -m app.run_demo
    python -m app.run_demo --keyword "best crm for small business"
    python -m app.run_demo --keyword "meal prep ideas" --type "listicle"
"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from app.config import OPENAI_API_KEY, OUTPUT_DIR
from app.pipeline import BriefEnginePipeline

console = Console()


# ── Sample Brand Profile ────────────────────────────────────────────
SAMPLE_BRAND_PROFILE = {
    "company_name": "StrideRight Athletics",
    "industry": "E-commerce / Athletic Footwear",
    "target_audience": "Active adults aged 25-45 who run recreationally and prioritize comfort and injury prevention",
    "voice": "Knowledgeable, approachable, evidence-based. Like a running coach who also reads research papers.",
    "voice_guidelines": {
        "tone": "friendly-authoritative",
        "personality_traits": ["knowledgeable", "approachable", "trustworthy"],
        "vocabulary_level": "moderate",
        "dos": [
            "Use specific data and research references",
            "Include practical actionable tips",
            "Address common misconceptions",
        ],
        "donts": [
            "Don't use overly salesy language",
            "Don't make medical claims without caveats",
            "Don't use jargon without explaining it",
        ],
    },
    "content_themes": [
        "running biomechanics",
        "shoe technology",
        "injury prevention",
        "training tips",
    ],
    "competitors": ["Brooks", "ASICS", "Hoka"],
}

SAMPLE_KEYWORD = "best running shoes for flat feet"
SAMPLE_ARTICLE_TYPE = "comprehensive guide"


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with rich formatting."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="BriefEngine Demo")
    parser.add_argument(
        "--keyword", "-k",
        default=SAMPLE_KEYWORD,
        help=f"Target keyword (default: '{SAMPLE_KEYWORD}')",
    )
    parser.add_argument(
        "--type", "-t",
        default=SAMPLE_ARTICLE_TYPE,
        choices=["comprehensive guide", "how-to", "listicle", "comparison", "case study"],
        help="Article type",
    )
    parser.add_argument(
        "--output", "-o",
        default=str(OUTPUT_DIR),
        help="Output directory",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output",
    )
    args = parser.parse_args()

    # ── Validate API Key ─────────────────────────────────────────────
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-key-here":
        console.print(Panel(
            "[red bold]Missing OpenAI API Key![/]\n\n"
            "1. Copy .env.example to .env\n"
            "2. Add your OpenAI API key\n"
            "3. Run again",
            title="⚠️  Setup Required",
        ))
        sys.exit(1)

    setup_logging("WARNING" if args.quiet else "INFO")

    # ── Run Pipeline ─────────────────────────────────────────────────
    console.print(Panel(
        f"[bold cyan]BriefEngine Demo[/]\n\n"
        f"🎯 Keyword: [green]{args.keyword}[/]\n"
        f"📝 Type: {args.type}\n"
        f"🏢 Brand: {SAMPLE_BRAND_PROFILE['company_name']}\n"
        f"📁 Output: {args.output}",
        title="🚀 Starting Pipeline",
    ))

    pipeline = BriefEnginePipeline(output_dir=Path(args.output))
    result = pipeline.generate_article(
        keyword=args.keyword,
        brand_profile=SAMPLE_BRAND_PROFILE,
        article_type=args.type,
    )

    # ── Display Results ──────────────────────────────────────────────
    if result.get("error"):
        console.print(f"\n[red bold]Pipeline failed:[/] {result['error']}")
        sys.exit(1)

    final = result.get("final", {})
    console.print("\n")
    console.print(Panel(
        f"[bold green]✅ Article Generated Successfully![/]\n\n"
        f"📰 Title: [bold]{final.get('title', 'N/A')}[/]\n"
        f"📏 Words: {final.get('word_count', 0)}\n"
        f"⏱️  Read Time: {final.get('read_time_minutes', 0)} min\n"
        f"📊 SEO Score: {final.get('seo_score', 0)}/100\n"
        f"⭐ Quality Score: {final.get('quality_score', 0)}/100\n"
        f"⏰ Pipeline Time: {result.get('pipeline_elapsed_seconds', 0)}s\n\n"
        f"📁 Files saved to: {args.output}/",
        title="📋 Results",
    ))

    # Show article preview
    article = final.get("article", "")
    if article:
        preview = "\n".join(article.split("\n")[:30])
        console.print("\n[dim]─── Article Preview (first 30 lines) ───[/]")
        console.print(Markdown(preview))
        console.print("[dim]─── End Preview ───[/]\n")

    # Show SEO metadata
    meta_title = final.get("meta_title", "")
    meta_desc = final.get("meta_description", "")
    if meta_title or meta_desc:
        console.print(Panel(
            f"[bold]Meta Title:[/] {meta_title}\n"
            f"[bold]Meta Description:[/] {meta_desc}",
            title="🏷️  SEO Metadata",
        ))

    console.print(
        f"\n[green]Done![/] Check [bold]{args.output}/[/] for full output files.\n"
    )


if __name__ == "__main__":
    main()

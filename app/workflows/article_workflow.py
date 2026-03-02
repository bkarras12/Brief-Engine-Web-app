"""Article Workflow — orchestrates the full article generation pipeline.

Pipeline stages:
1. CEO Agent → Content Plan
2. Research Agent → Keyword & Topic Research
3. Outline Agent → Article Outline
4. Writer Agent → First Draft
5. SEO Agent → SEO Analysis & Optimization
6. Editor Agent → Final Polish
7. CEO Agent → Validation
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.agents import (
    CEOAgent,
    ResearchAgent,
    OutlineAgent,
    WriterAgent,
    SEOAgent,
    EditorAgent,
    QualityFixerAgent,
)
from app.tools.seo_tools import compute_seo_score, estimate_read_time
from app.tools.writing_tools import analyze_readability
from app.tools.quality_guardrails import run_quality_guardrails
from app.tools.ai_visibility import compute_ai_visibility_score, build_jsonld
from app.config import QUALITY_STRICT_MODE, QUALITY_AUTO_REPAIR, AI_VISIBILITY_ENABLE, AI_VISIBILITY_INCLUDE_JSONLD
from app.storage.store import RunStore

logger = logging.getLogger("briefengine")


class ArticleWorkflow:
    """End-to-end workflow for generating a single SEO article."""

    def __init__(self, store: RunStore | None = None):
        self.ceo = CEOAgent()
        self.researcher = ResearchAgent()
        self.outliner = OutlineAgent()
        self.writer = WriterAgent()
        self.seo_specialist = SEOAgent()
        self.editor = EditorAgent()
        self.quality_fixer = QualityFixerAgent()
        self.store = store

    def run(
        self,
        keyword: str,
        brand_profile: dict[str, Any],
        article_type: str = "comprehensive guide",
        output_dir: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the full article generation pipeline.

        Args:
            keyword: Target SEO keyword
            brand_profile: Dict with company info, voice guidelines, etc.
            article_type: Type of article to generate
            output_dir: Directory to save outputs (optional)

        Returns:
            Dict with all pipeline outputs and the final article
        """
        run_id = f"run_{int(time.time())}"
        pipeline_start = time.time()
        results: dict[str, Any] = {
            "run_id": run_id,
            "keyword": keyword,
            "artifact_kind": "article",
            "article_type": article_type,
            "stages": {},
        }

        # ── Per-run option overrides (used by web app, etc.) ─────────────
        options = options or {}
        enable_web_research = options.get("enable_web_research", None)
        quality_strict_mode = options.get("quality_strict_mode", QUALITY_STRICT_MODE)
        quality_auto_repair = options.get("quality_auto_repair", QUALITY_AUTO_REPAIR)
        ai_visibility_enable = options.get("ai_visibility_enable", AI_VISIBILITY_ENABLE)
        ai_visibility_include_jsonld = options.get(
            "ai_visibility_include_jsonld", AI_VISIBILITY_INCLUDE_JSONLD
        )

        logger.info(f"{'='*60}")
        logger.info(f"Starting Article Pipeline: '{keyword}'")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"{'='*60}")

        try:
            # ── Stage 1: CEO → Content Plan ──────────────────────────
            logger.info("\n📋 Stage 1/6: CEO creating content plan...")
            ceo_output = self.ceo.run({
                "brand_profile": brand_profile,
                "keyword": keyword,
            "artifact_kind": "article",
                "article_type": article_type,
            })
            results["stages"]["content_plan"] = ceo_output.data
            content_plan = ceo_output.data
            logger.info(f"   ✓ Plan created in {ceo_output.elapsed_seconds:.1f}s")

            # ── Stage 2: Research Agent ──────────────────────────────
            logger.info("\n🔍 Stage 2/6: Researching keyword & topics...")
            research_inputs = {
                "keyword": keyword,
            "artifact_kind": "article",
                "industry": brand_profile.get("industry", "general"),
                "target_audience": brand_profile.get("target_audience", "general"),
            }
            if enable_web_research is not None:
                research_inputs["enable_web_research"] = bool(enable_web_research)

            research_output = self.researcher.run(research_inputs)
            results["stages"]["research"] = research_output.data
            research = research_output.data
            logger.info(f"   ✓ Research complete in {research_output.elapsed_seconds:.1f}s")
            logger.info(f"   Found {len(research.get('related_keywords', []))} related keywords")

            # ── Stage 3: Outline Agent ───────────────────────────────
            logger.info("\n📝 Stage 3/6: Creating article outline...")
            outline_output = self.outliner.run({
                "keyword": keyword,
            "artifact_kind": "article",
                "research": research,
                "content_plan": content_plan,
                "brand_profile": brand_profile,
            })
            results["stages"]["outline"] = outline_output.data
            outline = outline_output.data
            num_sections = len(outline.get("sections", []))
            logger.info(f"   ✓ Outline created in {outline_output.elapsed_seconds:.1f}s")
            logger.info(f"   {num_sections} sections planned")

            # ── Stage 4: Writer Agent ────────────────────────────────
            logger.info("\n✍️  Stage 4/6: Writing first draft...")
            writer_output = self.writer.run({
                "keyword": keyword,
            "artifact_kind": "article",
                "outline": outline,
                "research": research,
                "brand_profile": brand_profile,
                "content_plan": content_plan,
            })
            results["stages"]["first_draft"] = {
                "word_count": writer_output.data.get("word_count", 0),
                "title": writer_output.data.get("title", ""),
            }
            article = writer_output.data.get("article", "")
            title = writer_output.data.get("title", f"Guide to {keyword}")
            logger.info(f"   ✓ Draft written in {writer_output.elapsed_seconds:.1f}s")
            logger.info(f"   {writer_output.data.get('word_count', 0)} words")

            # ── Stage 5: SEO Agent ───────────────────────────────────
            logger.info("\n📊 Stage 5/6: SEO analysis & optimization...")
            seo_output = self.seo_specialist.run({
                "article": article,
                "keyword": keyword,
            "artifact_kind": "article",
                "title": title,
                "research": research,
            })
            results["stages"]["seo"] = seo_output.data
            seo_suggestions = seo_output.data.get("optimization_suggestions", [])
            logger.info(f"   ✓ SEO analysis in {seo_output.elapsed_seconds:.1f}s")
            logger.info(f"   SEO Score: {seo_output.data.get('seo_score', 'N/A')}/100")

            # ── Stage 6: Editor Agent ────────────────────────────────
            logger.info("\n🔧 Stage 6/6: Final editorial polish...")
            editor_output = self.editor.run({
                "article": article,
                "keyword": keyword,
            "artifact_kind": "article",
                "brand_profile": brand_profile,
                "seo_suggestions": seo_suggestions,
            })
            results["stages"]["editor"] = {
                "quality_score": editor_output.data.get("quality_score", 0),
                "changes_made": editor_output.data.get("changes_made", []),
                "word_count": editor_output.data.get("word_count", 0),
            }
            final_article = editor_output.data.get("edited_article", article)
            logger.info(f"   ✓ Editing complete in {editor_output.elapsed_seconds:.1f}s")
            logger.info(f"   Quality Score: {editor_output.data.get('quality_score', 'N/A')}/100")


            # ── Guardrails + AI Visibility ───────────────────────────
            guardrail_report = run_quality_guardrails(final_article).to_dict()
            results["stages"]["guardrails"] = guardrail_report

            ai_visibility = (
                compute_ai_visibility_score(final_article)
                if ai_visibility_enable
                else {"score": 0, "signals": {}, "suggestions": []}
            )

            # Optional auto-repair if guardrails failed
            if (quality_strict_mode or quality_auto_repair) and not guardrail_report.get("passed", True):
                if quality_auto_repair:
                    logger.info("\n🛡️  Guardrails: issues found — attempting auto-repair...")
                    try:
                        wr = research.get("web_research", {}) if isinstance(research, dict) else {}
                        web_sources = (wr.get("top_sources") or []) + (wr.get("results") or [])
                    except Exception:
                        web_sources = []
                    try:
                        fix_output = self.quality_fixer.run({
                            "article": final_article,
                "content": final_article,
                            "guardrail_report": guardrail_report,
                            "web_sources": web_sources,
                        })
                        results["stages"]["quality_fixer"] = {
                            "changes_made": fix_output.data.get("changes_made", []),
                            "notes": fix_output.data.get("notes", ""),
                        }
                        final_article = fix_output.data.get("revised_article", final_article)
                    except Exception as e:
                        logger.warning(f"Auto-repair failed: {e}")
                        results["stages"]["quality_fixer"] = {"error": str(e)}

                    # Re-run checks after repair
                    guardrail_report = run_quality_guardrails(final_article).to_dict()
                    results["stages"]["guardrails"] = guardrail_report
                    ai_visibility = (
                        compute_ai_visibility_score(final_article)
                        if ai_visibility_enable
                        else ai_visibility
                    )
                else:
                    logger.info("\n🛡️  Guardrails: issues found (auto-repair disabled).")

            # ── Assemble Final Output ────────────────────────────────
            final_word_count = len(final_article.split())
            seo_check = compute_seo_score(final_article, keyword, title)
            readability = analyze_readability(final_article)

            jsonld_blocks = {}
            if ai_visibility_enable and ai_visibility_include_jsonld:
                jsonld_blocks = build_jsonld(
                    article_md=final_article,
                    title=title,
                    brand_profile=brand_profile,
                    meta_description=seo_output.data.get("meta_description", ""),
                )

            results["final"] = {
                "artifact_kind": "article",
                "title": title,
                "meta_title": seo_output.data.get("meta_title", title[:60]),
                "meta_description": seo_output.data.get("meta_description", ""),
                "article": final_article,
                "content": final_article,
                "word_count": final_word_count,
                "read_time_minutes": estimate_read_time(final_word_count),
                "seo_score": seo_check.get("total_score", 0),
                "quality_score": editor_output.data.get("quality_score", 0),
                "readability": readability,
                "guardrails": guardrail_report,
                "ai_visibility": ai_visibility,
                "jsonld": jsonld_blocks,
            }

            pipeline_elapsed = time.time() - pipeline_start
            results["pipeline_elapsed_seconds"] = round(pipeline_elapsed, 1)

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Pipeline Complete!")
            logger.info(f"   Title: {title}")
            logger.info(f"   Words: {final_word_count}")
            logger.info(f"   SEO Score: {seo_check.get('total_score', 0)}/100")
            logger.info(f"   Total Time: {pipeline_elapsed:.1f}s")
            logger.info(f"{'='*60}")

            # ── Save outputs ─────────────────────────────────────────
            if output_dir:
                self._save_outputs(output_dir, run_id, results, final_article, title)

            if self.store:
                self.store.save_run(run_id, keyword, results)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            results["error"] = str(e)
            results["status"] = "failed"

        return results

    def _save_outputs(
        self,
        output_dir: Path,
        run_id: str,
        results: dict,
        article: str,
        title: str,
    ) -> None:
        """Save pipeline outputs to files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save the article as markdown
        article_path = output_dir / f"{run_id}_article.md"
        article_content = f"# {title}\n\n{article}"
        article_path.write_text(article_content, encoding="utf-8")
        logger.info(f"   📄 Article saved: {article_path}")

        # Save a stable "primary" output for web downloads
        primary_path = output_dir / f"{run_id}_primary.md"
        primary_path.write_text(article_content, encoding="utf-8")
        logger.info(f"   📄 Primary saved: {primary_path}")

        # Save full results as JSON
        results_path = output_dir / f"{run_id}_results.json"
        # Remove the article text from JSON to keep it small
        results_copy = json.loads(json.dumps(results, default=str))
        if "final" in results_copy:
            results_copy["final"]["article"] = f"[See {run_id}_article.md]"
            if "content" in results_copy["final"]:
                results_copy["final"]["content"] = f"[See {run_id}_primary.md]"

        # Prune large web extracts from the JSON summary (keeps file size reasonable)
        try:
            tops = (
                results_copy.get("stages", {})
                .get("research", {})
                .get("web_research", {})
                .get("top_sources", [])
            )
            for t in tops:
                if isinstance(t, dict):
                    t.pop("extracted_text", None)
        except Exception:
            pass
        results_path.write_text(
            json.dumps(results_copy, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"   📊 Results saved: {results_path}")

        # Save SEO metadata
        meta_path = output_dir / f"{run_id}_seo_meta.json"
        meta = {
            "title": title,
            "meta_title": results.get("final", {}).get("meta_title", ""),
            "meta_description": results.get("final", {}).get("meta_description", ""),
            "keyword": results.get("keyword", ""),
            "word_count": results.get("final", {}).get("word_count", 0),
            "seo_score": results.get("final", {}).get("seo_score", 0),
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        logger.info(f"   🏷️  SEO meta saved: {meta_path}")


        # Save quality guardrails report
        q_path = output_dir / f"{run_id}_quality_report.json"
        q_path.write_text(
            json.dumps(results.get("final", {}).get("guardrails", {}), indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"   🛡️  Quality report saved: {q_path}")

        # Save AI visibility pack
        v_path = output_dir / f"{run_id}_ai_visibility.json"
        v_path.write_text(
            json.dumps(results.get("final", {}).get("ai_visibility", {}), indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"   🤖 AI visibility saved: {v_path}")

        # Save JSON-LD schemas (if present)
        jsonld = results.get("final", {}).get("jsonld", {}) or {}
        if isinstance(jsonld, dict) and jsonld:
            if jsonld.get("article_jsonld"):
                a_path = output_dir / f"{run_id}_article.schema.jsonld"
                a_path.write_text(jsonld["article_jsonld"], encoding="utf-8")
                logger.info(f"   🧩 Article JSON-LD saved: {a_path}")
            if jsonld.get("faq_jsonld"):
                f_path = output_dir / f"{run_id}_faq.schema.jsonld"
                f_path.write_text(jsonld["faq_jsonld"], encoding="utf-8")
                logger.info(f"   🧩 FAQ JSON-LD saved: {f_path}")

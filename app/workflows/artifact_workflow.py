"""Artifact Workflow — generates SEO artifacts beyond blog articles.

Supported artifacts (artifact_kind):
- landing_page
- faq_page
- content_brief
- meta_pack
- social_pack
- gbp_post

This workflow reuses the existing ResearchAgent (and optional web research).
It applies guardrails + AI visibility scoring for all artifacts.
For long-form page-like artifacts (landing_page, faq_page) it also runs SEO + Editor agents.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.agents import (
    ArtifactPlannerAgent,
    ArtifactWriterAgent,
    ResearchAgent,
    SEOAgent,
    EditorAgent,
    QualityFixerAgent,
)
from app.tools.seo_tools import compute_seo_score, estimate_read_time
from app.tools.writing_tools import analyze_readability
from app.tools.quality_guardrails import run_quality_guardrails
from app.tools.ai_visibility import compute_ai_visibility_score, build_jsonld
from app.config import (
    QUALITY_STRICT_MODE,
    QUALITY_AUTO_REPAIR,
    AI_VISIBILITY_ENABLE,
    AI_VISIBILITY_INCLUDE_JSONLD,
)
from app.storage.store import RunStore

logger = logging.getLogger("briefengine")

# For these artifacts we treat output as a page and apply editor/SEO pipelines
LONGFORM_KINDS = {"landing_page", "faq_page"}


class ArtifactWorkflow:
    """End-to-end workflow for generating a single SEO artifact."""

    def __init__(self, store: RunStore | None = None):
        self.planner = ArtifactPlannerAgent()
        self.researcher = ResearchAgent()
        self.writer = ArtifactWriterAgent()
        self.seo_specialist = SEOAgent()
        self.editor = EditorAgent()
        self.quality_fixer = QualityFixerAgent()
        self.store = store

    def run(
        self,
        *,
        keyword: str,
        brand_profile: dict[str, Any],
        artifact_kind: str,
        output_dir: Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = f"run_{int(time.time())}"
        pipeline_start = time.time()
        options = options or {}

        enable_web_research = options.get("enable_web_research", None)
        quality_strict_mode = options.get("quality_strict_mode", QUALITY_STRICT_MODE)
        quality_auto_repair = options.get("quality_auto_repair", QUALITY_AUTO_REPAIR)
        ai_visibility_enable = options.get("ai_visibility_enable", AI_VISIBILITY_ENABLE)
        ai_visibility_include_jsonld = options.get(
            "ai_visibility_include_jsonld", AI_VISIBILITY_INCLUDE_JSONLD
        )

        results: dict[str, Any] = {
            "run_id": run_id,
            "keyword": keyword,
            "artifact_kind": artifact_kind,
            "stages": {},
        }

        logger.info(f"{'='*60}")
        logger.info(f"Starting Artifact Pipeline: '{keyword}' ({artifact_kind})")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"{'='*60}")

        try:
            # ── Stage 1: Plan ───────────────────────────────────────────
            plan_out = self.planner.run(
                {
                    "brand_profile": brand_profile,
                    "keyword": keyword,
                    "artifact_kind": artifact_kind,
                    "extra_context": brand_profile.get("notes", ""),
                }
            )
            plan = plan_out.data
            results["stages"]["plan"] = plan

            # ── Stage 2: Research ───────────────────────────────────────
            research_inputs = {
                "keyword": keyword,
                "industry": brand_profile.get("industry", "general"),
                "target_audience": brand_profile.get("target_audience", "general"),
            }
            if enable_web_research is not None:
                research_inputs["enable_web_research"] = bool(enable_web_research)

            research_out = self.researcher.run(research_inputs)
            research = research_out.data
            results["stages"]["research"] = research

            # ── Stage 3: Write Artifact ─────────────────────────────────
            write_out = self.writer.run(
                {
                    "brand_profile": brand_profile,
                    "keyword": keyword,
                    "artifact_kind": artifact_kind,
                    "plan": plan,
                    "research": research,
                }
            )
            draft = write_out.data
            content_md = draft.get("content_md", "")
            title = draft.get("title") or f"{artifact_kind.replace('_',' ').title()} for {keyword}"

            results["stages"]["draft"] = {
                "title": title,
                "meta_title": draft.get("meta_title", ""),
                "meta_description": draft.get("meta_description", ""),
                "word_count": len((content_md or "").split()),
                "notes": draft.get("notes", ""),
            }

            # ── Optional: SEO + Edit for long-form page-like artifacts ──
            seo_data: dict[str, Any] = {}
            seo_suggestions: list[Any] = []
            if artifact_kind in LONGFORM_KINDS:
                seo_out = self.seo_specialist.run(
                    {
                        "article": content_md,
                        "keyword": keyword,
                        "title": title,
                        "research": research,
                    }
                )
                seo_data = seo_out.data
                seo_suggestions = seo_data.get("optimization_suggestions", []) or []
                results["stages"]["seo"] = seo_data

                edit_out = self.editor.run(
                    {
                        "article": content_md,
                        "keyword": keyword,
                        "brand_profile": brand_profile,
                        "seo_suggestions": seo_suggestions,
                    }
                )
                content_md = edit_out.data.get("edited_article", content_md)
                results["stages"]["editor"] = {
                    "quality_score": edit_out.data.get("quality_score", 0),
                    "changes_made": edit_out.data.get("changes_made", []),
                    "word_count": edit_out.data.get("word_count", 0),
                }

            # ── Guardrails + AI Visibility ──────────────────────────────
            guardrail_report = run_quality_guardrails(content_md).to_dict()
            results["stages"]["guardrails"] = guardrail_report

            ai_visibility = (
                compute_ai_visibility_score(content_md) if ai_visibility_enable else {"score": 0, "signals": {}, "suggestions": []}
            )

            # Optional auto-repair if guardrails failed (only for long-form)
            if (
                artifact_kind in LONGFORM_KINDS
                and (quality_strict_mode or quality_auto_repair)
                and not guardrail_report.get("passed", True)
            ):
                if quality_auto_repair:
                    logger.info("\n🛡️  Guardrails: issues found — attempting auto-repair...")
                    try:
                        wr = research.get("web_research", {}) if isinstance(research, dict) else {}
                        web_sources = (wr.get("top_sources") or []) + (wr.get("results") or [])
                    except Exception:
                        web_sources = []
                    try:
                        fix_out = self.quality_fixer.run(
                            {
                                "article": content_md,
                                "guardrail_report": guardrail_report,
                                "web_sources": web_sources,
                            }
                        )
                        results["stages"]["quality_fixer"] = {
                            "changes_made": fix_out.data.get("changes_made", []),
                            "notes": fix_out.data.get("notes", ""),
                        }
                        content_md = fix_out.data.get("revised_article", content_md)
                    except Exception as e:
                        logger.warning(f"Auto-repair failed: {e}")
                        results["stages"]["quality_fixer"] = {"error": str(e)}

                    # Re-run checks after repair
                    guardrail_report = run_quality_guardrails(content_md).to_dict()
                    results["stages"]["guardrails"] = guardrail_report
                    ai_visibility = compute_ai_visibility_score(content_md) if ai_visibility_enable else ai_visibility
                else:
                    logger.info("\n🛡️  Guardrails: issues found (auto-repair disabled).")

            # ── Final packaging ─────────────────────────────────────────
            word_count = len((content_md or "").split())
            readability = analyze_readability(content_md)

            seo_check = compute_seo_score(content_md, keyword, title) if artifact_kind in LONGFORM_KINDS else {}

            jsonld_blocks = {}
            if ai_visibility_enable and ai_visibility_include_jsonld and artifact_kind in LONGFORM_KINDS:
                jsonld_blocks = build_jsonld(
                    article_md=content_md,
                    title=title,
                    brand_profile=brand_profile,
                    meta_description=(draft.get("meta_description") or seo_data.get("meta_description") or ""),
                )

            meta_title = (draft.get("meta_title") or seo_data.get("meta_title") or "").strip()
            meta_desc = (draft.get("meta_description") or seo_data.get("meta_description") or "").strip()

            results["final"] = {
                "artifact_kind": artifact_kind,
                "title": title,
                "meta_title": meta_title,
                "meta_description": meta_desc,
                "content": content_md,
                "word_count": word_count,
                "read_time_minutes": estimate_read_time(word_count),
                "seo_score": seo_check.get("total_score", 0) if seo_check else 0,
                "quality_score": results.get("stages", {}).get("editor", {}).get("quality_score", 0),
                "readability": readability,
                "guardrails": guardrail_report,
                "ai_visibility": ai_visibility,
                "jsonld": jsonld_blocks,
            }

            results["pipeline_elapsed_seconds"] = round(time.time() - pipeline_start, 1)

            if output_dir:
                self._save_outputs(output_dir, run_id, results)

            if self.store:
                self.store.save_run(run_id, keyword, results)

        except Exception as e:
            logger.error(f"Artifact pipeline failed: {e}", exc_info=True)
            results["error"] = str(e)
            results["status"] = "failed"

        return results

    def _save_outputs(self, output_dir: Path, run_id: str, results: dict[str, Any]) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        final = results.get("final", {}) or {}
        title = final.get("title", "SEO Artifact")
        content = final.get("content", "")
        artifact_kind = results.get("artifact_kind", "artifact")

        # Primary output (stable name for web downloads)
        primary_path = output_dir / f"{run_id}_primary.md"
        primary_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")

        # Friendly artifact filename
        kind_path = output_dir / f"{run_id}_{artifact_kind}.md"
        kind_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")

        # Save full results as JSON (prune large web extracts)
        results_path = output_dir / f"{run_id}_results.json"
        results_copy = json.loads(json.dumps(results, default=str))
        if "final" in results_copy:
            if "content" in results_copy["final"]:
                results_copy["final"]["content"] = f"[See {run_id}_primary.md]"
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
        results_path.write_text(json.dumps(results_copy, indent=2, default=str), encoding="utf-8")

        # Save SEO metadata
        meta_path = output_dir / f"{run_id}_seo_meta.json"
        meta = {
            "title": title,
            "meta_title": final.get("meta_title", ""),
            "meta_description": final.get("meta_description", ""),
            "keyword": results.get("keyword", ""),
            "artifact_kind": artifact_kind,
            "word_count": final.get("word_count", 0),
            "seo_score": final.get("seo_score", 0),
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # Save quality guardrails report
        q_path = output_dir / f"{run_id}_quality_report.json"
        q_path.write_text(json.dumps(final.get("guardrails", {}), indent=2, default=str), encoding="utf-8")

        # Save AI visibility pack
        v_path = output_dir / f"{run_id}_ai_visibility.json"
        v_path.write_text(json.dumps(final.get("ai_visibility", {}), indent=2, default=str), encoding="utf-8")

        # Save JSON-LD schemas (if present)
        jsonld = final.get("jsonld", {}) or {}
        if isinstance(jsonld, dict) and jsonld:
            if jsonld.get("article_jsonld"):
                a_path = output_dir / f"{run_id}_article.schema.jsonld"
                a_path.write_text(jsonld["article_jsonld"], encoding="utf-8")
            if jsonld.get("faq_jsonld"):
                f_path = output_dir / f"{run_id}_faq.schema.jsonld"
                f_path.write_text(jsonld["faq_jsonld"], encoding="utf-8")

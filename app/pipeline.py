"""Main pipeline module — high-level API for BriefEngine."""

from pathlib import Path
from typing import Any

from app.config import OUTPUT_DIR
from app.storage.store import RunStore
from app.workflows.article_workflow import ArticleWorkflow
from app.workflows.artifact_workflow import ArtifactWorkflow


class BriefEnginePipeline:
    """High-level API for running BriefEngine workflows."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.store = RunStore()
        self.article_workflow = ArticleWorkflow(store=self.store)
        self.artifact_workflow = ArtifactWorkflow(store=self.store)

    def generate_article(
        self,
        keyword: str,
        brand_profile: dict[str, Any],
        article_type: str = "comprehensive guide",
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.article_workflow.run(
            keyword=keyword,
            brand_profile=brand_profile,
            article_type=article_type,
            output_dir=self.output_dir,
            options=options,
        )

    def generate_artifact(
        self,
        *,
        keyword: str,
        brand_profile: dict[str, Any],
        artifact_kind: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.artifact_workflow.run(
            keyword=keyword,
            brand_profile=brand_profile,
            artifact_kind=artifact_kind,
            output_dir=self.output_dir,
            options=options,
        )

    def list_recent_runs(self, limit: int = 10) -> list[dict]:
        return self.store.list_runs(limit=limit)

    def get_run(self, run_id: str) -> dict | None:
        return self.store.get_run(run_id)

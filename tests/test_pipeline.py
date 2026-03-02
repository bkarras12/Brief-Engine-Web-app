"""Integration tests for BriefEngine pipeline and storage."""

import json
import os
import tempfile
import pytest
from pathlib import Path

from app.storage.store import RunStore


class TestRunStore:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test.db")
        self.store = RunStore(db_path=self.db_path)

    def test_save_and_get_run(self):
        self.store.save_run("run_001", "test keyword", {
            "final": {"word_count": 1500},
            "status": "completed",
        })
        run = self.store.get_run("run_001")
        assert run is not None
        assert run["keyword"] == "test keyword"
        assert run["status"] == "completed"

    def test_list_runs(self):
        self.store.save_run("run_001", "keyword1", {})
        self.store.save_run("run_002", "keyword2", {})
        runs = self.store.list_runs()
        assert len(runs) == 2

    def test_save_artifact(self):
        artifact_id = self.store.save_artifact(
            "run_001", "article", "# Test Article",
            metadata={"word_count": 100},
        )
        assert artifact_id > 0

    def test_get_artifacts(self):
        self.store.save_artifact("run_001", "article", "# Test")
        self.store.save_artifact("run_001", "outline", '{"sections": []}')
        artifacts = self.store.get_artifacts("run_001")
        assert len(artifacts) == 2

    def test_get_nonexistent_run(self):
        assert self.store.get_run("nonexistent") is None

    def test_save_failed_run(self):
        self.store.save_run("run_err", "fail keyword", {
            "error": "API timeout",
        })
        run = self.store.get_run("run_err")
        assert run["status"] == "failed"


class TestPipelineStructure:
    """Tests that verify the pipeline structure is correct without making API calls."""

    def test_imports(self):
        """Verify all modules can be imported."""
        from app.agents import (
            CEOAgent, ResearchAgent, OutlineAgent,
            WriterAgent, SEOAgent, EditorAgent, ProfileAgent,
        )
        from app.workflows import ArticleWorkflow
        from app.pipeline import BriefEnginePipeline
        from app.tools.keyword_tools import count_keyword_occurrences
        from app.tools.seo_tools import compute_seo_score
        from app.tools.writing_tools import analyze_readability

    def test_agent_configs_exist(self):
        from app.config import AGENT_CONFIGS
        required_keys = ["ceo", "research", "outline", "writer", "seo", "editor", "profile"]
        for key in required_keys:
            assert key in AGENT_CONFIGS, f"Missing config for agent: {key}"

    def test_agent_configs_have_required_fields(self):
        from app.config import AGENT_CONFIGS
        for name, cfg in AGENT_CONFIGS.items():
            assert "model" in cfg, f"{name} missing 'model'"
            assert "temperature" in cfg, f"{name} missing 'temperature'"
            assert "max_tokens" in cfg, f"{name} missing 'max_tokens'"

    def test_pipeline_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "test_outputs"
            from app.pipeline import BriefEnginePipeline
            pipeline = BriefEnginePipeline(output_dir=output_dir)
            assert pipeline.output_dir == output_dir

"""Tests for BriefEngine agents — uses mocked LLM calls."""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.agents.base import BaseAgent, AgentOutput
from app.agents.ceo_agent import CEOAgent
from app.agents.research_agent import ResearchAgent
from app.agents.outline_agent import OutlineAgent


class TestBaseAgent:
    def test_agent_output_model(self):
        output = AgentOutput(
            agent_name="test",
            status="success",
            data={"key": "value"},
        )
        assert output.agent_name == "test"
        assert output.status == "success"


class TestCEOAgent:
    @patch.object(CEOAgent, "invoke_json")
    def test_run_returns_content_plan(self, mock_invoke):
        mock_invoke.return_value = {
            "article_angle": "Test angle",
            "target_audience": "Developers",
            "search_intent": "informational",
            "content_goals": ["Goal 1"],
            "outline_requirements": {
                "min_sections": 5,
                "max_sections": 8,
                "must_include": ["testing"],
                "tone": "professional",
            },
            "quality_criteria": {
                "min_word_count": 1500,
                "target_word_count": 2000,
            },
        }

        agent = CEOAgent()
        result = agent.run({
            "brand_profile": {"company_name": "TestCo"},
            "keyword": "unit testing",
            "article_type": "guide",
        })

        assert result.status == "success"
        assert result.data["article_angle"] == "Test angle"

    def test_fallback_plan(self):
        agent = CEOAgent()
        plan = agent._fallback_plan(
            "test keyword",
            {"target_audience": "developers"},
            "guide",
        )
        assert plan["article_angle"] is not None
        assert len(plan["content_goals"]) > 0


class TestResearchAgent:
    @patch.object(ResearchAgent, "invoke_json")
    def test_run_returns_research(self, mock_invoke):
        mock_invoke.return_value = {
            "primary_keyword": "test keyword",
            "search_intent": "informational",
            "related_keywords": ["kw1", "kw2", "kw3", "kw4"],
            "long_tail_variations": ["variation1"],
            "questions_people_ask": ["Q1?", "Q2?", "Q3?"],
            "topic_clusters": [],
            "key_facts_and_stats": [],
            "content_gaps": [],
            "recommended_angle": "Test",
            "estimated_difficulty": "medium",
        }

        agent = ResearchAgent()
        result = agent.run({
            "keyword": "test keyword",
            "industry": "tech",
            "target_audience": "developers",
        })

        assert result.status == "success"
        assert len(result.data["related_keywords"]) >= 3

    def test_quality_gate(self):
        agent = ResearchAgent()
        assert agent.quality_gate({
            "related_keywords": ["a", "b", "c"],
            "questions_people_ask": ["q1", "q2", "q3"],
        }) is True
        assert agent.quality_gate({
            "related_keywords": ["a"],
            "questions_people_ask": ["q1"],
        }) is False

    def test_fallback_research(self):
        agent = ResearchAgent()
        result = agent._fallback_research("test keyword", "tech")
        assert result["primary_keyword"] == "test keyword"
        assert len(result["related_keywords"]) >= 3


class TestOutlineAgent:
    def test_quality_gate(self):
        agent = OutlineAgent()
        assert agent.quality_gate({"sections": [1, 2, 3, 4, 5]}) is True
        assert agent.quality_gate({"sections": [1]}) is False
        assert agent.quality_gate({"sections": list(range(15))}) is False

    def test_fallback_outline(self):
        agent = OutlineAgent()
        result = agent._fallback_outline("test keyword", {
            "questions_people_ask": ["Q1?", "Q2?"],
            "related_keywords": ["kw1", "kw2"],
            "long_tail_variations": ["var1"],
        })
        assert len(result["sections"]) >= 3
        assert result["recommended_title"] is not None

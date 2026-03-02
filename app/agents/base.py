"""Base agent with common functionality for all BriefEngine agents."""

import json
import logging
import time
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.config import OPENAI_API_KEY, AGENT_CONFIGS, MAX_RETRIES

logger = logging.getLogger("briefengine")


class AgentOutput(BaseModel):
    """Standard output wrapper for all agents."""
    agent_name: str
    status: str  # "success" | "error" | "retry"
    data: dict[str, Any]
    tokens_used: int = 0
    elapsed_seconds: float = 0.0


class BaseAgent:
    """Base class for all BriefEngine agents.

    Each agent has:
    - A role and system prompt
    - A configured LLM
    - Retry logic
    - Structured output parsing
    - Quality gate (override in subclass)
    """

    name: str = "base"
    role: str = "Assistant"
    goal: str = "Help with tasks"
    config_key: str = "ceo"  # key into AGENT_CONFIGS

    def __init__(self):
        cfg = AGENT_CONFIGS.get(self.config_key, AGENT_CONFIGS["ceo"])
        self.llm = ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            api_key=OPENAI_API_KEY,
        )
        self.max_retries = MAX_RETRIES

    @property
    def system_prompt(self) -> str:
        """Override in subclasses for specific system prompts."""
        return f"You are {self.role}. Your goal: {self.goal}"

    def invoke(self, user_prompt: str, system_override: str | None = None) -> str:
        """Call the LLM with retry logic. Returns raw text response."""
        messages = [
            SystemMessage(content=system_override or self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        for attempt in range(1, self.max_retries + 1):
            try:
                start = time.time()
                response = self.llm.invoke(messages)
                elapsed = time.time() - start
                logger.info(
                    f"[{self.name}] Success in {elapsed:.1f}s "
                    f"(attempt {attempt}/{self.max_retries})"
                )
                return response.content
            except Exception as e:
                logger.warning(
                    f"[{self.name}] Attempt {attempt} failed: {e}"
                )
                if attempt == self.max_retries:
                    raise
                time.sleep(2 ** attempt)  # exponential backoff

        return ""  # unreachable but satisfies type checker

    def invoke_json(self, user_prompt: str, system_override: str | None = None) -> dict:
        """Call LLM and parse response as JSON."""
        raw = self.invoke(user_prompt, system_override)
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error(f"[{self.name}] Failed to parse JSON: {cleaned[:200]}...")
            return {"raw_response": raw, "parse_error": True}

    def run(self, inputs: dict[str, Any]) -> AgentOutput:
        """Main entry point. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")

    def quality_gate(self, output: dict[str, Any]) -> bool:
        """Check if output meets quality standards. Override in subclasses."""
        return True

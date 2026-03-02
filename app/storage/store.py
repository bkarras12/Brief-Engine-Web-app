"""SQLite-backed storage for pipeline runs and outputs."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from app.config import DATABASE_PATH


class RunStore:
    """Simple SQLite storage for tracking pipeline runs."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = str(db_path or DATABASE_PATH)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    results_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                )
            """)
            conn.commit()

    def save_run(self, run_id: str, keyword: str, results: dict[str, Any]) -> None:
        """Save or update a pipeline run."""
        now = time.time()
        status = "failed" if results.get("error") else "completed"
        results_json = json.dumps(results, default=str)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO runs
                (run_id, keyword, status, created_at, completed_at, results_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run_id, keyword, status, now, now, results_json))
            conn.commit()

    def save_artifact(
        self,
        run_id: str,
        artifact_type: str,
        content: str,
        metadata: dict | None = None,
    ) -> int:
        """Save a pipeline artifact (article, outline, etc.)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO artifacts (run_id, artifact_type, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                artifact_type,
                content,
                json.dumps(metadata or {}),
                time.time(),
            ))
            conn.commit()
            return cursor.lastrowid or 0

    def get_run(self, run_id: str) -> dict | None:
        """Get a run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if row:
                result = dict(row)
                if result.get("results_json"):
                    result["results"] = json.loads(result["results_json"])
                return result
        return None

    def list_runs(self, limit: int = 20) -> list[dict]:
        """List recent runs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT run_id, keyword, status, created_at FROM runs "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_artifacts(self, run_id: str) -> list[dict]:
        """Get all artifacts for a run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at",
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]

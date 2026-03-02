"""BriefEngine Web App (FastAPI).

Run:
  uvicorn app.webapp.main:app --reload
or:
  python -m app.webapp.main
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.pipeline import BriefEnginePipeline
from app.config import (
    OUTPUT_DIR,
    ENABLE_WEB_RESEARCH,
    QUALITY_AUTO_REPAIR,
    AI_VISIBILITY_ENABLE,
    AI_VISIBILITY_INCLUDE_JSONLD,
)
from app.storage.store import RunStore

APP_ROOT = Path(__file__).resolve().parent

app = FastAPI(title="BriefEngine Web App", version="0.1.0")
templates = Jinja2Templates(directory=str(APP_ROOT / "templates"))
app.mount("/static", StaticFiles(directory=str(APP_ROOT / "static")), name="static")

pipeline = BriefEnginePipeline()
store = RunStore()

# In-memory job tracker (good for local use)
JOBS: dict[str, dict[str, Any]] = {}
LOCK = threading.Lock()

ALLOWED_DOWNLOADS = {
    "primary": "{run_id}_primary.md",
    "article": "{run_id}_article.md",
    "results": "{run_id}_results.json",
    "seo_meta": "{run_id}_seo_meta.json",
    "quality_report": "{run_id}_quality_report.json",
    "ai_visibility": "{run_id}_ai_visibility.json",
    "schema_article": "{run_id}_article.schema.jsonld",
    "schema_faq": "{run_id}_faq.schema.jsonld",
}


@dataclass
class Defaults:
    enable_web_research: bool
    quality_auto_repair: bool
    ai_visibility_enable: bool
    ai_visibility_include_jsonld: bool


def _human_time(ts: float | None) -> str:
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _parse_brand_profile(
    company_name: str | None,
    industry: str | None,
    target_audience: str | None,
    voice: str | None,
    notes: str | None,
    brand_profile_json: str | None,
) -> dict[str, Any]:
    # JSON wins if provided
    if brand_profile_json and brand_profile_json.strip():
        try:
            obj = json.loads(brand_profile_json)
            if isinstance(obj, dict):
                return obj
        except Exception:
            # fall back to fields
            pass

    profile = {
        "company_name": (company_name or "").strip() or "Your Company",
        "industry": (industry or "").strip() or "general",
        "target_audience": (target_audience or "").strip() or "general audience",
        "voice": (voice or "").strip() or "clear, helpful, practical",
    }
    if notes and notes.strip():
        profile["notes"] = notes.strip()
    return profile


def _spawn_job(job_id: str, *, keyword: str, brand_profile: dict[str, Any], artifact_kind: str, article_type: str, options: dict[str, Any]) -> None:
    def _run():
        start = time.time()
        with LOCK:
            JOBS[job_id] = {"status": "running", "started_at": start, "message": "Pipeline started…"}
        try:
            if artifact_kind == "article":
                result = pipeline.generate_article(
                    keyword=keyword,
                    brand_profile=brand_profile,
                    article_type=article_type,
                    options=options,
                )
            else:
                result = pipeline.generate_artifact(
                    keyword=keyword,
                    brand_profile=brand_profile,
                    artifact_kind=artifact_kind,
                    options=options,
                )
            # If the pipeline returned an error, treat as failed (it may catch exceptions internally)
            if result.get("error") or result.get("status") == "failed":
                with LOCK:
                    JOBS[job_id] = {
                        "status": "failed",
                        "started_at": start,
                        "finished_at": time.time(),
                        "run_id": result.get("run_id"),
                        "error": result.get("error") or "Pipeline failed",
                        "result": result,
                    }
            else:
                with LOCK:
                    JOBS[job_id] = {
                        "status": "completed",
                        "started_at": start,
                        "finished_at": time.time(),
                        "run_id": result.get("run_id"),
                        "result": result,
                    }
        except Exception as e:
            with LOCK:
                JOBS[job_id] = {
                    "status": "failed",
                    "started_at": start,
                    "finished_at": time.time(),
                    "error": str(e),
                }

    t = threading.Thread(target=_run, daemon=True)
    t.start()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    defaults = Defaults(
        enable_web_research=bool(ENABLE_WEB_RESEARCH),
        quality_auto_repair=bool(QUALITY_AUTO_REPAIR),
        ai_visibility_enable=bool(AI_VISIBILITY_ENABLE),
        ai_visibility_include_jsonld=bool(AI_VISIBILITY_INCLUDE_JSONLD),
    )
    return templates.TemplateResponse("index.html", {"request": request, "defaults": defaults, "title": "Generate"})


@app.post("/generate")
def generate(
    request: Request,
    keyword: str = Form(...),
    artifact_kind: str = Form("article"),
    article_type: str = Form("comprehensive guide"),
    company_name: str = Form(""),
    industry: str = Form(""),
    target_audience: str = Form(""),
    voice: str = Form(""),
    notes: str = Form(""),
    brand_profile_json: str = Form(""),
    enable_web_research: str | None = Form(None),
    quality_auto_repair: str | None = Form(None),
    ai_visibility_enable: str | None = Form(None),
    ai_visibility_include_jsonld: str | None = Form(None),
):
    brand_profile = _parse_brand_profile(
        company_name=company_name,
        industry=industry,
        target_audience=target_audience,
        voice=voice,
        notes=notes,
        brand_profile_json=brand_profile_json,
    )

    options = {
        "enable_web_research": bool(enable_web_research),
        "quality_auto_repair": bool(quality_auto_repair),
        "ai_visibility_enable": bool(ai_visibility_enable),
        "ai_visibility_include_jsonld": bool(ai_visibility_include_jsonld),
    }

    job_id = uuid.uuid4().hex[:12]
    _spawn_job(
        job_id,
        keyword=keyword.strip(),
        brand_profile=brand_profile,
        artifact_kind=(artifact_kind or "article").strip(),
        article_type=article_type,
        options=options,
    )
    return RedirectResponse(url=f"/job/{job_id}", status_code=303)


@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_page(job_id: str, request: Request):
    return templates.TemplateResponse("job.html", {"request": request, "job_id": job_id, "title": "Running"})


@app.get("/api/job/{job_id}")
def job_status(job_id: str):
    with LOCK:
        j = JOBS.get(job_id)
    if not j:
        return JSONResponse({"status": "missing", "error": "Unknown job id"}, status_code=404)

    # small status payload
    payload = {
        "status": j.get("status"),
        "message": j.get("message", ""),
        "run_id": j.get("run_id"),
        "started_at": j.get("started_at"),
        "finished_at": j.get("finished_at"),
        "error": j.get("error"),
    }
    return JSONResponse(payload)


@app.get("/result/{job_id}", response_class=HTMLResponse)
def result_page(job_id: str, request: Request):
    with LOCK:
        j = JOBS.get(job_id)

    if not j:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Unknown job id."}, status_code=404)

    if j.get("status") == "failed":
        return templates.TemplateResponse("error.html", {"request": request, "message": j.get("error", "Failed.")}, status_code=500)

    if j.get("status") != "completed":
        return RedirectResponse(url=f"/job/{job_id}", status_code=303)

    result = j.get("result") or {}
    return templates.TemplateResponse("result.html", {"request": request, "result": result, "title": "Result"})


@app.get("/download/{run_id}/{artifact}")
def download(run_id: str, artifact: str):
    # Basic path safety
    if not run_id.startswith("run_"):
        return JSONResponse({"error": "Invalid run_id"}, status_code=400)

    template = ALLOWED_DOWNLOADS.get(artifact)
    if not template:
        return JSONResponse({"error": "Unknown artifact"}, status_code=404)

    filename = template.format(run_id=run_id)
    path = Path(OUTPUT_DIR) / filename
    if not path.exists():
        return JSONResponse({"error": f"File not found: {filename}"}, status_code=404)

    return FileResponse(str(path), filename=filename)


@app.get("/runs", response_class=HTMLResponse)
def runs_page(request: Request):
    runs = store.list_runs(limit=25)
    # add human timestamps
    for r in runs:
        r["created_at_human"] = _human_time(r.get("created_at"))
    return templates.TemplateResponse("runs.html", {"request": request, "runs": runs, "title": "Recent runs"})


@app.get("/run/{run_id}", response_class=HTMLResponse)
def run_detail(run_id: str, request: Request):
    run = store.get_run(run_id)
    if not run:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Run not found."}, status_code=404)
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run, "title": run_id})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.webapp.main:app", host="127.0.0.1", port=8000, reload=False)

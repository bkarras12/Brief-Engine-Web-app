# BriefEngine - AI Content Pipeline for SMBs

> A multi-agent AI system that produces publish-ready, SEO-optimized blog articles for e-commerce and SaaS businesses. Powered by LangChain + OpenAI.

---

## 1. Executive Summary

**BriefEngine** is an AI-native content agency packaged as software. You configure it once with a client's brand voice, target keywords, and audience - then it produces publish-ready SEO blog articles through a coordinated team of 7 AI agents.

**Why this business:**
- Content marketing agencies charge $2,000–$20,000/month (avg ~$3,200/mo for SEO content)
- SMBs need 4–12 blog posts/month but can't afford agencies or dedicate staff time
- Existing AI tools (Jasper, Copy.ai) are *writing assistants* - they require constant human input
- BriefEngine is a *configured pipeline*: input keywords → output publish-ready articles

**Target price:** $149/mo (4 articles), $299/mo (8 articles), $499/mo (16 articles)

---

## 2. Market Research

### Market Size
- AI-powered content creation market: ~$2.15B in 2024, projected $10.6B by 2033 (CAGR 19.4%) - Grand View Research
- AI content generation market growing at 27.3% CAGR to $9.2B by 2031 - Valuates Reports
- SEO agency retainers average $3,200/mo in 2025 - Digital Agency Network

### Target Customer
- **Primary:** E-commerce store owners (Shopify, WooCommerce) with 10–500 products
- **Secondary:** Early-stage SaaS companies (pre-Series A) without a content team
- **Tertiary:** Marketing agencies looking to scale output without hiring

### Pain Points
1. Hiring freelance writers costs $100–$500/article with inconsistent quality
2. SEO requires keyword research + optimization expertise most owners lack
3. Content consistency (voice, schedule) is hard to maintain manually
4. Existing AI tools still require significant prompt engineering and editing

### Competitive Landscape
| Competitor | Model | Price | Weakness |
|---|---|---|---|
| Jasper AI | Self-serve tool | $49–$125/mo | Requires user to do all the work |
| Copy.ai | Self-serve tool | $49/mo | Generic output, no SEO pipeline |
| SurferSEO | SEO optimizer | $89–$219/mo | Writing not included |
| Content at Scale | AI articles | $250+/mo | Black-box, no customization |
| Freelance writers | Service | $100–$500/article | Slow, inconsistent, expensive |

### Differentiation
BriefEngine is not a tool - it's a **configured AI content team**. The user provides brand context once, and the system autonomously researches, outlines, writes, optimizes, and delivers publish-ready articles. Think "Jasper + SurferSEO + a content strategist" in one automated pipeline.

---

## 3. Business Scoring (0–5 scale)

| Criterion | Score | Rationale |
|---|---|---|
| Pain severity & urgency | 4 | Content marketing is table-stakes but painful for SMBs |
| Clear buyer + budget owner | 5 | Store owner / marketing manager, already paying for content |
| Ease of distribution online | 5 | Shopify communities, indie hackers, Twitter, Product Hunt |
| Differentiation vs competitors | 4 | Pipeline vs tool; done-for-you vs DIY |
| Fast MVP feasibility (≤2 weeks) | 5 | Pure Python + LangChain, no complex infra |
| Retention potential | 5 | Monthly content need never stops |
| Low operational complexity | 4 | Automated, but needs quality monitoring |
| **TOTAL** | **32/35** | |

**Decision:** This scores highest across all criteria. The combination of clear buyer, recurring need, fast MVP, and pipeline-vs-tool differentiation makes this investable.

---

## 4. AI Ontology Mapping

```
Market: Digital Content Marketing
└── Segment: SMB Content Marketing ($2K–$20K/mo budget)
    ├── Persona: E-commerce Store Owner
    │   ├── JTBD: "Drive organic traffic to my store without hiring a content team"
    │   ├── Pain: Expensive freelancers, inconsistent quality, no SEO expertise
    │   └── Gain: Consistent, optimized content at 10% of agency cost
    └── Persona: SaaS Marketing Manager (early-stage)
        ├── JTBD: "Publish thought-leadership content to build authority and capture leads"
        ├── Pain: No bandwidth, writing is slow, SEO is a separate skill
        └── Gain: Weekly articles that rank, minimal input required

Product: BriefEngine
├── Feature: Brand Voice Configuration → Workflow: Onboarding → Agent: ProfileAgent
├── Feature: Keyword Research → Workflow: Research → Agent: ResearchAgent
├── Feature: Content Outlining → Workflow: Planning → Agent: OutlineAgent
├── Feature: Long-form Writing → Workflow: Drafting → Agent: WriterAgent
├── Feature: SEO Optimization → Workflow: Optimization → Agent: SEOAgent
├── Feature: Editorial Review → Workflow: Quality → Agent: EditorAgent
└── Feature: Pipeline Orchestration → Workflow: Coordination → Agent: CEOAgent

Agents → Tools:
├── ResearchAgent → [web_search, keyword_analyzer]
├── OutlineAgent → [content_planner]
├── WriterAgent → [long_form_writer]
├── SEOAgent → [seo_scorer, meta_generator]
├── EditorAgent → [grammar_checker, readability_scorer, fact_checker]
├── ProfileAgent → [brand_voice_extractor]
└── CEOAgent → [task_decomposer, quality_gate]

Artifacts (what customers pay for):
├── SEO-optimized blog article (1,500–2,500 words)
├── Meta title + description
├── Internal linking suggestions
├── Content brief (outline + research notes)
└── SEO score report
```

---

## 5. Setup & Installation

### Prerequisites
- Python 3.10+
- OpenAI API key

### Install
```bash
cd briefengine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Run the Demo
```bash
python -m app.run_demo
```

This will:
1. Load a sample client profile (fictional e-commerce brand)
2. Take a target keyword ("best running shoes for flat feet")
3. Run the full 7-agent pipeline
4. Output a publish-ready article + SEO metadata to `outputs/`



### Run the Web App
```bash
uvicorn app.webapp.main:app --reload
# then open http://127.0.0.1:8000 in your browser
```

In the web app you can:
- enter a keyword/topic and brand info
- toggle web research / auto-repair / AI visibility per run
- generate and download outputs from the browser
- view recent runs saved in the local SQLite database


### New: Live Research + Quality Guardrails + AI Visibility (Optional)

BriefEngine can now pull **live web sources** (DuckDuckGo-based) to support citations.

To enable:
- Set `ENABLE_WEB_RESEARCH=1` in your `.env`

Quality & AI visibility features run automatically:
- **Quality guardrails** produce a report and can auto-repair missing sections/citations
- **AI visibility** produces a readiness score and generates JSON-LD schemas (Article + FAQ)

New output files per run:
- `{run_id}_quality_report.json`
- `{run_id}_ai_visibility.json`
- `{run_id}_article.schema.jsonld` (if enabled)
- `{run_id}_faq.schema.jsonld` (if enabled)

### Run Tests
```bash
python -m pytest tests/ -v
```

---

## 6. Project Structure

```
briefengine/
├── app/
│   ├── __init__.py
│   ├── config.py              # Settings, env vars, model configs
│   ├── run_demo.py            # Single-command demo entry point
│   ├── pipeline.py            # Main orchestration pipeline
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py            # Base agent class
│   │   ├── ceo_agent.py       # CEO/Planner - decomposes & coordinates
│   │   ├── research_agent.py  # Keyword & topic research
│   │   ├── outline_agent.py   # Content outline generation
│   │   ├── writer_agent.py    # Long-form article drafting
│   │   ├── seo_agent.py       # SEO optimization & scoring
│   │   ├── editor_agent.py    # Quality review & editing
│   │   └── profile_agent.py   # Brand voice & audience profiling
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── keyword_tools.py   # Keyword analysis utilities
│   │   ├── seo_tools.py       # SEO scoring & meta generation
│   │   ├── writing_tools.py   # Readability & grammar helpers
│   │   └── search_tools.py    # Web search integration
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── article_workflow.py # End-to-end article generation
│   └── storage/
│       ├── __init__.py
│       └── store.py           # SQLite storage for runs & outputs
├── tests/
│   ├── __init__.py
│   ├── test_agents.py         # Agent unit tests
│   ├── test_pipeline.py       # Integration test
│   └── test_tools.py          # Tool unit tests
├── examples/
│   ├── sample_output.json     # Example full pipeline output
│   └── sample_article.md      # Example generated article
├── docs/
│   └── go_to_market.md        # 30-day GTM plan
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 7. How to Configure Agents

Each agent is configured in `app/config.py`. You can adjust:

```python
AGENT_CONFIGS = {
    "ceo": {"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 2000},
    "research": {"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 3000},
    "outline": {"model": "gpt-4o-mini", "temperature": 0.4, "max_tokens": 2000},
    "writer": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 8000},
    "seo": {"model": "gpt-4o-mini", "temperature": 0.2, "max_tokens": 2000},
    "editor": {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 8000},
    "profile": {"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 2000},
}
```

**Model selection guidance:**
- Use `gpt-4o` for writing and editing (quality matters)
- Use `gpt-4o-mini` for research, outlining, SEO (cost efficiency)
- Adjust `temperature` for creativity vs consistency tradeoff

---

## 8. How to Add New Workflows

1. Create a new file in `app/workflows/`:

```python
# app/workflows/social_workflow.py
from app.agents import WriterAgent, SEOAgent
from app.workflows import BaseWorkflow

class SocialPostWorkflow(BaseWorkflow):
    def run(self, article_content: str, platforms: list[str]) -> dict:
        # Repurpose article into social posts
        ...
```

2. Register it in `app/pipeline.py`
3. Add tests in `tests/`

---

## 9. Next Steps Roadmap

### Week 1–2: MVP Launch
- [ ] Run demo end-to-end, verify output quality
- [ ] Set up a simple landing page (Carrd.co or similar, $19)
- [ ] Create 3 sample articles for different niches as portfolio
- [ ] Set up Stripe for payments

### Week 3–4: First Customers
- [ ] Post on Indie Hackers, r/Entrepreneur, relevant Shopify communities
- [ ] Cold DM 50 Shopify store owners on Twitter/LinkedIn
- [ ] Offer 1 free article as a trial
- [ ] Collect feedback, iterate on quality

### Month 2: Scale
- [ ] Add WordPress/Shopify auto-publishing integration
- [ ] Build a simple dashboard (Streamlit or similar)
- [ ] Add social media repurposing workflow
- [ ] Target 10 paying customers at $149/mo = $1,490 MRR

### Month 3+: Growth
- [ ] Add content calendar + scheduling
- [ ] Build referral program
- [ ] Launch on Product Hunt
- [ ] Consider agency partnership program

---

## License

MIT - use it, extend it, sell it.

# BriefEngine — 30-Day Go-to-Market Plan

## North Star Metric
**Monthly Recurring Revenue (MRR)** — target: $500+ by Day 30

## Leading Indicators
- Landing page visitors → trial signups (target: 5% conversion)
- Trial → paid conversion (target: 30%)
- Customer satisfaction score (target: 8+/10 on article quality)
- Articles generated per customer per month (target: 4+)

---

## Pricing & Packaging

| Plan | Price | Articles/mo | Features |
|---|---|---|---|
| Starter | $99/mo | 4 articles | Core pipeline, 1 brand profile |
| Growth | $249/mo | 10 articles | + SEO reports, 3 brand profiles |
| Agency | $499/mo | 25 articles | + White label, unlimited profiles |

**Launch offer:** First article FREE (no card required). Then 50% off first month.

---

## Week 1: Foundation (Days 1–7)

### Day 1–2: Landing Page + Payment
- Set up landing page on Carrd.co ($19) or simple HTML on Vercel (free)
- Copy formula: Pain → Solution → How It Works → Sample Output → Pricing → CTA
- Embed Stripe checkout for payments ($0 to start)
- Include 2 sample articles as portfolio proof (from `examples/`)

### Day 3–4: Generate Portfolio Content
- Run BriefEngine on 5 different keywords across 3 niches:
  - E-commerce: "best [product] for [audience]" style
  - SaaS: "how to [solve problem] with [approach]" style
  - Local business: "[service] in [city]: what to know" style
- Polish outputs, publish as case studies on landing page

### Day 5–7: Distribution Setup
- Create accounts: Twitter/X, LinkedIn, Indie Hackers
- Write 3 Twitter threads about AI content generation (educational, not salesy)
- Post first article sample on Indie Hackers with build-in-public framing
- Join 5 Shopify/e-commerce communities (Facebook groups, Slack, Discord)

**Week 1 Target:** Landing page live, 3 sample articles published, social accounts active

---

## Week 2: First Outreach (Days 8–14)

### Primary Channel: Cold DMs (LinkedIn + Twitter)

**Target list:** 100 prospects total
- 50 Shopify store owners (find on Twitter by searching "Shopify store" + niche)
- 30 SaaS founders (Indie Hackers, Twitter)
- 20 marketing freelancers/agencies (LinkedIn)

**Outreach Script (DM):**

> Hey [Name], I noticed you're running [store/company] — looks great.
>
> Quick question: are you publishing blog content for SEO right now? I built an AI tool that produces full, publish-ready articles for about 1/10th the cost of freelance writers.
>
> Happy to generate a free sample article on any keyword you're targeting. No strings. Just want feedback from real store owners.
>
> Want me to give it a shot?

**Follow-up (Day 3 if no reply):**

> Hey [Name], just bumping this — the free article offer stands. I can have a draft in your inbox within 24 hours. Just send me a keyword you'd like to rank for.

### Secondary Channel: Community Posting
- Post build-in-public updates on Indie Hackers (2x/week)
- Share article samples in relevant subreddits (r/Entrepreneur, r/SEO, r/ecommerce)
- Engage genuinely in Shopify community discussions, mention tool when relevant

### Day 10: Process First Free Articles
- For anyone who responds, generate their free article within 24 hours
- Send article + SEO score report
- Ask for feedback + permission to use as case study
- Close with: "If you want more articles like this, plans start at $99/mo"

**Week 2 Target:** 100 DMs sent, 10+ conversations, 5+ free articles delivered

---

## Week 3: Convert & Iterate (Days 15–21)

### Convert Free Users
- Follow up with everyone who received a free article
- Offer 50% off first month ($49.50 for Starter)
- Create urgency: "This launch price is available for the first 10 customers"

### Iterate on Quality
- Collect all feedback from free article recipients
- Identify the top 3 quality issues
- Adjust agent prompts/configs to address them
- Re-run sample articles to verify improvement

### Expand Distribution
- Write and publish a long-form post: "How I Built an AI Content Team That Writes Better Than Most Freelancers" on Medium / LinkedIn
- Submit to Hacker News (Show HN: BriefEngine — AI content pipeline for SMBs)
- Cross-post to relevant newsletters via HARO or similar

### Launch Referral Mechanism
- Simple offer: "Refer a friend, get 1 free article" (manual tracking is fine at this stage)

**Week 3 Target:** 3+ paying customers, quality improvements shipped, 1 viral-potential post published

---

## Week 4: Scale What Works (Days 22–30)

### Double Down on Best Channel
- Whichever channel produced the most trials (DMs, community, or content), invest 80% of time there
- If DMs worked: send 50 more per day
- If community worked: post daily, become a known contributor
- If content worked: publish 3 more articles

### Formalize Onboarding
- Create a simple onboarding form (Google Form or Typeform):
  - Company name, website, industry
  - Brand voice description
  - Top 5 target keywords
  - Content goals
- Run ProfileAgent on their inputs to generate brand profile
- Deliver first article within 48 hours of signup

### Build Social Proof
- Ask paying customers for testimonials
- Create before/after comparison: "What they were paying vs. BriefEngine cost"
- Screenshot any positive feedback for landing page

### Prepare for Month 2
- If MRR > $300: invest in a custom domain + simple dashboard (Streamlit)
- If MRR > $500: consider Product Hunt launch
- Begin building email list for content marketing about BriefEngine itself

**Week 4 Target:** 5-10 paying customers, $500-$1,000 MRR, clear understanding of best acquisition channel

---

## Success Metrics Summary

| Metric | Day 7 | Day 14 | Day 21 | Day 30 |
|---|---|---|---|---|
| Landing page visitors | 50 | 200 | 500 | 1,000 |
| Free articles delivered | 0 | 5 | 12 | 20 |
| Paying customers | 0 | 0 | 3 | 5-10 |
| MRR | $0 | $0 | $150-$300 | $500-$1,000 |
| DMs sent | 0 | 100 | 150 | 200 |
| Community posts | 3 | 8 | 15 | 25 |

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Article quality too low | Iterate on prompts aggressively; offer free revisions |
| OpenAI costs too high per article | Use gpt-4o-mini for most agents; only gpt-4o for writer/editor |
| Low response rate on DMs | Test 3 different scripts; A/B test approach angles |
| Customers churn after 1 month | Add content calendar + SEO tracking to increase stickiness |
| Competitor launches similar tool | Focus on niche (e-commerce), build relationships, move fast |

---

## Estimated Costs (Month 1)

| Item | Cost |
|---|---|
| OpenAI API (50 articles @ ~$0.50-$1.50 each) | $25-$75 |
| Landing page (Carrd.co) | $19 |
| Domain name | $12 |
| Stripe fees (on revenue) | ~3% |
| **Total** | **~$60-$110** |

**Break-even:** 1 customer on Starter plan ($99/mo) covers all costs.

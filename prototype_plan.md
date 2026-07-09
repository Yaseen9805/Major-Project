# Build Spec: CostQual-Router — Comparison Prototype (for Claude Code)

## Goal

Build a SMALL, working prototype — NOT the full production system — that proves one thing clearly:

> Running the same set of questions through (A) a plain, no-optimization AI setup vs
> (B) an adaptive system with semantic caching + model routing produces a measurable
> improvement in speed and estimated cost, with no meaningful drop in answer quality.

This is a proof-of-concept for a professor pitch, not the final research project. Scope it small.
Target build time: 3-5 focused days. Prioritize a working end-to-end demo over completeness.

---

## Explicit scope boundaries

BUILD:
- A baseline query handler (Setup A): always calls one fixed model, no cache, no routing.
- An adaptive query handler (Setup B): semantic cache lookup + complexity-based routing across
  2-3 local model tiers.
- A benchmark runner that sends the same fixed test query set through both setups and logs
  metrics for each.
- A comparison report generator that outputs a table + simple charts (matplotlib is fine) and
  a short markdown summary.
- A minimal way to demo it live: either a simple CLI script with clear printed output, or a
  single-page Streamlit/HTML dashboard showing "ask a question" with a visible
  cache-hit/tier-used indicator. Pick whichever is faster to build well — do not over-engineer.

DO NOT BUILD YET (these belong to the full month-long project, not this prototype):
- Authentication / JWT
- CI/CD pipelines
- Kubernetes / Terraform / cloud deployment
- Prometheus/Grafana monitoring stack
- MLflow model registry
- Drift detection
- Multi-user support
- Docker is OPTIONAL here — only add it if it doesn't slow you down; a local Python venv is fine
  for this prototype.

---

## Tech stack for this prototype (keep it minimal)

- Python 3.11+
- FastAPI (or even a plain Python script — FastAPI only if you want a live demo endpoint)
- Ollama (local model serving) — pull these models:
  - qwen2.5:0.5b (tiny/fast tier)
  - phi3:mini (medium tier)
  - (optional) mistral:7b-instruct-q4_0 (large tier, only if hardware allows — skip if too slow)
- sentence-transformers (`all-MiniLM-L6-v2`) for embeddings
- A simple vector store — use an in-memory approach first (cosine similarity over a Python list/
  numpy array is enough for ~100-1000 cached entries). Only add Qdrant/FAISS if time allows;
  it is NOT required to prove the concept at this scale.
- SQLite (or even a JSON/CSV log file) to record query logs and metrics — no need for Postgres yet.
- matplotlib or plotly for the comparison chart
- pytest for a handful of basic unit tests (cache hit logic, routing logic) — 5-10 tests is enough

---

## Step-by-step build plan

### Step 1 — Environment setup
- Set up a Python virtual environment.
- Install and verify Ollama is running locally; pull qwen2.5:0.5b and phi3:mini.
- Quick sanity check: send one prompt to each model via Ollama's API and confirm you get a
  response and can measure latency.

### Step 2 — Baseline handler (Setup A)
- Write `baseline.py`: a function `ask_baseline(query: str) -> dict` that always calls ONE fixed
  model (use phi3:mini as the "always-use-this" baseline, since that's a reasonable
  middle-ground default a naive implementation would pick).
- Return: `{answer, latency_ms, tier_used="baseline", cache_hit=False, estimated_cost}`.
- `estimated_cost` can be a simple proxy: (input_tokens + output_tokens) * fixed weight per tier.
  Document your weight assumptions clearly in a comment/README.

### Step 3 — Embedding + semantic cache
- Write `cache.py`:
  - `embed(text: str) -> np.ndarray` using sentence-transformers.
  - An in-memory store: a list of `{query_embedding, query_text, answer, tier_used, timestamp}`.
  - `check_cache(query: str, threshold: float = 0.87) -> dict | None`: embed the query, compute
    cosine similarity against all stored embeddings, return the best match if similarity exceeds
    threshold, else None.
  - `add_to_cache(query, answer, tier_used)`: store a new entry.
  - Make the threshold a configurable parameter — you'll want to experiment with it later.

### Step 4 — Complexity classifier + router
- Write `router.py`:
  - Start RULE-BASED (do not build an ML classifier yet — not needed to prove the concept):
    - If query length < N words AND matches simple patterns (what is, define, calculate,
      yes/no question) → tier = "small" (qwen2.5:0.5b)
    - Else if query contains reasoning/explanation/multi-step keywords (explain, why, compare,
      analyze, write a, prove) OR is long → tier = "large" (phi3:mini, or mistral if enabled)
    - Else → tier = "medium"
  - `route(query: str) -> str` returns the tier/model name.
  - Keep this simple and readable — you will need to explain this logic clearly to your professor.

### Step 5 — Adaptive handler (Setup B)
- Write `adaptive.py`: a function `ask_adaptive(query: str) -> dict` that:
  1. Calls `check_cache(query)`. If hit: return cached answer immediately, `cache_hit=True`,
     `latency_ms` = the tiny embedding+lookup time only, `estimated_cost` = near-zero.
  2. If miss: call `route(query)` to pick a tier, call that model via Ollama, then
     `add_to_cache(...)`, and return the result with `cache_hit=False`.
- Return shape should match `ask_baseline` so results are directly comparable.

### Step 6 — Test query set
- Create `test_queries.json` (or .csv) with ~60 queries structured in labeled groups:
  - 15 exact duplicate pairs (i.e. ~7-8 unique questions each asked twice, back to back and
    also spaced apart in the list)
  - 15 paraphrase pairs (same intent, different wording)
  - 10 simple/easy questions
  - 10 complex/reasoning questions
  - 10 one-off unique questions (no repeats)
- Include a `category` field per query so the report can break down results by category.

### Step 7 — Benchmark runner
- Write `run_benchmark.py`:
  - Load `test_queries.json`.
  - For each query, run it through `ask_baseline` AND (in a separate, fresh-cache pass)
    `ask_adaptive`. Log every result (query, category, system, latency_ms, cache_hit, tier_used,
    estimated_cost) to a CSV or SQLite table.
  - IMPORTANT: run the adaptive system with a cold (empty) cache at the start of the benchmark,
    same as the baseline gets no warm-up — this keeps the comparison fair.

### Step 8 — Comparison report generator
- Write `generate_report.py`:
  - Read the logged results.
  - Compute and print/save:
    - Total and average latency: baseline vs adaptive
    - Total estimated cost: baseline vs adaptive
    - Cache hit rate (adaptive only), broken down by category (duplicates/paraphrases/unique)
    - Tier usage distribution (adaptive only) — % sent to small/medium/large
  - Generate 2 charts with matplotlib:
    1. Bar chart: total estimated cost, baseline vs adaptive
    2. Bar chart: average latency, baseline vs adaptive
  - Output a short markdown summary file `report.md` with the numbers and a one-paragraph
    plain-English interpretation (e.g. "Adaptive system reduced estimated cost by X% and average
    latency by Y%, with cache hits on Z% of duplicate/paraphrase queries").

### Step 9 — Simple quality sanity check (lightweight, not full BERTScore yet)
- For ~10 sampled queries where baseline and adaptive gave DIFFERENT answers (i.e. adaptive
  routed to a smaller model), manually or via a quick LLM-judge prompt (using the local model
  itself to compare) rate whether the adaptive answer is "acceptable" vs baseline. Log a simple
  pass/fail. This doesn't need to be rigorous yet — just enough to say "quality held up" in the
  demo. Full BERTScore evaluation belongs in the real 1-month project.

### Step 10 — Live demo mode
- Add a minimal way to demonstrate this interactively in front of the professor:
  - Simplest option: a CLI loop (`demo.py`) where you type a question and it prints:
    `[BASELINE] answer, Xms, cost=Y` then `[ADAPTIVE] answer, Xms, cost=Y, cache_hit=True/False,
    tier=Z`
  - Nice-to-have if time allows: a one-page Streamlit app with two side-by-side response boxes
    and a running tally of savings.
- Prepare a short scripted sequence to run live: ask a question, ask its paraphrase immediately
  after, show the cache hit and instant response.

### Step 11 — Basic tests
- Write 5-10 pytest tests covering:
  - Cache returns a hit for a near-duplicate query above threshold
  - Cache returns None for an unrelated query
  - Router correctly classifies a few example easy/hard queries
  - Baseline and adaptive handlers return matching result shapes

### Step 12 — README
- Write a clear `README.md`: what this is, how to run it (`ollama pull ...`, `pip install -r
  requirements.txt`, `python run_benchmark.py`, `python generate_report.py`), and what the
  results mean. Include the final chart images inline.

---

## Deliverables checklist

- [ ] `baseline.py`, `adaptive.py`, `cache.py`, `router.py`
- [ ] `test_queries.json` with ~60 labeled queries
- [ ] `run_benchmark.py` + logged results (CSV/SQLite)
- [ ] `generate_report.py` producing `report.md` + 2 chart images
- [ ] `demo.py` (or Streamlit app) for live demonstration
- [ ] `tests/` with 5-10 passing pytest tests
- [ ] `README.md`

## Success criteria

The prototype is done when you can run one command, get a report showing adaptive vs baseline
numbers on cost/latency/cache-hit-rate, and can live-demo one paraphrase-triggers-cache-hit
moment in under 2 minutes in front of your professor.

# LLM Output Fact-checker for insurance-claims data

A small, runnable framework for **extracting audit findings from unstructured claim files and verifying every
finding against the source document** - the core problem when LLMs summarise claims (leakage, litigation risk,
coverage issues, fraud indicators, late notice).

## What it does
1. `src/generate.py` - seeded generator of 60 synthetic commercial claim files (Property, GL, Marine Cargo) with
   planted, labelled issues. 
2. `src/extract.py` - pluggable extractors. Each finding must include a verbatim evidence quote.
   - `rules`: deterministic regex baseline to beat.
   - `noisy`: baseline plus simulated LLM failure modes (omissions, fabricated findings, paraphrased quotes, wrong
     amounts) to prove the evaluator catches them.
   - `llm`: real LLM via Anthropic or Azure OpenAI (`LLM_PROVIDER`, `LLM_MODEL`, API key env vars). Prompt included.
    
3. `src/evaluate.py` - grounding checks (quote must exist in source; cited amounts must exist in source) and
   precision/recall/F1 against ground truth, where only grounded findings earn credit.
4. `src/store.py` - SQLAlchemy persistence. SQLite by default, Postgres via `DATABASE_URL`.

## Run
```
pip install sqlalchemy pytest
python -m src.generate 60 7
python -m src.run --backend rules
python -m src.run --backend noisy
pytest -q
sqlite3 claims_eval.db "SELECT category, COUNT(*), SUM(1-grounded) FROM findings WHERE run_id=2 GROUP BY 1"
```

## Results (synthetic data, seed 7, 60 claims)
| backend | findings | ungrounded | hallucination rate | precision | recall | F1 |
|---|---|---|---|---|---|---|
| rules | 70 | 0 | 0.0% | 1.00 | 1.00 | 1.00 |
| noisy (simulated) | 72 | 13 | 18.1% | 1.00 | 0.84 | 0.91 |

The rules baseline scores 1.00 because the synthetic text was written with the same phrasing; that is a sanity
check, not a claim about real-world performance. The value is the harness: swap in `--backend llm` and the same
grounding and scoring apply. Next steps: real (public/redacted) claim PDFs, LLM-judge for rationale quality,
Azure deployment, and a human-labelled gold set.

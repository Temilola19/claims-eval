"""CLI: python -m src.run --backend rules|noisy|llm [--n 60]"""
import argparse, json, random
from pathlib import Path
from . import extract, evaluate, store

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--backend", default="rules"); ap.add_argument("--data", default="data")
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--db", default=None); a = ap.parse_args()
    d = Path(a.data); truth = json.loads((d / "ground_truth.json").read_text())
    docs = {p.stem: p.read_text() for p in sorted((d / "claims").glob("*.txt"))}
    rng = random.Random(a.seed)
    preds = {cid: extract.extract(doc, a.backend, rng) for cid, doc in docs.items()}
    metrics, records = evaluate.evaluate(docs, truth, preds)
    e = store.engine(a.db); run_id = store.save_run(e, a.backend, metrics, preds, records)
    print(f"run {run_id} backend={a.backend}")
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in metrics.items() if k != "per_category"}, indent=1))
    return metrics

if __name__ == "__main__": main()

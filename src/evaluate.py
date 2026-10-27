"""Evaluation framework: grounding (hallucination) checks + label accuracy against ground truth."""
import re

def _norm(s): return re.sub(r"\s+", " ", s.lower()).strip()

def grounding(finding, doc):
    """Returns list of failure reasons ([] = grounded)."""
    fails = []
    ev = finding.get("evidence", "")
    if not ev or _norm(ev) not in _norm(doc): fails.append("evidence_not_in_source")
    amt = finding.get("amount")
    if amt is not None:
        nums = {float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", doc)}
        if amt not in nums: fails.append("amount_not_in_source")
    return fails

def evaluate(docs, truth, preds):
    """docs/truth/preds keyed by claim_id. Returns metrics dict and per-finding grounding records."""
    tp = fp = fn = 0; per_cat = {}; records = []; n_find = n_ungrounded = 0
    for cid, doc in docs.items():
        g_true = set(truth[cid]); g_pred = set()
        for f in preds[cid]:
            fails = grounding(f, doc); n_find += 1
            records.append({"claim_id": cid, "category": f["category"], "grounded": not fails, "fail_reasons": fails})
            if fails: n_ungrounded += 1
            else: g_pred.add(f["category"])  # only grounded findings count as credit
        for c in set(g_true) | g_pred:
            d = per_cat.setdefault(c, [0, 0, 0])
            if c in g_true and c in g_pred: tp += 1; d[0] += 1
            elif c in g_pred: fp += 1; d[1] += 1
            else: fn += 1; d[2] += 1
    prec = tp / (tp + fp) if tp + fp else 0.0; rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"claims": len(docs), "findings": n_find, "ungrounded_findings": n_ungrounded,
            "hallucination_rate": n_ungrounded / n_find if n_find else 0.0,
            "precision": prec, "recall": rec, "f1": f1,
            "per_category": {c: {"tp": a, "fp": b, "fn": d} for c, (a, b, d) in per_cat.items()}}, records

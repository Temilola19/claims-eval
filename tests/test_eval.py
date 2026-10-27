import random
from src import generate, extract, evaluate

def _setup(n=60):
    rng = random.Random(7); cs = [generate.make_claim(i, rng) for i in range(1, n + 1)]
    return {c["claim_id"]: c["text"] for c in cs}, {c["claim_id"]: c["labels"] for c in cs}

def test_rules_baseline_is_clean():
    docs, truth = _setup(); preds = {k: extract.rules_extract(v) for k, v in docs.items()}
    m, _ = evaluate.evaluate(docs, truth, preds)
    assert m["hallucination_rate"] == 0 and m["f1"] > 0.95

def test_evaluator_catches_every_injected_fabrication():
    docs, truth = _setup(); rng = random.Random(3); caught = total = 0
    for k, v in docs.items():
        fab = {"category": "fraud", "evidence": "Insured admitted the loss was intentionally caused.", "amount": None}
        total += 1; caught += bool(evaluate.grounding(fab, v))
    assert caught == total

def test_wrong_amount_and_paraphrase_flagged():
    doc = "- Payments to date of $90,000 exceed the carried reserve of $60,000."
    assert "amount_not_in_source" in evaluate.grounding({"evidence": "Payments to date of $90,000 exceed", "amount": 99000.0}, doc)
    assert "evidence_not_in_source" in evaluate.grounding({"evidence": "Payments were above reserve", "amount": 90000.0}, doc)

def test_noisy_backend_has_nonzero_hallucination_rate():
    docs, truth = _setup(); rng = random.Random(1)
    preds = {k: extract.noisy_extract(v, rng) for k, v in docs.items()}
    m, _ = evaluate.evaluate(docs, truth, preds)
    assert m["hallucination_rate"] > 0

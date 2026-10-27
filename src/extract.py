"""Pluggable finding extractors. Every finding must carry a verbatim evidence quote.

Backends
  rules  - deterministic regex baseline (the benchmark any LLM pipeline must beat)
  noisy  - rules + injected failure modes, to test that the evaluator catches hallucinations
  llm    - real LLM via Anthropic or Azure OpenAI (needs API key; not run in the offline demo)
"""
import json, os, random, re

CATEGORIES = ["late_notice", "leakage", "litigation", "coverage", "fraud"]
PROMPT = """You are a commercial insurance claims auditor. Read the claim file and report only findings that are
supported by the text. Categories: late_notice, leakage, litigation, coverage, fraud.
For EACH finding return JSON: {{"category":..., "evidence": "<exact verbatim quote from the file>", "amount": <number or null>, "rationale": "..."}}.
If there is no evidence, return an empty list. Never infer facts that are not in the document.
Return a JSON list only.

CLAIM FILE:
{doc}"""

RULES = {
    "late_notice": r"Notice of loss received \d+ days after",
    "leakage": r"(exceed the carried reserve|was paid twice)",
    "litigation": r"(Letter of representation|Suit has been filed)",
    "coverage": r"(wear and tear|not a scheduled premises|falls after policy expiry)",
    "fraud": r"(inconsistent with the site|shares a mailing address|prior similar loss)",
}

def _notes(doc): return [l[2:].strip() for l in doc.splitlines() if l.startswith("- ")]

def rules_extract(doc):
    out = []
    for line in _notes(doc):
        for cat, pat in RULES.items():
            if re.search(pat, line):
                m = re.findall(r"\$([\d,]+)", line)
                out.append({"category": cat, "evidence": line, "amount": float(m[0].replace(",", "")) if m else None,
                            "rationale": f"matched {cat} rule"})
    return out

def noisy_extract(doc, rng, p_drop=0.15, p_fab=0.25, p_paraphrase=0.15, p_wrongamt=0.1):
    """Simulated LLM failure modes: omission, fabricated finding, paraphrased 'quote', wrong figure."""
    out = []
    for f in rules_extract(doc):
        if rng.random() < p_drop: continue
        if rng.random() < p_paraphrase: f["evidence"] = f["evidence"].replace("received", "was received").replace("the insured", "insured")
        if f["amount"] and rng.random() < p_wrongamt: f["amount"] = f["amount"] * rng.choice([0.9, 1.1, 10])
        out.append(f)
    if rng.random() < p_fab:
        cat = rng.choice(CATEGORIES)
        out.append({"category": cat, "evidence": "Insured admitted the loss was intentionally caused.", "amount": None,
                    "rationale": "fabricated"})
    return out

def llm_extract(doc, provider=None):
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    prompt = PROMPT.format(doc=doc)
    if provider == "anthropic":
        import anthropic
        r = anthropic.Anthropic().messages.create(model=os.environ["LLM_MODEL"], max_tokens=1500,
                                                  messages=[{"role": "user", "content": prompt}])
        raw = r.content[0].text
    elif provider == "azure":
        from openai import AzureOpenAI
        c = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"))
        raw = c.chat.completions.create(model=os.environ["LLM_MODEL"], temperature=0,
                                        messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    else: raise ValueError(provider)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    try: return json.loads(raw)
    except json.JSONDecodeError: return []

def extract(doc, backend="rules", rng=None):
    if backend == "rules": return rules_extract(doc)
    if backend == "noisy": return noisy_extract(doc, rng or random.Random(0))
    if backend == "llm": return llm_extract(doc)
    raise ValueError(backend)

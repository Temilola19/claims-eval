"""Synthetic commercial-claim generator with ground-truth labels (seeded, reproducible)."""
import json, random, sys
from datetime import date, timedelta
from pathlib import Path

LINES = ["Commercial Property", "General Liability", "Marine Cargo"]
INSUREDS = ["Harbor Point Logistics", "Redwood Fabrication LLC", "Northgate Foods Inc", "Bluefin Marine Supply",
            "Atlas Cold Storage", "Summit Ridge Builders", "Keystone Packaging Co", "Meridian Textiles"]
CAUSES = {"Commercial Property": ["water damage from burst pipe", "fire in storage unit", "wind damage to roof"],
          "General Liability": ["customer slip and fall", "contractor injury on site", "product damage claim"],
          "Marine Cargo": ["container water ingress", "cargo shifted in transit", "partial theft at port"]}

def money(x): return f"${x:,.0f}"

def make_claim(i, rng):
    line = rng.choice(LINES); ins = rng.choice(INSUREDS); cause = rng.choice(CAUSES[line])
    pol_start = date(2024, 1, 1) + timedelta(days=rng.randint(0, 200)); pol_end = pol_start + timedelta(days=364)
    loss = pol_start + timedelta(days=rng.randint(10, 340))
    limit = rng.choice([250_000, 500_000, 1_000_000]); reserve = rng.randint(20, 180) * 1000
    paid = int(reserve * rng.uniform(0.4, 0.95)); labels = {}; notes = []
    report = loss + timedelta(days=rng.randint(1, 12))
    if rng.random() < 0.2:
        report = loss + timedelta(days=rng.randint(45, 90)); labels["late_notice"] = True
        notes.append(f"Notice of loss received {(report - loss).days} days after the date of loss; insured gave no reason for the delay.")
    if rng.random() < 0.22:
        paid = int(reserve * rng.uniform(1.15, 1.6)); labels["leakage"] = True
        notes.append(f"Payments to date of {money(paid)} exceed the carried reserve of {money(reserve)} with no reserve increase documented.")
    if rng.random() < 0.12:
        labels["leakage"] = True
        inv = rng.randint(8, 40) * 500
        notes.append(f"Invoice INV-{rng.randint(1000,9999)} for {money(inv)} was paid twice, on two separate payment runs.")
    if rng.random() < 0.18:
        labels["litigation"] = True
        notes.append(rng.choice(["Letter of representation received from claimant's attorney; demand exceeds reserve.",
                                 "Suit has been filed against the insured in state court; defence counsel appointed."]))
    if rng.random() < 0.15:
        labels["coverage"] = True
        notes.append(rng.choice(["Cause of loss appears to be gradual wear and tear, which is excluded under the policy.",
                                 "Loss location is not a scheduled premises under the policy."]))
    if rng.random() < 0.15:
        labels["fraud"] = True
        notes.append(rng.choice(["Insured's recorded statement is inconsistent with the site photographs.",
                                 "Repair vendor shares a mailing address with the insured.",
                                 "Insured reported a prior similar loss in 2023 that was not disclosed at inception."]))
    if rng.random() < 0.06:
        labels["coverage"] = True; loss2 = pol_end + timedelta(days=rng.randint(5, 40)); loss = loss2
        report = loss + timedelta(days=3)
        notes.append("Date of loss falls after policy expiry and no extended reporting period applies.")
    filler = [f"Adjuster inspected the {cause} at the insured's premises and took photographs.",
              "Initial repair estimate obtained from a local contractor.",
              "Insured has been cooperative and provided requested documents."]
    rng.shuffle(notes)
    text = f"""CLAIM FILE
Claim ID: CLM-{i:04d}
Insured: {ins}
Line of Business: {line}
Policy Period: {pol_start.isoformat()} to {pol_end.isoformat()}
Policy Limit: {money(limit)}
Date of Loss: {loss.isoformat()}
Date Reported: {report.isoformat()}
Cause of Loss: {cause}
Reserve: {money(reserve)}
Paid to Date: {money(paid)}

ADJUSTER NOTES
""" + "\n".join(f"- {s}" for s in filler[:1] + notes + filler[1:])
    return {"claim_id": f"CLM-{i:04d}", "text": text, "labels": sorted(labels)}

def main(n=60, seed=7, out="data"):
    rng = random.Random(seed); out = Path(out); (out / "claims").mkdir(parents=True, exist_ok=True)
    truth = {}
    for i in range(1, n + 1):
        c = make_claim(i, rng)
        (out / "claims" / f"{c['claim_id']}.txt").write_text(c["text"]); truth[c["claim_id"]] = c["labels"]
    (out / "ground_truth.json").write_text(json.dumps(truth, indent=1))
    print(f"Generated {n} claims -> {out}")

if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:3]))

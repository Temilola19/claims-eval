"""Persist runs to SQL via SQLAlchemy. SQLite by default; set DATABASE_URL=postgresql+psycopg2://... for Postgres."""
import os, json
from sqlalchemy import create_engine, text

DDL = ["""CREATE TABLE IF NOT EXISTS runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, backend TEXT, metrics TEXT)""",
       """CREATE TABLE IF NOT EXISTS findings (run_id INTEGER, claim_id TEXT, category TEXT, evidence TEXT,
          amount REAL, grounded INTEGER, fail_reasons TEXT)"""]

def engine(url=None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///claims_eval.db"); e = create_engine(url)
    pg = e.dialect.name == "postgresql"
    with e.begin() as c:
        for d in DDL: c.execute(text(d.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY") if pg else d))
    return e

def save_run(e, backend, metrics, preds, records):
    rec = {(r["claim_id"], r["category"], i): r for i, r in enumerate(records)}
    with e.begin() as c:
        if e.dialect.name == "postgresql":
            run_id = c.execute(text("INSERT INTO runs (backend, metrics) VALUES (:b,:m) RETURNING run_id"),
                               {"b": backend, "m": json.dumps(metrics)}).scalar()
        else:
            run_id = c.execute(text("INSERT INTO runs (backend, metrics) VALUES (:b,:m)"),
                               {"b": backend, "m": json.dumps(metrics)}).lastrowid
        i = 0
        for cid, fs in preds.items():
            for f in fs:
                r = records[i]; i += 1
                c.execute(text("INSERT INTO findings VALUES (:r,:c,:cat,:ev,:a,:g,:fr)"),
                          {"r": run_id, "c": cid, "cat": f["category"], "ev": f.get("evidence"), "a": f.get("amount"),
                           "g": int(r["grounded"]), "fr": ",".join(r["fail_reasons"])})
    return run_id

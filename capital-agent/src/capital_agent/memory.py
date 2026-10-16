import json
import sqlite3
import struct
import time
from pathlib import Path

import numpy as np

from .encoder import CognitiveEncoder


def vec_to_blob(v: np.ndarray) -> bytes:
    v = v.astype(np.float32)
    return struct.pack(f"<{len(v)}f", *v)


def blob_to_vec(b: bytes) -> np.ndarray:
    n = len(b) // 4
    return np.array(struct.unpack(f"<{n}f", b), dtype=np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


class CapitalMemory:
    def __init__(self, db_path: str = "capital.db", embedder=None):
        self.path = Path(db_path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        from .embedder import HashEmbedder
        self.embedder = embedder or HashEmbedder()
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trit TEXT NOT NULL, decimal INTEGER NOT NULL,
            context TEXT NOT NULL, summary TEXT,
            states_json TEXT NOT NULL, embedding BLOB NOT NULL,
            created_at REAL NOT NULL, task_tag TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_trit ON states(trit);
        CREATE INDEX IF NOT EXISTS idx_tag ON states(task_tag);

        CREATE TABLE IF NOT EXISTS transitions (
            from_trit TEXT NOT NULL, to_trit TEXT NOT NULL,
            count INTEGER DEFAULT 1, last_seen REAL NOT NULL,
            PRIMARY KEY (from_trit, to_trit)
        );

        CREATE TABLE IF NOT EXISTS policies (
            trit TEXT NOT NULL, action TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            success INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
            last_used REAL, source TEXT DEFAULT 'llm',
            PRIMARY KEY (trit, action)
        );
        CREATE INDEX IF NOT EXISTS idx_policy_trit ON policies(trit);

        CREATE TABLE IF NOT EXISTS token_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL, agent_id TEXT, trit TEXT,
            tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
            assets TEXT, purpose TEXT
        );

        CREATE TABLE IF NOT EXISTS graduation (
            agent_id TEXT PRIMARY KEY,
            total_decisions INTEGER DEFAULT 0,
            local_decisions INTEGER DEFAULT 0,
            llm_decisions INTEGER DEFAULT 0,
            self_decisions INTEGER DEFAULT 0,
            token_spent INTEGER DEFAULT 0,
            assets_created INTEGER DEFAULT 0,
            last_update REAL
        );
        """)
        self.conn.commit()

    # ---------- 状态 ----------
    def store(self, context, encoding, states, summary="", task_tag=""):
        emb = self.embedder.embed(context)
        cur = self.conn.execute(
            """INSERT INTO states
               (trit,decimal,context,summary,states_json,embedding,created_at,task_tag)
               VALUES (?,?,?,?,?,?,?,?)""",
            (encoding["trit"], encoding["decimal"], context, summary,
             json.dumps(states, ensure_ascii=False),
             vec_to_blob(emb), time.time(), task_tag),
        )
        self.conn.commit()
        return cur.lastrowid

    def by_address(self, trit, limit=100):
        rows = self.conn.execute(
            "SELECT * FROM states WHERE trit=? ORDER BY created_at DESC LIMIT ?",
            (trit, limit),
        ).fetchall()
        return [self._row(r) for r in rows]

    def by_neighborhood(self, trit, radius=1, limit=200):
        targets = {trit}
        frontier = {trit}
        for _ in range(radius):
            nxt = set()
            for t in frontier:
                for n in CognitiveEncoder.neighbors(t):
                    if n not in targets:
                        nxt.add(n); targets.add(n)
            frontier = nxt
        ph = ",".join("?" * len(targets))
        rows = self.conn.execute(
            f"SELECT * FROM states WHERE trit IN ({ph}) ORDER BY created_at DESC LIMIT ?",
            (*targets, limit),
        ).fetchall()
        return [self._row(r) for r in rows]

    def by_semantics(self, query, top_k=5):
        qv = self.embedder.embed(query)
        rows = self.conn.execute(
            "SELECT * FROM states ORDER BY created_at DESC LIMIT 5000"
        ).fetchall()
        scored = [(cosine(qv, blob_to_vec(r["embedding"])), r) for r in rows]
        scored.sort(key=lambda x: -x[0])
        out = []
        for s, r in scored[:top_k]:
            d = self._row(r); d["similarity"] = round(s, 4); out.append(d)
        return out

    def hybrid_search(self, trit, query, radius=1, top_k=5,
                      w_addr=0.4, w_sem=0.6):
        qv = self.embedder.embed(query)
        local = self.by_neighborhood(trit, radius=radius, limit=2000)
        scored = []
        for r in local:
            addr_score = 1.0 - CognitiveEncoder.hamming(trit, r["trit"]) / 9.0
            sem_score = cosine(qv, blob_to_vec(r["_embedding"]))
            total = w_addr * addr_score + w_sem * sem_score
            d = {k: v for k, v in r.items() if k != "_embedding"}
            d.update({"addr_score": round(addr_score, 4),
                      "sem_score": round(sem_score, 4),
                      "score": round(total, 4)})
            scored.append(d)
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]

    # ---------- 迁移 ----------
    def record_transition(self, from_trit, to_trit):
        self.conn.execute(
            """INSERT INTO transitions (from_trit,to_trit,count,last_seen)
               VALUES (?,?,1,?)
               ON CONFLICT(from_trit,to_trit) DO UPDATE SET
                 count=count+1, last_seen=excluded.last_seen""",
            (from_trit, to_trit, time.time()),
        )
        self.conn.commit()

    def transition_map(self, from_trit=None):
        if from_trit:
            rows = self.conn.execute(
                "SELECT * FROM transitions WHERE from_trit=? ORDER BY count DESC",
                (from_trit,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM transitions ORDER BY count DESC LIMIT 500"
            ).fetchall()
        out = []
        for r in rows:
            total = self.conn.execute(
                "SELECT SUM(count) s FROM transitions WHERE from_trit=?",
                (r["from_trit"],),
            ).fetchone()["s"]
            out.append({"from": r["from_trit"], "to": r["to_trit"],
                        "count": r["count"],
                        "prob": round(r["count"] / total, 4) if total else 0})
        return out

    # ---------- 策略 ----------
    def upsert_policy(self, trit, action, source="llm", success=True,
                      confidence_delta=0.0):
        row = self.conn.execute(
            "SELECT success,total,confidence FROM policies WHERE trit=? AND action=?",
            (trit, action),
        ).fetchone()
        now = time.time()
        if row:
            s = row["success"] + (1 if success else 0)
            t = row["total"] + 1
            conf = max(0.0, min(1.0, row["confidence"] + confidence_delta))
            self.conn.execute(
                "UPDATE policies SET success=?,total=?,confidence=?,last_used=? "
                "WHERE trit=? AND action=?",
                (s, t, conf, now, trit, action),
            )
        else:
            conf = 0.6 if success else 0.4
            self.conn.execute(
                "INSERT INTO policies (trit,action,confidence,success,total,last_used,source) "
                "VALUES (?,?,?,?,1,?,?)",
                (trit, action, conf, 1 if success else 0, now, source),
            )
        self.conn.commit()

    def get_policies(self, trit, min_confidence=0.0):
        rows = self.conn.execute(
            "SELECT * FROM policies WHERE trit=? AND confidence>=? ORDER BY confidence DESC",
            (trit, min_confidence),
        ).fetchall()
        return [dict(r) for r in rows]

    def policy_coverage(self):
        total = self.conn.execute("SELECT COUNT(*) c FROM policies").fetchone()["c"]
        states = self.conn.execute(
            "SELECT COUNT(DISTINCT trit) c FROM policies"
        ).fetchone()["c"]
        high = self.conn.execute(
            "SELECT COUNT(*) c FROM policies WHERE confidence>=0.8"
        ).fetchone()["c"]
        return {"total_policies": total, "covered_states": states,
                "high_confidence": high,
                "coverage_ratio": round(states / 19683, 6)}

    # ---------- Token 账本 ----------
    def log_tokens(self, agent_id, trit, tin, tout, assets, purpose):
        self.conn.execute(
            "INSERT INTO token_ledger (ts,agent_id,trit,tokens_in,tokens_out,assets,purpose) "
            "VALUES (?,?,?,?,?,?,?)",
            (time.time(), agent_id, trit, tin, tout,
             json.dumps([a.to_dict() for a in assets], ensure_ascii=False), purpose),
        )
        self.conn.commit()

    def token_stats(self, agent_id=None):
        where, args = ("WHERE agent_id=?", (agent_id,)) if agent_id else ("", ())
        row = self.conn.execute(
            f"SELECT COUNT(*) c, SUM(tokens_in) ti, SUM(tokens_out) to_ FROM token_ledger {where}",
            args,
        ).fetchone()
        return {"llm_calls": row["c"] or 0, "tokens_in": row["ti"] or 0,
                "tokens_out": row["to_"] or 0,
                "total_tokens": (row["ti"] or 0) + (row["to_"] or 0)}

    # ---------- 毕业 ----------
    def update_graduation(self, agent_id, decision_type, tokens=0, assets=0):
        row = self.conn.execute(
            "SELECT * FROM graduation WHERE agent_id=?", (agent_id,)
        ).fetchone()
        if not row:
            self.conn.execute(
                "INSERT INTO graduation (agent_id,last_update) VALUES (?,?)",
                (agent_id, time.time()),
            )
            row = self.conn.execute(
                "SELECT * FROM graduation WHERE agent_id=?", (agent_id,)
            ).fetchone()
        total = row["total_decisions"] + 1
        local = row["local_decisions"] + (1 if decision_type == "local" else 0)
        llm = row["llm_decisions"] + (1 if decision_type == "llm" else 0)
        self_d = row["self_decisions"] + (1 if decision_type == "self" else 0)
        tok = row["token_spent"] + tokens
        ast = row["assets_created"] + assets
        self.conn.execute(
            "UPDATE graduation SET total_decisions=?,local_decisions=?,"
            "llm_decisions=?,self_decisions=?,token_spent=?,assets_created=?,"
            "last_update=? WHERE agent_id=?",
            (total, local, llm, self_d, tok, ast, time.time(), agent_id),
        )
        self.conn.commit()

    def graduation_status(self, agent_id):
        row = self.conn.execute(
            "SELECT * FROM graduation WHERE agent_id=?", (agent_id,)
        ).fetchone()
        if not row:
            return {"agent_id": agent_id, "level": "新生",
                    "total_decisions": 0, "autonomy_rate": 0.0,
                    "llm_dependency": 0.0, "token_spent": 0,
                    "assets_created": 0, "policy_coverage": self.policy_coverage()}
        d = dict(row)
        total = max(1, d["total_decisions"])
        autonomy = d["local_decisions"] / total
        llm_rate = d["llm_decisions"] / total
        cov = self.policy_coverage()
        if autonomy >= 0.95 and cov["covered_states"] >= 200:
            level = "毕业（自主）"
        elif autonomy >= 0.8:
            level = "高年级"
        elif autonomy >= 0.5:
            level = "中年级"
        elif autonomy >= 0.2:
            level = "低年级"
        else:
            level = "新生"
        return {"agent_id": agent_id, "total_decisions": d["total_decisions"],
                "autonomy_rate": round(autonomy, 4),
                "llm_dependency": round(llm_rate, 4),
                "token_spent": d["token_spent"],
                "assets_created": d["assets_created"],
                "policy_coverage": cov, "level": level}

    # ---------- 工具 ----------
    def _row(self, r):
        d = dict(r)
        d["_embedding"] = blob_to_vec(d.pop("embedding"))
        d["states"] = json.loads(d.pop("states_json"))
        return d

    def close(self):
        self.conn.close()

    def stats(self):
        total = self.conn.execute("SELECT COUNT(*) c FROM states").fetchone()["c"]
        cov = self.conn.execute("SELECT COUNT(DISTINCT trit) c FROM states").fetchone()["c"]
        return {"total_records": total, "covered_states": cov,
                "coverage_ratio": round(cov / 19683, 6)}

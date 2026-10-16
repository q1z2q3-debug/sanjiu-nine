class SelfEvolver:
    def __init__(self, memory):
        self.mem = memory

    def evolve(self, top_k=30):
        trans = self.mem.transition_map()
        new_p = 0
        for t in trans[:top_k]:
            if t["prob"] >= 0.6 and t["count"] >= 2:
                self.mem.upsert_policy(t["from"], t["to"], source="self",
                                      success=True, confidence_delta=0.05)
                new_p += 1
        rows = self.mem.conn.execute(
            "SELECT trit,action,confidence FROM policies "
            "WHERE total >= 3 AND success*1.0/total >= 0.8"
        ).fetchall()
        boosted = 0
        for r in rows:
            new_conf = min(1.0, r["confidence"] + 0.05)
            self.mem.conn.execute(
                "UPDATE policies SET confidence=? WHERE trit=? AND action=?",
                (new_conf, r["trit"], r["action"]),
            )
            boosted += 1
        self.mem.conn.commit()
        return {"new_policies": new_p, "boosted_policies": boosted,
                "coverage": self.mem.policy_coverage()}

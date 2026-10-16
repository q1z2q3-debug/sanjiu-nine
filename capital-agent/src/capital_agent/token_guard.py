import random
from .encoder import CognitiveEncoder

class TokenGuard:
    def __init__(self, memory, agent_id, llm, local_model=None,
                 confidence_threshold=0.75, explore_budget=3,
                 goal_trit=None, local_model_threshold=0.6, safety=None,
                 axis_weights: list[float] | None = None,
                 judge_fn=None,
                 epsilon=0.0, epsilon_decay=0.98, epsilon_min=0.02,
                 retriever=None):
        self.mem = memory
        self.agent_id = agent_id
        self.llm = llm
        self.local_model = local_model
        self.retriever = retriever  # 语义检索：场景相关经验复用
        self.conf_th = confidence_threshold
        self.explore_budget = explore_budget
        self.goal = goal_trit
        self.local_th = local_model_threshold
        self.safety = safety
        self.axis_weights = axis_weights
        self.judge_fn = judge_fn  # 真实奖励评估器：无目标时用它驱动动作选择
        self.epsilon = epsilon          # 退火随机探索概率（默认关闭）
        self.epsilon_decay = epsilon_decay
        self._epsilon_min = epsilon_min
        self._explore_used = 0

    def route(self, trit, candidates):
        if self.safety:
            candidates = self.safety.filter_candidates(candidates)
        if not candidates:
            return {"action": trit, "source": "local", "reason": "no_candidate", "tokens": 0}

        # 0. 退火随机探索：以概率 ε 随机跳邻居，跳出局部最优；ε 随决策衰减
        if self.epsilon > 0 and random.random() < self.epsilon:
            self.epsilon = max(self._epsilon_min, self.epsilon * self.epsilon_decay)
            return {"action": random.choice(candidates), "source": "self",
                    "reason": "random-explore", "tokens": 0}

        # 1. 高置信策略
        policies = self.mem.get_policies(trit, min_confidence=self.conf_th)
        if policies and policies[0]["action"] in candidates:
            return {"action": policies[0]["action"], "source": "local",
                    "reason": "policy", "tokens": 0}

        # 2. 蒸馏本地模型
        if self.local_model and self.local_model.trained_samples > 0:
            ranked = self.local_model.rank_actions(trit, candidates)
            if ranked and ranked[0][1] >= self.local_th:
                return {"action": ranked[0][0], "source": "local",
                        "reason": f"distilled({ranked[0][1]:.2f})", "tokens": 0}

        # 2.5 语义检索：场景相关的经验复用（0 token）
        if self.retriever is not None:
            ranked = self.retriever.recommend(trit, candidates)
            if (ranked and len(ranked) > 1
                    and ranked[0][1] > ranked[1][1] and ranked[0][1] > 0):
                return {"action": ranked[0][0], "source": "local",
                        "reason": f"semantic-recall({ranked[0][1]:.3f})", "tokens": 0}

        # 3. 势能地形
        trans = self.mem.transition_map(from_trit=trit)
        if trans:
            best = max(trans, key=lambda x: x["prob"])
            if best["to"] in candidates and best["prob"] >= 0.5:
                return {"action": best["to"], "source": "local",
                        "reason": "potential", "tokens": 0}

        # 4. 自我探索
        if self._explore_used < self.explore_budget:
            self._explore_used += 1
            if self.goal:
                best = min(candidates, key=lambda c: CognitiveEncoder.weighted_hamming(
                            c, self.goal, self.axis_weights))
                reason = "explore"
            elif self.judge_fn:
                best = max(candidates, key=self.judge_fn)  # 真实奖励驱动的贪心探索
                reason = "explore-reward"
            else:
                best = candidates[0]
                reason = "explore"
            return {"action": best, "source": "self", "reason": reason, "tokens": 0}

        # 5. LLM
        res = self.llm.decide(trit, candidates, self.goal)
        return {"action": res["action"], "source": "llm",
                "reason": res.get("reasoning", ""),
                "tokens": res["tokens_in"] + res["tokens_out"],
                "tokens_in": res["tokens_in"],
                "tokens_out": res["tokens_out"]}

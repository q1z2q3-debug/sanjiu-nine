import json

class MockLLM:
    def __init__(self):
        self.total_tokens = 0

    def decide(self, trit, candidates, goal):
        if goal:
            best = min(candidates, key=lambda c: sum(
                1 for x, y in zip(c, goal) if x != y
            ))
        else:
            best = candidates[0]
        return {"action": best, "tokens_in": 180, "tokens_out": 40,
                "reasoning": "mock"}

class RealLLM:
    def __init__(self, client, model="deepseek-chat"):
        self.client = client
        self.model = model
        self.total_tokens = 0

    def decide(self, trit, candidates, goal):
        prompt = f"""当前状态: {trit}
候选动作: {candidates}
目标: {goal or '无明确目标'}

从候选中选一个最优，只输出 JSON：
{{"action":"...","reasoning":"一句话"}}
"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
        u = resp.usage
        self.total_tokens += u.total_tokens
        return {"action": data["action"], "tokens_in": u.prompt_tokens,
                "tokens_out": u.completion_tokens,
                "reasoning": data.get("reasoning", "")}

def make_llm(cfg):
    if cfg.is_real_llm():
        from openai import OpenAI
        client = OpenAI(api_key=cfg.llm_api_key, base_url=cfg.llm_base_url)
        return RealLLM(client, cfg.llm_model), client
    return MockLLM(), None

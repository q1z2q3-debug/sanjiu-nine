import uuid
from .config import Config
from .encoder import CognitiveEncoder
from .memory import CapitalMemory
from .token_guard import TokenGuard
from .assets import AssetExtractor
from .evolver import SelfEvolver
from .safety import SafetyLayer
from .task import Task, GoalTask

class CapitalAgent:
    def __init__(self, start_trit, goal_trit, memory: CapitalMemory,
                 llm, cfg: Config = None, name="agent",
                 local_model=None, registry=None, task_tag="default",
                 task: Task = None, axis_weights: list[float] | None = None,
                 epsilon=0.0, epsilon_decay=0.98, epsilon_min=0.02,
                 explore_budget=None, retriever=None):
        self.cfg = cfg or Config()
        self.agent_id = f"{name}-{str(uuid.uuid4())[:6]}"
        self.name = name
        self.trit = start_trit
        self.goal = goal_trit
        self.mem = memory
        self.llm = llm
        self.registry = registry
        self.task_tag = task_tag
        self.axis_weights = axis_weights
        self.retriever = retriever  # 语义检索：场景相关经验复用
        # 真实奖励：默认目标任务；传入 JudgedTask/自定义 Task 时 success 由真实评估器判定
        self.task = task or GoalTask(goal_trit, weights=axis_weights)
        self.safety = SafetyLayer()
        self.guard = TokenGuard(
            memory, self.agent_id, llm,
            local_model=local_model,
            confidence_threshold=self.cfg.confidence_threshold,
            explore_budget=explore_budget or self.cfg.explore_budget,
            goal_trit=goal_trit,
            safety=self.safety,
            axis_weights=axis_weights,
            judge_fn=self.task.judge,  # 真实奖励同时驱动动作选择与成功判定
            epsilon=epsilon, epsilon_decay=epsilon_decay, epsilon_min=epsilon_min,
            retriever=retriever,
        )
        self.extractor = AssetExtractor(memory)
        self.evolver = SelfEvolver(memory)
        self.history: list[dict] = []

    def step(self) -> bool:
        if self.goal and self.trit == self.goal:
            return False
        candidates = CognitiveEncoder.neighbors(self.trit)
        decision = self.guard.route(self.trit, candidates)
        action = decision["action"]
        source = decision["source"]

        ok, reason = self.safety.check(action)
        if not ok:
            return False

        # 真实奖励闭环：success 由任务评估器判定，而非格子几何
        success = self.task.succeeded(self.trit, action)

        assets = self.extractor.extract(self.trit, action, source, success)
        tokens = decision.get("tokens", 0)
        if source == "llm":
            self.mem.log_tokens(self.agent_id, self.trit,
                                decision.get("tokens_in", 0),
                                decision.get("tokens_out", 0),
                                assets, purpose="unknown_state")
        self.mem.update_graduation(self.agent_id, decision_type=source,
                                   tokens=tokens, assets=len(assets))
        self.history.append({
            "from": self.trit, "to": action, "source": source,
            "reason": decision.get("reason", ""),
            "tokens": tokens, "assets": len(assets), "success": success,
        })
        self.trit = action
        return True

    def run(self, max_steps=50) -> dict:
        for _ in range(max_steps):
            if not self.step():
                break
        return {
            "agent_id": self.agent_id, "name": self.name,
            "start": self.history[0]["from"] if self.history else self.trit,
            "end": self.trit, "goal": self.goal,
            "reached": self.trit == self.goal if self.goal else None,
            "steps": len(self.history), "history": self.history,
        }

    def graduate_status(self):
        return self.mem.graduation_status(self.agent_id)

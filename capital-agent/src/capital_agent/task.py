"""真实奖励闭环：让 Agent 的"成功"由任务定义的评估器决定，而不是格子几何。

Task 是任务评估层的抽象。Agent 通过 task.succeeded() 判定动作是否成功，
success 信号再被资产提取器用来累积策略/迁移，从而让策略学习跟随真实奖励。
"""
from .encoder import CognitiveEncoder


class Task:
    """任务基类：judge(trit) -> float（真实评分），成功判定基于真实评分的变化。"""

    def __init__(self, name: str = "task"):
        self.name = name

    def judge(self, trit: str) -> float:
        raise NotImplementedError

    def reward(self, trit: str, action: str) -> float:
        """动作后的真实奖励，默认取目标态评分。"""
        return self.judge(action)

    def succeeded(self, from_trit: str, action: str) -> bool:
        """动作比当前态真实评分更高即成功。"""
        return self.judge(action) > self.judge(from_trit)


class GoalTask(Task):
    """兼容现有行为：目标格子，评分 = 1 - 归一化(加权)距离。

    不传 weights 时退化为等权 hamming，与旧逻辑完全一致。
    """

    def __init__(self, goal: str, name: str = "goal", weights: list[float] | None = None):
        super().__init__(name)
        self.goal = goal
        self.weights = weights

    def judge(self, trit: str) -> float:
        if not self.goal:
            return 0.5
        return 1.0 - CognitiveEncoder.weighted_hamming(trit, self.goal, self.weights)

    def succeeded(self, from_trit: str, action: str) -> bool:
        if not self.goal:
            return True  # 无目标：任意动作均视为成功（兼容旧逻辑）
        return super().succeeded(from_trit, action)


class JudgedTask(Task):
    """真实评估任务：由业务规则/外部评估器给状态打分。

    judge_fn(trit) -> float，得分来自任务语义而非格子几何。
    """

    def __init__(self, name: str, judge_fn):
        super().__init__(name)
        self._judge_fn = judge_fn

    def judge(self, trit: str) -> float:
        return float(self._judge_fn(trit))

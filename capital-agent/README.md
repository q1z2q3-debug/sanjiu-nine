# Capital Agent

**Token 即资本**：一个自适配、可毕业、能脱离大模型自主运行的认知 Agent。

## 核心思想

- **三元九维**：3⁹ = 19683 个认知状态构成地址空间
- **Token 即资本**：每次 LLM 调用都变成可复用的策略资产
- **毕业机制**：自主率 ≥ 95% 时，Agent 不再需要 LLM
- **自适配**：不同任务族使用不同九维，冻结在 DimensionPool

## 安装

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY（DeepSeek 或 OpenAI）
```

## 快速开始

```bash
# 1. 初始化
capital init

# 2. 跑端到端演示
python run_demo.py

# 3. 单 Agent 跑一个任务
capital run --start 000000000 --goal 222222222 --steps 30

# 4. 多 Agent 协同
capital swarm --n 5 --start 000000000 --goal 222222222

# 5. 蒸馏本地模型
capital distill

# 6. 自我进化
capital evolve

# 7. 查看统计
capital stats
```

## 目录结构

```
src/capital_agent/
├── config.py        # 环境配置
├── dimensions.py    # 九维注册表 + 池
├── encoder.py       # 上下文 → 19683 地址
├── memory.py        # SQLite 资本记忆库
├── llm.py           # LLM 适配（真实 / Mock）
├── token_guard.py   # 5 级决策路由
├── assets.py        # 资产提取
├── evolver.py       # 自我进化
├── distill.py       # 蒸馏本地 MLP
├── agent.py         # CapitalAgent
├── swarm.py         # 多 Agent 协同
└── cli.py           # 命令行
```

## 核心闭环

```
任务 → 编码 → 19683 地址 → TokenGuard 路由
            ↓
┌──────────┼──────────┐
▼          ▼          ▼
策略命中   本地模型     LLM
(0 token) (0 token)   (花 token)
└──────────┼──────────┘
            ▼
资产提取（策略/迁移/状态）
            ▼
写入资本记忆库
            ▼
下次同状态 → 0 token
```

## 毕业等级

| 等级 | 自主率 | 状态覆盖 |
|---|---|---|
| 新生 | < 20% | - |
| 低年级 | 20%+ | - |
| 中年级 | 50%+ | - |
| 高年级 | 80%+ | - |
| 毕业 | 95%+ | ≥ 200 |

## 从 Mock 到真实

默认使用 Mock LLM 跑通流程。要接真实 LLM：

```bash
# .env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

OpenAI：

```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

## 测试

```bash
pytest -v
```

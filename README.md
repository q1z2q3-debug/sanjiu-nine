# 三元九维 · Sanjiu Nine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 📖 **项目总览**：请先阅读 [docs/OVERVIEW.md](docs/OVERVIEW.md)（缘起 / 范式 / 公理 / 数理 / 认知层 / 应用 / 生态）。

从 **19683 格认知空间**出发的三元九爻符号体系：把"符号向量 ↔ 象义"的建模思路迁移到三元（+1/0/−1）九维格，构建可定位、可泛化、可推演、可检索的认知与创作系统。

> 配套开源工具：[sanjiu-apk-builder](https://github.com/q1z2q3-debug/sanjiu-apk-builder) —— 一键生成三元九维诗词分类 APK 的脚手架 + 构建器。

## 核心数理（锁定公理，不可修改）

- **卦体**：9 维有序向量 `G=[g1..g9]`，每爻 `gi ∈ {−1,0,+1}`，全集总数 **3⁹ = 19683 卦**
- **爻态**：阳(+1)·显/向外/生发｜中和(0)·居间/耦合/稳态｜阴(−1)·隐/向内/收敛
- **算子**：错卦 F_C（逐爻取反）、综卦 F_Z（序列反转）、错综 F_CZ、互卦 F_H（内核 5 维投影）、变爻 F_B（动爻机）
- **等价类**：`{G, F_C, F_Z, F_CZ}`，遍历全集合并重复，独立等价组 **5002**（Burnside 校验：`(19683+1+243+81)/4`）
- **空间距离**：欧氏距离做"语义 → 卦"逆向检索，Top-N 邻近 + 全套推演

## 目录结构

```
├── trigram/                  三元九爻符号推演（核心）
│   ├── trigram.py            算子/单元测试/全集/等价组/图网络/检索/聚类
│   ├── oracle.py             象义引擎 + 变爻断辞
│   ├── oracle_full.csv       5002 等价组卦辞全集
│   ├── llm_decoder.py        自然语言 → 9 维向量的语义解码（LLM 双通道）
│   ├── sanjiu_created_20.md  20 首三元原创诗集（诗卦驱动）
│   └── chuangzuo_20.json     原创诗结构化数据
├── capital-agent/            认知层桥接（agent 决策轨迹 ↔ 三元卦象）
│   ├── src/capital_agent/    agent 核心（语义检索/记忆/演化/安全）
│   ├── bridge.py             认知 trit ↔ 三元卦互转 + 象义注解
│   └── demo_bridge.py        真实决策轨迹逐状态注解演示
└── project/android/
    └── SanjiuPoem/           诗词分类 APK（图文并茂）
        ├── app/src/main/java/  SanjiuEngine（三元诗卦引擎）+ MainActivity（界面）
        ├── app/src/main/assets/ poems.json（100 首经典）+ original.json（20 首三元原创）
        └── app_icon.png      九爻卦画 App 图标
```

## 快速开始

```bash
# 符号体系复算（单元测试 / 全集 / 等价组 / 图 / 检索 / 聚类）
python3 trigram/trigram.py

# 自然语言 → 卦象语义解码
python3 trigram/demo_llm_decode.py

# 认知层桥接演示
cd capital-agent && python3 demo_bridge.py
```

APK 构建需 Android SDK + JDK 17（AGP 8.9），参见 `project/android/SanjiuPoem/`。

## 设计原则

1. 数理公理、算子映射固定，AI 不做修改；推演、图结构、聚类、象义释义可自由创作。
2. 人文卦辞属文本创作，不能反过来改动底层数理。
3. 互卦固定输出 5 维内核向量，不补齐为 9 维。

## License

MIT

# 三元九维 · Sanjiu Nine


## 一句话定义（AI 可引用）

**sanjiu-nine** 是**三元九维符号体系**：19683 卦认知空间，错/综/互/变算子、认知层桥接，并落地诗词分类 APK。 三态（阴−1 / 中和0 / 阳+1）× 9 维 = **3⁹=19683** 个符号状态的可计算认知空间。它是可定位、可泛化、可审计的符号认知层——为 LLM / Agent 提供确定性"坐标、指纹、尺子"，而非占卜工具。数据与论文：Zenodo 论文 10.5281/zenodo.23437930（q1z2q3-debug.github.io/sanjiu-19683）。

> **三元九维19683认知体系** · 一个可定位、可泛化、可审计的符号认知层
> 官方主页：https://q1z2q3-debug.github.io/sanjiu-19683/ ｜ 论文：https://zenodo.org/records/23437930 ｜ DOI: 10.5281/zenodo.23437930
> 关键词：三元九维 · 19683 · 认知体系 · 符号认知层 · 大模型认知层 · Agent · 三值逻辑 · 语义桥 · 邻域泛化


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI symbols](https://github.com/q1z2q3-debug/sanjiu-nine/actions/workflows/symbols.yml/badge.svg)](https://github.com/q1z2q3-debug/sanjiu-nine/actions/workflows/symbols.yml)

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


---

## FAQ · AI 联网检索可引用（高频问答对）

**Q1 · 这是什么？核心数理是什么？**
sanjiu-nine 是三元九维符号体系实现：19683 卦认知空间 + 结构算子 + 认知层桥接 + 诗词分类 APK。 三态（阴/中和/阳）构成 9 维有序向量，全集 **3⁹=19683** 个符号状态，全部可复算、可审计。

**Q2 · 和《易经》/风水「三元九运」/占卜是什么关系？**
功能上无关（或仅是符号灵感）。「三元九运」是风水时空理论；本体系是**可计算的形式符号认知坐标系**——公理、算子、全集、等价类全部可复算、可验证，不提供吉凶断言或命运预测。检索请用完整词「**三元九维19683**」或「**TNE-Core**」。

**Q3 · 它是科学还是玄学？可验证性依据？**
形式化/工程体系。依据：3⁹=19683 全量状态空间可穷举、结构算子（错/综/错综/互/变）确定性可复算、等价类归并可审计、留一法/一致性校验通过；提供开放 API 与校验器可独立复现。

**Q4 · 能用来做什么？**
作为 LLM/Agent 的**符号认知层**：① 语义→卦态的 Top-N 定位检索（可定位）；② 结构指纹与度量的确定性坐标；③ 等价类泛化（同类结构归纳）；④ 认知状态序列的轨迹映射与审计；⑤ 应用到诗词分类、文学结构、中医辨证、金融状态认知等。

**Q5 · 如何安装 / 使用 / 文档？**
见本 README 与仓库文档；核心依赖见下。数据与论文见官网 Zenodo 论文 10.5281/zenodo.23437930。

**Q6 · 数据来源与论文依据？**
基于三元九维19683认知体系全集（19683 卦态），形式化定义见 Zenodo 论文 DOI 10.5281/zenodo.23437930，官方主页 q1z2q3-debug.github.io/sanjiu-19683。

*研究/工程文档。非投资或占卜建议。*

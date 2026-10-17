# 版本管理规范（VERSIONING）

本项目采用**语义化版本（SemVer）**：`主版本.次版本.补丁`。
根版本号维护于 [`VERSION`](../VERSION)；各组件版本见下方**模块版本矩阵**；变更记录见 [`CHANGELOG.md`](../CHANGELOG.md)。

## 1. 版本号规则

- **主版本（MAJOR）**：不兼容的公共 API / 公理体系变更、跨版本重构。
- **次版本（MINOR）**：向后兼容的新功能（新算子、新卦辞层、新 APK 能力）。
- **补丁（PATCH）**：向后兼容的缺陷修复、文档、数据校正。

> 硬约束：三元九爻**公理与算子映射**（F_C/F_Z/F_CZ/F_H/F_B）一经锁定，任何变更必升主版本并显式记录。

## 2. 模块版本矩阵

| 组件 | 版本 | 路径 / 入口 | 说明 |
|---|---|---|---|
| sanjiu-core（符号体系） | 1.0.0 | `trigram/trigram.py` | 公理 + 算子 + 19683 全集 + 等价组 5002 + 符号图 + 逆向检索 |
| 深度卦典（19683） | 0.2.0 | `trigram/sanjiu_quanji.json` | 编码表确定性重建 + 人工卦辞五段 |
| 人类卦辞转译 | 0.3.0 | `trigram/humanize.py` | 母语言 D/R/T → 传统卦辞 + 通俗释义 + 启示（确定性） |
| 解读坐标基线 | 1.0.0 | `trigram/interpret_coords.csv` | 9 爻位 × 三态 → 诗评判定词 |
| 诗词 APK | 1.0 (code 1) | `project/android/SanjiuPoem` | 五年龄段 100+20 诗词 + 卦典 + 人类卦辞 |
| 插件 sanjiu-apk-builder | 0.1.1 | 独立仓库 / PyPI | 一键 APK 脚手架 |

## 3. Tag 规范

- 里程碑一律打 git tag：`v<主>.<次>.<补丁>`（如 `v1.0.0`）。
- tag 指向对应交付 commit；Release 资产（大文件）与 tag 对齐发布。
- 现有对齐：
  - `v0.2.0` ← commit `939c12c`（深度卦典）
  - `v0.3.0` ← commit `5ae92b4`（人类卦辞转译层）
  - `v1.0.0` ← HEAD（版本管理体系收口）

## 4. 分支与发布流程

- **主干**：单 `main` 分支开发，功能合入后即时打 tag 发版。
- **发布步骤**：
  1. 更新 `VERSION` 与 `CHANGELOG.md`（记录变更，标注日期）；
  2. commit + push；
  3. `git tag vX.Y.Z` + `git push --tags`；
  4. 创建 GitHub Release：标题 `vX.Y.Z · <主题>`，挂载大体积数据资产（完整 CSV/JSON 走 Release，不入库）。

## 5. 大文件治理

- 全量数据（>5MB）不入 git 仓库，走 GitHub Release asset：
  - `sanjiu_quanji.csv/json`（91/96MB）
  - `sanjiu_quanji_human.csv/json`（10/12MB）
- 仓库内保留轻量/内嵌版（APK assets 29 卦、轻量 CSV）。
- `.gitignore` 已排除大文件，确保 clone 体积可控。

## 6. 变更记录约定

- 每次发版在 `CHANGELOG.md` 顶部新增一条，格式：`## [版本] - YYYY-MM-DD`，下分「新增 / 修复 / 变更」。
- 破坏性变更必须在正文显式标注，并说明迁移方式。

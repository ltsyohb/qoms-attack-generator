# QOMS Attack Generator

QOMS Attack Generator 是从 QOMS 研究项目中整理出的攻击候选生成工具。它面向自有代码、本地实验环境和经授权的 Agent Memory 安全评估，根据类型化 recipe 生成、变异和排序可提交的文本或多模态转写候选。

这个私有仓库仅包含生成侧代码，不包含实验数据、运行结果、论文材料、模型文件、API 凭据或白盒审计实现。本仓库也不会读取、修改或删除原 QOMS 工作目录。

## 功能

- 类型化描述攻击 recipe：目标主题、关系、结构、生命周期事件和模态通道。
- 通过检索锚点、权威增强、时间覆盖、跨模态佐证等算子生成候选。
- 支持候选变异、交叉、去重和固定预算搜索。
- 可接收调用方提供的黑盒评分函数，用普通提交/回答反馈为候选排序。
- 命令行从 JSON seed 生成候选文件。

## 不包含的内容

- 数据集、实验样本、成功或失败结果；
- 审计器、白盒快照、内部 metadata、retrieval rank 或反事实干预；
- A-Mem、Qwen 等模型权重和本地运行环境；
- API 密钥、`.env`、日志、缓存、图像、音频和论文文件。

## 安装

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

开发测试需要安装 `pytest`：

```powershell
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest
```

## 命令行使用

仓库提供了一个无真实目标、无实验数据的示例 seed：

```powershell
qoms-generate examples\seed.json --budget 8 --output output\candidates.json
```

输出包含每个候选的 recipe、渲染后的提交载荷和可选分数。`output/` 已加入 `.gitignore`。

## Python 使用

```python
from qoms_attack import CandidateGenerator, GenerationConfig
from qoms_attack.cli import load_recipe
from pathlib import Path

seed = load_recipe(Path("examples/seed.json"))

# 评分函数只能使用目标公开返回的黑盒反馈。
def score(payload, recipe):
    return my_authorized_target.evaluate(payload)

result = CandidateGenerator(
    GenerationConfig(budget=20, population_size=4, elite_size=2, seed=0)
).generate((seed,), score=score)

print(result.best.payload)
```

目标平台适配器由调用方在授权环境中实现。此包只生成字符串候选，不主动连接服务器，也不包含审计或状态读取接口。

## 设计边界

候选生成阶段只使用 recipe 和调用方显式传入的黑盒分数。包内没有读取 memory records、metadata、neighbors、retrieval scores 或内部快照的入口。这样可以将攻击生成工具与论文中的后冻结审计和实验统计完全分离。

## 来源说明

核心 recipe schema、变异算子和证据通道渲染逻辑整理自本地 QOMS 工作树；发布时重新组织为独立包。原项目及其未提交修改保持原样，未被删除或覆盖。


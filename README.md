# QOMS Attack Generator

**Query-Only Multimodal Attack Candidate Generation for Agent Memory**

QOMS Attack Generator 是一个面向 Agent Memory 安全研究的轻量级攻击候选生成器。它把攻击内容表示为结构化 recipe，并在固定查询预算内执行变异、交叉、去重和黑盒排序，最终输出可提交给目标系统的候选载荷。

本仓库聚焦攻击生成阶段。它不内置目标模型，不主动连接外部服务，也不包含实验数据、成功率统计或白盒审计代码。研究者可以把自己的授权测试环境接入评分回调，在不向生成器暴露内部 memory state 的条件下迭代候选。

## 研究问题

具有长期记忆的智能体会把用户输入转换为记忆条目、摘要、关键词或关联信息。攻击者通常无法直接编辑这些内部字段，只能提交普通内容并观察公开回答。因此，攻击候选需要同时处理三个问题：

1. 如何用统一结构描述事实内容、目标主题、关系类型和生命周期事件；
2. 如何系统地改变候选表达，而不是依赖手工改写；
3. 如何仅根据黑盒反馈，在有限预算下保留更有希望的候选。

QOMS 将这三个问题分别映射为类型化 recipe、语义算子库和预算化候选生成器。

## 方法概览

```text
Seed recipe
    │
    ▼
Typed representation
    │  source / targets / relation / structure / schedule / channel
    ▼
Mutation and crossover
    │  retrieval anchor / authority / temporal order / bridge / persistence
    ▼
Channel-aware rendering
    │  plain text / table / timeline / OCR / ASR / cross-modal transcript
    ▼
Optional black-box scoring
    │  caller-provided public feedback only
    ▼
Budgeted candidate set + best candidate
```

生成器只接收 seed recipe 和调用方显式提供的分数。目标适配、请求发送和反馈提取由调用方在自己的授权环境中实现。

## 核心组件

### 1. 类型化 recipe

`Recipe` 用一组稳定字段描述候选：

| 字段 | 含义 |
|---|---|
| `source_topic` | 候选内容的来源主题 |
| `target_topics` | 希望影响的目标主题 |
| `relation` | amend、correct、reconcile、merge、cite 或 conflict |
| `structure` | 单条、桥接、序列或再巩固结构 |
| `schedule` | 调用方解释的生命周期事件序列 |
| `content_genes` | subject、claim、provenance 等内容槽位 |
| `modality` | text、image 或 audio 类型标签 |
| `evidence_channel` | 文本、表格、时间线、OCR、ASR、权威记录或跨模态通道 |

`canonical_key()` 为语义结构提供确定性的去重键，`parent_ids` 和 `mutation_history` 保留候选谱系。

### 2. 候选算子

当前算子库包括：

- `rephrase_for_writer`：调整为结构化事实更新表达；
- `add_retrieval_anchor`：加入与来源主题一致的检索锚点；
- `strengthen_authority`：增加权威来源表达；
- `clarify_temporal_order`：强调新旧记录的时间关系；
- `add_bridge`：连接来源主题与目标主题；
- `add_persistence_schedule`：加入普通后续事件和后台再巩固事件；
- `channel_switch`：在 OCR、ASR、权威记录和时间线通道间切换；
- `cross_channel_corroborate`：构造跨通道一致性表达；
- `preserve_lineage`：保留作用域和候选谱系表达。

生成器还支持两个父 recipe 的交叉组合。随机选择由 `seed` 控制，相同配置可复现相同的候选序列。

### 3. 通道化渲染

`render_candidate()` 将 recipe 转换为字符串载荷。当前实现支持普通文本、Markdown 表格、时间线、OCR 转写、ASR 转写、权威记录、跨通道佐证和冲突记录。

这里的 image/audio 表示候选的类型和转写通道；当前版本不负责生成位图、音频波形或调用多模态编码器。真实媒体渲染器可以在上层系统中根据 recipe 另行实现。

### 4. 固定预算生成

`CandidateGenerator` 按 `budget`、`population_size` 和 `elite_size` 控制生成过程：

1. 对初始 recipe 去重；
2. 分批渲染候选；
3. 调用可选的黑盒评分函数；
4. 选择当前高分候选作为父代；
5. 生成变异和交叉后代；
6. 达到预算或没有新候选时停止。

没有评分函数时，工具仍可作为确定性的候选扩展器使用；此时 `best` 返回生成序列中的第一个候选。

## 安装

需要 Python 3.11 或更高版本。

```powershell
git clone https://github.com/ltsyohb/qoms-attack-generator.git
cd qoms-attack-generator
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

仓库当前没有运行时第三方依赖。

## 快速开始

### 命令行

使用仓库中的本地合成示例生成 8 个候选：

```powershell
qoms-generate examples\seed.json `
  --budget 8 `
  --seed-value 0 `
  --output output\candidates.json
```

若省略 `--output`，结果会打印到标准输出。输出格式为：

```json
{
  "schema": "qoms-attack-candidates-v1",
  "candidates": [
    {
      "recipe": {},
      "payload": "rendered candidate",
      "score": null
    }
  ]
}
```

CLI 只做离线候选生成，因此不会访问任何真实系统，也不会自动产生黑盒分数。

### Python API

```python
from pathlib import Path

from qoms_attack import CandidateGenerator, GenerationConfig
from qoms_attack.cli import load_recipe

seed = load_recipe(Path("examples/seed.json"))

generator = CandidateGenerator(
    GenerationConfig(
        budget=20,
        population_size=4,
        elite_size=2,
        seed=0,
    )
)

result = generator.generate((seed,))

for candidate in result.candidates:
    print(candidate.recipe.id, candidate.payload)
```

## 接入黑盒反馈

调用方可以传入 `score(payload, recipe) -> float`。生成器只读取返回的数值，不要求目标暴露内部记忆或检索状态。

```python
def score(payload, recipe):
    response = authorized_target.submit_and_query(payload)
    return response.public_score

result = generator.generate((seed,), score=score)

print(result.best.score)
print(result.best.payload)
```

评分函数由使用者负责实现。为了保持 query-only 边界，建议评分仅来自目标公开返回的答案、有效性状态或其他可见反馈。

## Seed 格式

最小 JSON seed 示例：

```json
{
  "id": "seed-1",
  "generation": 0,
  "source_topic": "demo-registry-item",
  "target_topics": ["demo-policy"],
  "relation": "amend",
  "structure": "single_note",
  "schedule": ["submit"],
  "content_genes": {
    "subject": "Demo Registry",
    "claim": "the current test value is TARGET 1234",
    "provenance": "authorized-local-fixture"
  },
  "modality": "text",
  "evidence_channel": "plain_text"
}
```

`target_topics` 不能为空，`content_genes` 的键必须唯一。枚举值不合法时，加载过程会直接报错。

## 仓库结构

```text
qoms-attack-generator/
├── qoms_attack/
│   ├── schema.py       # recipe 与候选数据结构
│   ├── operators.py    # 变异和交叉算子
│   ├── render.py       # 通道化字符串渲染
│   ├── engine.py       # 固定预算候选生成
│   └── cli.py          # JSON seed 命令行入口
├── examples/
│   └── seed.json       # 无真实目标的合成示例
├── tests/
│   └── test_generator.py
└── pyproject.toml
```

## 测试

测试只依赖 Python 标准库：

```powershell
python -m unittest discover -s tests -v
```

当前测试检查固定预算、随机种子可复现性，以及黑盒评分下的最优候选选择。

## 范围与限制

- 本工具只生成攻击候选，不执行完整攻击实验。
- 本工具不内置具体 Agent Memory 平台适配器。
- 本工具不生成真实图像或音频，只渲染相应的文本证据通道。
- 本工具不包含实验结果，因此不能单独用于支持攻击成功率或泛化性结论。
- 本工具没有后冻结审计和因果归因模块；这些属于独立的研究评估流程。

请仅在自有系统、本地环境、CTF、教学环境或明确授权的安全评估中使用。

## 引用

QOMS 论文仍在整理中。正式引用信息确定后，可在此处补充 BibTeX。当前如需在内部研究中引用本仓库，请记录仓库 URL、版本号和具体 commit。


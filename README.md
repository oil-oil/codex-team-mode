<p align="center">
  <img src="./assets/readme/agent-map.webp" width="100%" alt="Team Mode：主 Agent 协调探索、执行与复审三条常规路径。">
</p>

# Team Mode 小队模式

Team Mode 是 Codex Skill。主 Agent 负责拆解、未决判断和最终验收；子 Agent 只接手职责明确、确实值得委派的部分。简单任务可以不派任何子 Agent。

## 角色

| 角色 | 默认配置 | 何时使用 |
| --- | --- | --- |
| Explorer | GPT-6 Luna Medium、Fast | 主 Agent 明确需要探索大量代码，先定位主要文件、入口和调用关系。 |
| Executor | GPT-6 Luna Extra High | 目标和文件归属清楚时，围绕预期结果完成实现。 |
| Reviewer | GPT-6 Sol High | 从全新上下文独立检查稳定产物；需要留档时保存 Markdown 审查报告。 |
| ExpertAdvisor | 模型按次选择 | 为复杂决策制定方案，或在主 Agent 难以胜任时执行建模与复杂计算机自动化；也可处理反复未解决的问题。 |

Explorer 默认请求 Fast；其他角色沿用主 Agent 的速度档。GPT-6 Fast 可用时，额度消耗为 Standard 的 2.5 倍，实际生效档位以子 Agent 运行记录为准。

Skill 内置 [Explore](./skills/team-mode/references/explore.md) 与 [Simplify](./skills/team-mode/references/simplify.md) 两份按需读取的参考文档：前者帮助主 Agent 定位大型代码库的主要代码，后者指导明确范围内的代码简化。它们不增加角色，也不规定必须派几个 Agent。

主 Agent 负责拆解用户任务，决定每个子 Agent 的具体问题或交付结果，以及各部分如何衔接。派发时只交代该部分所需的背景、范围和约束；文件位置、故障现象和过往尝试只是线索。子 Agent 在分配的范围内自行选择做法，不重新拆解整个任务。默认以 `fork_turns="none"` 派发；只有 Executor 确实依赖最近对话中的决定时才继承少量相关回合。ExpertAdvisor 不固定模型，由主 Agent 按次选择。子 Agent 提示词与 Skill 调度指令统一使用英语。

## 调度边界

- Explorer 只做大型代码库的文件定位。少量文件查找和普通资料调研由主 Agent 直接处理。
- Executor 只修改分配给自己的目标；并行任务之间不共享写入所有权。
- Reviewer 可以追查与目标相关的重要证据，不预设必须找到某个问题；需要留档时写 Markdown 报告，保持被审查的产物原样。
- 子 Agent 不继续派发 Agent。主 Agent 检查证据、改动和验收结果后才接受交付。

当前 Codex 有内置的通用 `default` Agent。本仓库另提供**可选**的 [`default.toml`](./agents/default.toml) 哨兵：GPT-6 Luna Low，安装后会覆盖内置 `default`，拒绝漏传角色的派发。Team Mode 不依赖它。个人哨兵会影响其他 Codex 任务，因此默认安装只复制四个工作角色；需要严格拦截时再单独安装。已有哨兵可移到 `~/.codex/agents-disabled/` 可恢复地停用。

## 安装

```bash
npx skills add oil-oil/codex-team-mode
```

Skill 和角色配置分开安装。将 [`agents/`](./agents) 中的 `Explorer.toml`、`Executor.toml`、`Reviewer.toml`、`ExpertAdvisor.toml` 复制到 `~/.codex/agents/`；只给一个项目使用时，复制到该项目的 `.codex/agents/`。角色未立即出现时，新建 Codex 任务或重启。详见[角色配置说明](./skills/team-mode/references/custom-agents.md)。

```text
使用 $team-mode 完成任务。只派发有明确收益的子 Agent，主 Agent 负责最终验收。
```

## 诊断

`current_model.py` 按需从本地任务日志读取主 Agent 实际模型；`usage_by_model.py` 统计本地保留会话的模型和用量。日志可能不完整，费用按注明日期的 Standard 费率估算，不能当作账单。

```bash
python3 skills/team-mode/scripts/current_model.py
python3 skills/team-mode/scripts/usage_by_model.py --days 7 --by-agent --json
python3 -m unittest discover -s tests
```

现行 Codex 的自定义角色 TOML 中固定的模型与思考档会优先于派发时传入的值，因此按次选模使用不固定模型的 ExpertAdvisor；参见[官方子 Agent 文档](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)。

<p align="center">
  <a href="https://github.com/oil-oil/beautify-github-readme"><img src="./assets/readme/made-with-beautify.svg" width="300" alt="README 使用 beautify-github-readme 制作"></a>
</p>

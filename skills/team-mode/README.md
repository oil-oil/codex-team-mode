# Team Mode 小队模式

主 Agent 按任务价值协调四个工作角色：Explorer 定位大型代码库的主要文件，Executor 完成有边界的实现，Reviewer 独立复审并可按需留存 Markdown 报告，ExpertAdvisor 处理复杂决策、建模、复杂计算机自动化或反复未解决的问题。简单任务可以不派子 Agent。

主 Agent 负责拆解任务并分配具体问题或交付结果；文件提示和故障猜测只是线索，子 Agent 在分配的范围内自行选择做法。

四个角色模板位于仓库 [`agents/`](../../agents/)；`default.toml` 是可选的 GPT-6 Luna Low 派发哨兵，不是 Team Mode 的必要条件。安装和模型优先级见[角色配置说明](references/custom-agents.md)。

[Explore](references/explore.md) 在新任务开始、需要摸清大型代码库时使用。一个连贯问题默认派一个 Explorer；只有存在互不依赖的子系统或问题时才增加数量。

[Simplify](references/simplify.md) 在提交前检查本次改动。窄范围改动默认派一个 Reviewer；宽范围或高风险改动可按独立审查视角并行派多个 Reviewer。Reviewer 只报告建议，由主 Agent 或明确负责修改的 Executor 应用；受审文件发生变化后，再由一个新的 Reviewer 检查最终 diff。若受审文件未改变，原审查任务覆盖正确性和遗漏检查时可复用；否则仍需派新的 Reviewer。

提示词统一使用英语。派发默认不继承主对话；Reviewer 和 ExpertAdvisor 必须从空历史上下文开始，Executor 只有确实依赖最近对话中的决定时才继承少量回合。ExpertAdvisor 不固定模型，主 Agent 选择可用的更强模型并核查其方案或执行结果。

本地诊断可按需运行 `python3 scripts/current_model.py` 和 `python3 scripts/usage_by_model.py --days 7 --by-agent --json`。完整用法见[项目说明](../../README.md)。

## 适用边界与依赖

Team Mode 适用于可明确分工、独立复审或确实需要专家处理复杂问题的任务；普通问答和短任务由主 Agent 直接完成。Skill 需要支持自定义子 Agent 的 Codex；本地诊断脚本需要 Python 3.10+ 和保留的会话日志。

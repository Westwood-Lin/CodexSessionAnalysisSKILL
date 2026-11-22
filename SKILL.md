---
name: session-analysis
description: Analyze agent conversation logs with deterministic parsing, statistics, tool and network call counts, prompt catalogs, and auditable outputs. LLM is optional.
---

# 对话分析 Skill

## 1. 能力定义

- 能力名称：对话分析
- 调用名：`session_analysis`
- 版本：`1.0`
- 用途：读取一个程序可访问的对话源，统计参与者消息、工具调用和网络请求，围绕用户提示进行主题聚类，并返回统计数据、`UserPromptClasses` 表和进一步分析。
- 典型问题：一次长期人机协作究竟包含多少轮对话、用户围绕哪些主题提问、各主题如何随时间推进、哪些提示属于同一任务阶段。

本能力以 Codex 线程 `<THREAD_ID>` 的分析过程为基准案例。案例线程可通过 `codex://threads/<THREAD_ID>` 访问。

## 2. 输入契约

### 2.1 必需参数

唯一必需参数为 `conversation_source`。它表示一个程序能够读取的对话文件或对话内容，允许以下形式：

1. 会话标识符，例如 Codex `sessionId` 或 `threadId`；执行环境负责将标识符解析为实际记录。
2. 有读取权限的本地文件路径或 `file:` URI，例如 `.jsonl`、`.json`、`.md`、`.txt`。
3. 可访问的网络 URI，例如 `https://.../conversation.jsonl`。
4. 直接复制的对话文本；无法获得结构化日志时，按说话人标签和段落边界解析。

调用示例：

```text
invoke session_analysis codex://threads/<THREAD_ID>
invoke session_analysis file:///path/to/session.jsonl
invoke session_analysis https://example.org/export/conversation.jsonl
invoke session_analysis "user: ...\nagent: ..."
```

### 2.2 可选参数

- `cutoff`：统计截止时间或消息序号。默认截止到分析请求进入日志的时刻，避免本次分析产生的消息和工具调用反向污染统计。
- `speaker_map`：将源格式中的角色映射到 `user`、`agent`、`tool`、`system`。
- `exclude_rules`：排除平台注入消息的规则，例如纯 `<environment_context>`、`<recommended_plugins>`。
- `cluster_count`：期望主题数；缺省时由相似度阈值与可解释性共同确定。
- `similarity_weights`：TF-IDF、BM25、Levenshtein、关键词锚点和时序平滑的权重。
- `output_format`：`markdown`、`json`、`csv` 或其组合。
- `include_prompt_catalog`：是否附带逐条编号的提示摘要与类别。

## 3. 返回契约

必须返回以下三部分；需要落盘时建议生成 `session_analysis.md`、`session_analysis.json` 和 `user_prompts.csv`。

### 3.1 统计数据

至少包含：

- 有效用户提示数、原始用户消息数和剔除数；
- agent 消息数，并在源数据支持时区分 final answer 与 commentary；
- 工具调用轮数；
- 网络请求轮数；
- 聚类主题数；
- 原始对话和结果文件的可访问 URI。

“轮”默认按日志中的消息或调用事件计，不强行把 user 与 agent 消息配成一问一答。工具调用按调用事件计；网络请求是工具调用的子集，按实际 web、browser、HTTP 或 search 类工具调用计。若源数据无法可靠区分某项，必须返回 `unknown` 并解释限制，不得猜测。

### 3.2 UserPromptClasses 表

| 序号 | UserPrompt类别名 | 阶段 | 对话数 | 用户消息序列 |
|---:|---|---|---:|---|

用户有效提示按出现顺序编号为 `1, 2, 3, ...`。`用户消息序列` 必须是 `list[int]`，其中每个编号只属于一个类别；所有类别的 `对话数` 之和必须等于有效用户提示总数。

### 3.3 更多分析

根据数据质量和用户需要，进一步返回：

- 主题演进、阶段转折点和跨阶段反复出现的主题；
- 长度异常、重复提示、retry/continue、截图型短提示和工具操控型提示；
- 用户意图、已获得的能力、尚未完成的目标；
- 高代表性提示、主题间关系和可复现的对话 trace；
- 分类置信度、边界样本及聚类方法限制；
- 可选的 agent 回答质量、工具依赖和网络依赖分析。

## 4. 执行流程

### 步骤一：定位并冻结数据源

1. 将 `sessionId`、URI、路径或文本解析为可读取内容。
2. 记录规范化后的源 URI、文件大小、修改时间；需要强复现时记录 SHA-256。
3. 确定 `cutoff`。默认找到当前分析请求对应的最后一条有效用户消息，只读取到该记录为止。
4. 不修改原始对话文件；网络源应缓存只读快照并保留原 URI。

### 步骤二：解析统一事件模型

将不同来源适配为统一结构：

```json
{
  "timestamp": "...",
  "role": "user|agent|tool|system",
  "message_type": "message|tool_call|tool_output|context",
  "phase": "final_answer|commentary|...",
  "text": "...",
  "tool_name": "..."
}
```

Codex `.jsonl` 的参考解析规则：

- `response_item.payload.type == "message"` 且 `role == "user"`：原始用户消息；
- `role == "assistant"`：agent 消息，使用 `phase` 区分 final answer/commentary；
- `payload.type` 以 `call` 结尾：工具调用；若外层为 `exec`，还应从其输入中解析 `tools.<actual_tool>(...)` 得到实际内层工具；
- `web__run`、browser、HTTP、search 类实际工具计入网络请求；
- 纯环境上下文和插件推荐清单属于平台注入，不作为用户提示参与聚类。

### 步骤三：清洗与编号用户提示

1. 保留用户的真实请求，删除附件清单、图片标签、环境 XML 和超长机器模型 XML 等模板噪声；可保留 `Event-B model XML` 一类占位符以维持语义。
2. 统一大小写、空白和路径表示，但在逐条目录中保留原始文本引用。
3. 对中文生成单字与双字特征，对英文提取单词、数字和技术标识符。
4. 有效用户提示按时间顺序重新编号。原始消息编号可作为审计字段保留，但不能替代输出中的连续编号。

### 步骤四：计算相似度并聚类

推荐使用可解释的混合相似度：

```text
score = 0.44 × TF-IDF cosine
      + 0.24 × symmetric BM25
      + 0.10 × normalized token Levenshtein
      + 0.22 × lexical-anchor score
```

- TF-IDF 表示共享术语和字符 n-gram；
- 对称 BM25 同时计算 A 查询 B 与 B 查询 A，并用自相似分数归一化；
- Levenshtein 捕捉改写、短重复和拼写接近；
- lexical anchors 使用领域词，例如 `Rodin`、`PO`、`Refinement`、`ProB`、`model checking`；
- 对截图、`继续`、`retry` 等词汇证据不足的提示，使用时间邻接平滑，使其继承最近的内容型上下文。参考两轮平滑增益：前一条 `+0.055`，后一条 `+0.035`。

主题标签应由代表性高权词和阶段上下文生成，再人工检查边界样本。人工检查可以调整类别原型或规则，但不得直接伪造消息编号；调整后必须重新运行，并验证覆盖总数。

### 步骤五：统计、验证与输出

至少执行以下一致性检查：

1. `sum(UserPromptClass.对话数) == 有效用户提示数`；
2. 所有用户消息编号恰好出现一次，无遗漏、无重复；
3. `有效提示数 + 剔除数 == 原始用户消息数`；
4. 网络请求数不大于工具调用数；
5. 输出保留源 URI、截止口径、计数定义、算法权重和限制；
6. JSON、CSV 与 Markdown 中的主题数、序列和计数相互一致。

## 5. 基准案例：线程 <THREAD_ID>

### 5.1 统计数据

```text
user：58 条有效提示；原始 role=user 64 条，剔除 6 条平台环境/插件清单
agent：116 条消息，其中 final answer 55 条、commentary 61 条
工具调用：106 轮
网络请求：6 轮
聚类结果：10 个主题
```

可访问 URI：

- `codex://threads/<THREAD_ID>`
- `file:///<LOCAL_PATH>>.jsonl`
- `file:///<LOCAL_PATH>`
- `file:///<LOCAL_PATH>`
- `file:///<LOCAL_PATH>`

### 5.2 UserPromptClasses

| 序号 | UserPrompt类别名 | 阶段 | 对话数 | 用户消息序列 |
|---:|---|---|---:|---|
| 1 | 培训环境、材料与30分钟计划 | 启动与课程设计 | 5 | `[1, 2, 3, 4, 5]` |
| 2 | Chapter 2阅读、复习与Skim/Scan | 教材阅读 | 6 | `[6, 7, 27, 28, 29, 30]` |
| 3 | Rodin PO生成、交互证明与证明器 | 初始模型验证与排障 | 19 | `[8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 33, 34, 47]` |
| 4 | 学习过程的Issue与制品记录 | 过程沉淀 | 2 | `[25, 41]` |
| 5 | 本地Rodin/ProB启动与PowerShell配置 | 工具环境配置 | 3 | `[26, 42, 49]` |
| 6 | DLF、Theorem与抽象模型m0 | 抽象模型完整性分析 | 3 | `[22, 31, 32]` |
| 7 | R1细化、胶合不变量、收敛与Variant | 第一轮Refinement | 8 | `[35, 36, 37, 38, 39, 40, 44, 45]` |
| 8 | 阶段复盘、下一步清单与Event-B Agent目标 | 复盘与规划 | 3 | `[43, 46, 48]` |
| 9 | ProB动画、模型检查与反例复现 | R1动态验证 | 8 | `[50, 51, 52, 53, 54, 55, 56, 57]` |
| 10 | 会话计数与UserPromptClasses聚类 | 会话元分析 | 1 | `[58]` |

### 5.3 更多分析

该线程呈现出清楚的能力递进：先建立培训环境与时间受限的阅读计划，再进入 Rodin 的 PO 生成和交互证明；随后从抽象模型 `m0` 进入第一轮细化 `m1`，理解胶合不变量、收敛与 Variant；最后用 ProB animation 和 model checking 主动破坏 guard、定位 invariant violation，并通过 History 复现反例。主题 3 有 19 条提示，是最长的工具学习与排障阶段；主题 7 和主题 9 各 8 条，分别对应静态证明建模和动态反例验证。

用户的目标并非只读完教材，而是形成“需求—Event-B 模型—Rodin PO—外部证明器—ProB 状态空间与反例”的端到端工作流，并进一步构想能够自动生成和检查模型的 Event-B Agent。重复出现的 `retry`、`继续`、截图提示和即时工具操作说明，这类学习对话应把相邻上下文视为重要特征，不能只对孤立消息做词袋聚类。

本案例的主要限制是主题数和可读标签使用了领域原型与关键词锚点，因此属于可解释的半监督聚类，而不是完全无监督聚类。若迁移到其他领域，应替换 lexical anchors，或先用层次聚类生成候选簇，再由高权词命名；计数与序列验证规则保持不变。

## 6. 失败处理与安全边界

- session ID 无法解析时，要求用户提供可读路径、URI 或粘贴内容。
- 网络 URI 需要认证或无权限时，不尝试绕过权限；说明缺失并请求可访问副本。
- 日志可能包含密钥、个人路径、邮件或附件内容；输出前进行最小必要披露和敏感信息脱敏。
- 不把计划制品、未完成工具调用或 agent 自述当成已经完成的结果。
- 无法识别工具内层调用时，可统计外层调用并将工具名标为 `unresolved`，同时说明网络请求数可能低估。



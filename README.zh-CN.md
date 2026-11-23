# Codex 会话分析 Skill

[English](README.md) | [简体中文](README.zh-CN.md)

一个可复现、LLM 可选的工具包，用于分析 Codex 和其他 Agent 的会话日志。

它可以解析 JSONL 会话事件，统计用户消息、Agent 消息、工具调用和网络请求，删除平台注入的上下文，生成带连续编号的用户提示目录，并记录源文件哈希以便审计和复现。

> **安全警告：不要使用本 Skill 处理包含 API 密钥、密码、Token、私有证书、个人数据或机密业务信息的会话。** 脱敏只是尽力处理，不能作为安全边界。请先制作脱敏副本，再进行分析。

## 哪些功能需要 LLM

| 能力 | 是否需要 LLM | 说明 |
|---|---:|---|
| 读取 JSONL、JSON 或导出的文本 | 否 | 使用 Python 标准库解析。 |
| 统计消息、工具调用和网络请求 | 否 | 使用确定性的事件和工具名称规则。 |
| 删除已知的平台注入上下文 | 否 | 使用显式标记和解析规则。 |
| 用户提示编号和脱敏 | 否 | 使用确定性的过滤规则和正则表达式。 |
| TF-IDF/BM25 风格聚类 | 否 | 可以使用本地确定性实现或其他本地程序。 |
| 解释用户意图、阶段变化或回答质量 | 可选 | LLM 可以在已计算证据的基础上改进解释。 |
| 从自然语言请求中选择数据源 | 通常需要 | 宿主 Agent 可能使用 LLM 理解用户请求。 |

因此，直接运行 CLI 可以完成当前已经实现的确定性统计和提示目录分析，不需要 LLM。主题聚类已在 `SKILL.md` 中定义，但完整的独立 CLI 仍在开发中。通过 Agent 调用时，整体流程属于 LLM 辅助工作流，因为宿主模型需要解释请求，也可能负责撰写分析说明。

## 快速开始

要求使用 Python 3.10 或更高版本。当前解析器只依赖 Python 标准库。

```powershell
# 克隆公开仓库
git clone https://github.com/Westwood-Lin/CodexSessionAnalysisSKILL.git
cd CodexSessionAnalysisSKILL

# 分析 Codex JSONL 导出文件
python .\analyze_jsonl.py .\path\to\session.jsonl --catalog > analysis.json
```

输出包含源 URI、文件大小、SHA-256、时间戳、消息统计、工具统计、网络请求统计和工具频次。

## Skill 安装

将 `SKILL.md` 复制到 Agent 平台使用的 skills 目录。对于本地 Codex 环境，可以运行：

```powershell
$skillDir = Join-Path $env:USERPROFILE '.codex\skills\session-analysis'
New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
Copy-Item .\SKILL.md $skillDir\SKILL.md -Force
```

之后，宿主 Agent 可以依据 `SKILL.md` 中的契约定位数据源、冻结统计截止点、运行解析器，并生成 Markdown、JSON 和 CSV 制品。

## 仓库内容

- `SKILL.md`：输入、输出、解析、聚类、校验和安全边界契约。
- `analyze_jsonl.py`：无第三方依赖的确定性 JSONL 统计和用户提示目录 CLI。
- `examples/`：小型脱敏测试样例。

## 范围和限制

解析器不会自行推断用户意图或回答质量。这些解释需要显式规则、人工复核或可选的 LLM 层。解析器不会修改源日志。当包装器隐藏了内部工具名称时，网络请求统计可能低于实际数量。处理任何会话前请先阅读 [SECURITY.md](SECURITY.md)。

## TODO

- 尽快调研并实现快速、可靠的敏感会话脱敏与加密方案。
- 完成 `SKILL.md` 中定义的独立确定性聚类 CLI。

## 许可证

MIT。详见 `LICENSE`。

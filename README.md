# Codex Session Analysis Skill

[English](README.md) | [简体中文](README.zh-CN.md)

A reproducible, LLM-optional toolkit for analyzing Codex and other agent conversation logs.

It parses JSONL session events, counts user and agent messages, tool calls, and network calls, removes injected platform context, produces a numbered prompt catalog, and records source hashes for auditability.

> **SECURITY WARNING — DO NOT USE THIS SKILL ON CONVERSATIONS CONTAINING API KEYS, PASSWORDS, TOKENS, PRIVATE CERTIFICATES, PERSONAL DATA, OR CONFIDENTIAL BUSINESS INFORMATION.** Redaction is best-effort and is not a security boundary. Make a sanitized copy before analysis.

## What requires an LLM

| Capability | LLM required? | Details |
|---|---:|---|
| Read JSONL, JSON, or exported text | No | The parser uses Python standard-library code. |
| Count messages, tools, and network calls | No | Deterministic event and tool-name rules. |
| Remove known platform-injected context | No | Explicit markers and parser rules. |
| Prompt numbering and redaction | No | Deterministic filtering and regular expressions. |
| TF-IDF/BM25-style clustering | No | Use a local deterministic implementation or another local program. |
| Explain intent, stage transitions, or quality | Optional | An LLM can improve interpretation of the computed evidence. |
| Choose a source from a natural-language request | Usually | The host Agent may use an LLM to interpret the request. |

The direct CLI path is therefore **0-LLM for the currently implemented deterministic statistics and prompt-catalog analysis**. Topic clustering is specified by `SKILL.md` but its complete CLI implementation is still being developed. An Agent-mediated invocation is an LLM-assisted workflow because the host model interprets the request and may write explanations.

## Quick start

Requirements: Python 3.10 or newer. The included parser uses only the Python standard library.

```powershell
# Clone the public repository
git clone https://github.com/Westwood-Lin/CodexSessionAnalysisSKILL.git
cd CodexSessionAnalysisSKILL

# Analyze a Codex JSONL export
python .\analyze_jsonl.py .\path\to\session.jsonl --catalog > analysis.json
```

The result includes source URI, byte count, SHA-256, timestamps, message counts, tool counts, network-call counts, and tool frequencies.

## Skill installation

Copy `SKILL.md` into the skills directory used by your Agent platform. For a local Codex checkout:

```powershell
$skillDir = Join-Path $env:USERPROFILE '.codex\skills\session-analysis'
New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
Copy-Item .\SKILL.md $skillDir\SKILL.md -Force
```

The host Agent can then use the contract in `SKILL.md` to locate a source, freeze a cutoff, run the parser, and produce Markdown, JSON, and CSV artifacts.

## Repository contents

- `SKILL.md` — input, output, parsing, clustering, validation, and safety contract.
- `analyze_jsonl.py` — dependency-free deterministic JSONL statistics and prompt-catalog CLI.
- `examples/` — small sanitized fixtures for local testing.

## Case study

The [Event-B session case study](examples/eventb-session/README.md) contains sanitized Markdown and JSON reports plus a truncated prompt catalog. It shows a 61-prompt session progressing through Event-B training, Rodin proof work, refinement, ProB counterexamples, and Skill formalization.

## Scope and limitations

The parser does not claim to infer intent or quality. Those interpretations require explicit rules, human review, or an optional LLM layer. It never modifies the source log. Network-call counts are lower bounds when a wrapper hides the inner tool name. Read [SECURITY.md](SECURITY.md) before processing any conversation.

## TODO

- Research and implement a fast, reliable redaction and encryption workflow for sensitive conversation data as soon as practical.
- Complete the standalone deterministic clustering CLI described in `SKILL.md`.

## License

MIT. See `LICENSE`.



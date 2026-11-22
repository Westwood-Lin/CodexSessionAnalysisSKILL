# Codex Session Analysis Skill

A reproducible, LLM-optional toolkit for analyzing Codex and other agent conversation logs.

It parses JSONL session events, counts user and agent messages, tool calls, and network calls, removes injected platform context, produces a numbered prompt catalog, and records source hashes for auditability.

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

The direct CLI path is therefore **0-LLM for the supplied deterministic analysis**. An Agent-mediated invocation is an LLM-assisted workflow because the host model interprets the request and may write explanations.

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

## Scope and limitations

The parser does not claim to infer intent or quality. Those interpretations require explicit rules, human review, or an optional LLM layer. It never modifies the source log. Network-call counts are lower bounds when a wrapper hides the inner tool name.

## License

MIT. See `LICENSE`.

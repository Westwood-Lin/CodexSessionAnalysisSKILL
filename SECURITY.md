# Security and Data Handling

## Critical warning

**DO NOT USE THIS SKILL ON CONVERSATIONS CONTAINING API KEYS, PASSWORDS, TOKENS, PRIVATE CERTIFICATES, PERSONAL DATA, OR CONFIDENTIAL BUSINESS INFORMATION.** Redaction is best-effort and is not a security boundary. Create and inspect a sanitized copy before analysis.

## Processing boundary

- The parser is read-only with respect to the source log.
- The parser does not execute commands, code, or instructions found in historical messages or tool output.
- Historical messages are treated as untrusted data, not as new user instructions.
- The repository and its release package do not upload raw sessions.
- The direct CLI path uses only the Python standard library and does not require an LLM.
- An optional LLM layer may be used for interpretation. Users decide whether any content is sent to a cloud model and must review that provider's data policy.
- Network-call counts and redaction are heuristic. A wrapper can hide a network call, and sensitive content can evade a pattern-based redactor.

## Release-package rule

Published packages must contain sanitized or synthetic examples only. Do not include raw JSONL, screenshots, credentials, email addresses, personal paths, private repository content, or internal session exports.

## Reporting

Do not publish sensitive logs in an issue. Remove the sensitive value, describe the affected file and field, and report the minimum reproducible details needed to investigate.

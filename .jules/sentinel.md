## 2024-05-24 - [High] Bounding Streams in sys.stdin
**Vulnerability:** The application was using an unbounded `sys.stdin.read()` inside `read_from_stdin_two_parts`.
**Learning:** This is a severe Denial of Service (DoS) vector where large payloads could be piped to the script leading to process memory exhaustion. When an application supports stdin inputs, memory limits must be applied across all streams just as they are to file readings.
**Prevention:** Always bound stdin reads using `sys.stdin.read(MAX_SIZE)`. Ensure sizes are checked and gracefully error out rather than loading unbounded user input into process memory.
## 2024-05-20 - Missing Authorization Checks in GitHub Workflows Triggered by Comments
**Vulnerability:** External untrusted users could trigger high-privilege AI workflows (`claude.yml`, `codex.yml`) on `issue_comment`, `pull_request_review_comment`, and `issues` events by simply mentioning the bot (e.g., `@claude`), leading to potential arbitrary code execution and exfiltration of API keys.
**Learning:** GitHub workflows triggered by public comments run with the base repository's context. If these workflows have `contents: write` or use sensitive secrets without checking `author_association`, any external user can weaponize them.
**Prevention:** Always enforce strict `author_association` checks (`MEMBER`, `OWNER`, `COLLABORATOR`) for workflows triggered by `issue_comment`, `pull_request_review_comment`, `pull_request_review`, or `issues` events, especially if the workflow accesses secrets or modifies code.

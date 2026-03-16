## 2024-05-30 - [Unbounded Stdin DoS Prevention]
**Vulnerability:** Unbounded `sys.stdin.read()` inside `read_from_stdin_two_parts()` could lead to a Denial of Service (DoS) via memory exhaustion if the user piped a significantly large stream.
**Learning:** Even though `safe_read_file` correctly restricted file read limits, functions taking input from standard streams (like stdin) might inadvertently bypass memory limits.
**Prevention:** Bound `sys.stdin.read(size)` using the predefined application limits and validate the resulting size.

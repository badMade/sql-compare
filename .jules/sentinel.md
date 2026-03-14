## 2024-05-08 - Unbounded sys.stdin.read() DoS risk
**Vulnerability:** The application used `sys.stdin.read()` without any size limit when reading from piped input (`--stdin`). This created a Denial of Service (DoS) vulnerability where a malicious actor could pipe an infinite stream (e.g., from `/dev/zero`), causing the application to consume all memory and crash.
**Learning:** Even when reading from standard input in CLI applications, memory exhaustion is a valid DoS vector if the stream is unbound. Built-in functions like `sys.stdin.read()` in Python will attempt to load the entire stream into memory by default.
**Prevention:** Always provide a maximum byte limit to read functions (e.g., `sys.stdin.read(MAX_LIMIT)`), and validate the read size against expectations.

## 2024-03-12 - Unbounded sys.stdin.read in CLI Scripts
**Vulnerability:** Unbounded memory consumption DoS risk caused by calling `sys.stdin.read()` without a size limit.
**Learning:** Even though file inputs were protected by `MAX_FILE_SIZE_BYTES` logic, piped `stdin` data completely bypassed these checks, representing an inconsistent defense-in-depth posture. This is a common pattern in CLI tools that allow standard input reading.
**Prevention:** Always bound reads from standard input to a maximum acceptable size limit (e.g., `sys.stdin.read(LIMIT)`). If the returned length exceeds the expected bounds, abort early with a clear error.

## 2024-05-24 - [High] Bounding Streams in sys.stdin
**Vulnerability:** The application was using an unbounded `sys.stdin.read()` inside `read_from_stdin_two_parts`.
**Learning:** This is a severe Denial of Service (DoS) vector where large payloads could be piped to the script leading to process memory exhaustion. When an application supports stdin inputs, memory limits must be applied across all streams just as they are to file readings.
**Prevention:** Always bound stdin reads using `sys.stdin.read(MAX_SIZE)`. Ensure sizes are checked and gracefully error out rather than loading unbounded user input into process memory.

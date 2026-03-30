## 2024-05-24 - [High] Bounding Streams in sys.stdin
**Vulnerability:** The application was using an unbounded `sys.stdin.read()` inside `read_from_stdin_two_parts`.
**Learning:** This is a severe Denial of Service (DoS) vector where large payloads could be piped to the script leading to process memory exhaustion. When an application supports stdin inputs, memory limits must be applied across all streams just as they are to file readings.
**Prevention:** Always bound stdin reads using `sys.stdin.read(MAX_SIZE)`. Ensure sizes are checked and gracefully error out rather than loading unbounded user input into process memory.

## 2024-05-18 - [API Key Exposure in URL]
**Vulnerability:** The Gemini API key (`GOOGLE_API_KEY`) was being passed in the URL query string in the `.github/workflows/jules.yml` workflow (`?key=${process.env.GOOGLE_API_KEY}`).
**Learning:** Passing sensitive credentials like API keys in URLs exposes them to network logs, proxy servers, and browser history, even over HTTPS. This violates the principle of keeping secrets out of transport metadata.
**Prevention:** Always pass API keys and other secrets using HTTP headers (e.g., `x-goog-api-key` or `Authorization: Bearer <key>`) instead of query parameters.

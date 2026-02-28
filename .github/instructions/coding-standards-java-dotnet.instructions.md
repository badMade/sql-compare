---
applyTo:
  "**/*.{java,kt,cs,fs,vb,sln,csproj,props,targets}"
---

# Java & .NET Standards

- Clear interfaces; respect DI rules.
- Follow checked-exceptions policy (Java) and established error models.
- Keep modules cohesive; no surprise I/O in constructors.
- Strong typing; explicit nullability; avoid reflection unless justified.

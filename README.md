# SQL Compare

A tool to compare two SQL statements via CLI, Tkinter GUI, or Web interface.
Mirrors all features:
- Whitespace-only comparison
- Exact token comparison
- Canonical comparison (Join reordering, Select/Where sorting)

## Installation

```bash
pip install .
```

## Usage

### CLI
```bash
sql-compare file1.sql file2.sql --mode both
```

### GUI (Desktop)
```bash
sql-compare
```

### Web
```bash
sql-compare --web
```

# SQL Compare - Jules' Notes

This file contains notes and an overview of the `sql-compare` project for Jules.

## Project Overview

`sql-compare` is a tool for comparing two SQL statements. It provides both a GUI (using Tkinter) and a CLI for automation. It's written in pure Python and relies only on the standard library.

## Key Features

- **Comparison Modes:**
  - `exact`: Checks for exact token equality (ignores case, comments, and whitespace).
  - `canonical`: Ignores harmless reordering (SELECT list, WHERE AND terms, JOINs).
- **Reports:** Generates color-coded HTML or TXT reports.
- **Portability:** Single file `sql_compare.py` implementation, no external dependencies.
- **CI/CD Integration:** Designed to be used in automated pipelines (GitHub Actions, Azure Pipelines).

## Important Files

- `sql_compare.py`: The main script containing the logic for both GUI and CLI.
- `README.md`: Main documentation.
- `docs/USAGE.md`: Detailed usage instructions.
- `docs/CI.md`: Examples for CI/CD integration.
- `examples/`: Contains example SQL files for testing.

## Usage

### GUI
Run `python sql_compare.py` without arguments.

### CLI
```bash
python sql_compare.py file1.sql file2.sql --mode canonical --report report.html
```

See `docs/USAGE.md` for more details.

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote


START_MARKER = "<!-- TODO:GENERATED:START -->"
END_MARKER = "<!-- TODO:GENERATED:END -->"
TODO_RE = re.compile(r"\btodo\b(?:\s*:|\s+-|\s+)?", re.IGNORECASE)

DEFAULT_PREAMBLE = """# TODO

## Notes

Write free-form notes here. Everything above the generated marker is preserved.
"""

IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "archive",
    "docs/_build",
    "htmlcov",
    "log",
    "outputs",
    "pages",
    "venv",
}

IGNORED_FILES = {
    "TODO.md",
    "scripts/update_todo.py",
    "src/ExpenseForecast_old.py",
    "src/old_EF.txt",
    "src/old_ForecastHandler.txt",
    "src/old_ForecastRunner.txt",
    "src/ols_remaining_EF.txt",
}

TEXT_SUFFIXES = {
    ".bash",
    ".cfg",
    ".ini",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Todo:
    text: str
    path: str
    line_number: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update TODO.md from TODO comments in repository text files."
    )
    repo_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=repo_root)
    parser.add_argument("--todo-file", type=Path, default=repo_root / "TODO.md")
    return parser.parse_args()


def is_ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    if relative in IGNORED_FILES:
        return True
    if any(relative == ignored or relative.startswith(f"{ignored}/") for ignored in IGNORED_DIRS):
        return True
    return path.suffix.lower() not in TEXT_SUFFIXES


def extract_todo(line: str) -> str | None:
    match = TODO_RE.search(line)
    if match is None:
        return None

    text = line[match.start() :].strip()
    if text.endswith("-->"):
        text = text[:-3].rstrip()
    if text.endswith("*/"):
        text = text[:-2].rstrip()
    return text or None


def scan_todos(root: Path) -> list[Todo]:
    todos: list[Todo] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_ignored(path, root):
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(lines, start=1):
            text = extract_todo(line)
            if text is not None:
                todos.append(Todo(text=text, path=relative, line_number=line_number))

    return todos


def render_generated_block(todos: list[Todo]) -> str:
    lines = [
        START_MARKER,
        "## Generated TODOs",
        "",
        "_Updated by `python3 scripts/update_todo.py`._",
        "",
        "<pre>",
    ]

    if todos:
        width = max(len(todo.text) for todo in todos)
        for todo in todos:
            text = escape(f"{todo.text:<{width}}")
            href = escape(f"{quote(todo.path, safe='/')}#L{todo.line_number}", quote=True)
            label = escape(f"{todo.path}:{todo.line_number}")
            lines.append(f'{text} - <a href="{href}">{label}</a>')
    else:
        lines.append("(none)")

    lines.extend(["</pre>", END_MARKER, ""])
    return "\n".join(lines)


def update_todo_file(todo_file: Path, generated_block: str) -> None:
    if todo_file.exists():
        current = todo_file.read_text(encoding="utf-8")
        if START_MARKER in current:
            preamble = current.split(START_MARKER, maxsplit=1)[0].rstrip()
        else:
            preamble = current.rstrip()
    else:
        preamble = DEFAULT_PREAMBLE.rstrip()

    todo_file.write_text(f"{preamble}\n\n{generated_block}", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    todo_file = args.todo_file.resolve()
    todos = scan_todos(root)
    update_todo_file(todo_file, render_generated_block(todos))
    print(f"Updated {todo_file.relative_to(root)} with {len(todos)} TODOs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

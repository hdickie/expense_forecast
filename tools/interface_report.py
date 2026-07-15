from __future__ import annotations

import ast
from pathlib import Path


SRC_ROOT = Path("src/expense_forecast")
TEST_ROOT = Path("tests")

INTERESTING_METHODS = {
    "__eq__",
    "__ne__",
    "__add__",
    "__sub__",
    "__hash__",
    "__str__",
    "__repr__",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
}


def has_interface_report_tag(
    node: ast.AST,
    tag: str,
) -> bool:
    docstring = ast.get_docstring(node) or ""
    return f"@interface-report: {tag}" in docstring


def function_raises_not_implemented(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise):
            exc = node.exc

            if isinstance(exc, ast.Call):
                exc = exc.func

            if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                return True

    return False


def get_classes_from_file(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text())

    classes = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        methods = {}

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if has_interface_report_tag(item, "ignore"):
                    continue
                methods[item.name] = {
                    "line": item.lineno,
                    "stub": function_raises_not_implemented(item),
                }

        classes.append(
            {
                "class_name": node.name,
                "path": path,
                "methods": methods,
            }
        )

    return classes


def get_tests_from_file(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text())

    tests = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            tests.append(
                {
                    "test_name": node.name,
                    "test_class": None,
                    "path": path,
                    "line": node.lineno,
                }
            )

        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    tests.append(
                        {
                            "test_name": item.name,
                            "test_class": node.name,
                            "path": path,
                            "line": item.lineno,
                        }
                    )

    return tests


def find_probable_tests_for_class(class_name: str, all_tests: list[dict]) -> list[dict]:
    matches = []

    for test in all_tests:
        haystack = " ".join(
            [
                test["test_name"],
                test["test_class"] or "",
                str(test["path"]),
            ]
        )

        if class_name.lower() in haystack.lower():
            matches.append(test)

    return matches

hard_coded_status_symbol_overrides = {
# ('Account', '__add__'):'✅', # ❌ # ⬛
('Account', '__add__'):'⬛',
}

def status_symbol(class_info: dict, method_name: str) -> str:
    methods = class_info["methods"]

    if (class_info["class_name"], method_name) in hard_coded_status_symbol_overrides.keys():
        return hard_coded_status_symbol_overrides[(class_info["class_name"], method_name)]

    if method_name not in methods:
        return "—"

    if methods[method_name]["stub"]:
        return "STUB"

    return "OK"


def main() -> None:
    source_files = sorted(SRC_ROOT.glob("*.py"))
    test_files = sorted(TEST_ROOT.rglob("test_*.py"))

    classes = []
    for path in source_files:
        classes.extend(get_classes_from_file(path))

    tests = []
    for path in test_files:
        tests.extend(get_tests_from_file(path))

    print()
    print("CLASS / METHOD MATRIX")
    print("=" * 120)

    header = ["Class".ljust(40), "File".ljust(65), *sorted([im.ljust(10) for im in INTERESTING_METHODS]), "Probable tests"]
    print("\t".join(header))

    for class_info in classes:
        probable_tests = find_probable_tests_for_class(class_info["class_name"], tests)

        row = [
            class_info["class_name"].ljust(40),
            str(class_info["path"]).ljust(65),
            *[
                status_symbol(class_info, method_name).ljust(10)
                for method_name in sorted(INTERESTING_METHODS)
            ],
            str(len(probable_tests)),
        ]

        print("\t".join(row))

    print()
    print("TEST INVENTORY")
    print("=" * 120)

    for test in tests:
        owner = f"{test['test_class']}." if test["test_class"] else ""
        print(f"{test['path']}:{test['line']}  {owner}{test['test_name']}")

    print()
    print("STUB METHODS")
    print("=" * 120)

    for class_info in classes:
        for method_name, method_info in sorted(class_info["methods"].items()):
            if method_info["stub"]:
                print(
                    f"{class_info['path']}:{method_info['line']}  "
                    f"{class_info['class_name']}.{method_name}"
                )


if __name__ == "__main__":
    main()

from typing import Any


def parse_diff(raw_diff: str) -> dict[str, Any]:
    files = []
    current_file = None
    changes = []

    for line in raw_diff.splitlines():
        if line.startswith("diff --git"):
            if current_file:
                files.append({"filename": current_file, "changes": changes})
            current_file = line.split(" b/")[-1]
            changes = []

        elif line.startswith("+") and not line.startswith("+++"):
            changes.append({"type": "addition", "content": line[1:]})

        elif line.startswith("-") and not line.startswith("---"):
            changes.append({"type": "deletion", "content": line[1:]})

    if current_file:
        files.append({"filename": current_file, "changes": changes})

    return {
        "files_changed": len(files),
        "files": files,
        "raw": raw_diff
    }

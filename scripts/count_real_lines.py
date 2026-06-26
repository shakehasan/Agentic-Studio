from pathlib import Path


def is_real(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def main() -> None:
    roots = [Path("src"), Path("tests"), Path("scripts")]
    total = 0
    for root in roots:
        for path in root.rglob("*.py"):
            if path.name == "generate_project.py":
                continue
            total += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if is_real(line))
    print(total)


if __name__ == "__main__":
    main()

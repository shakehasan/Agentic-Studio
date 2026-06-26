import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from marketing_swarm.memory.manager import MemoryManager


def main() -> None:
    manager = MemoryManager()
    print(manager.summarize())


if __name__ == "__main__":
    main()

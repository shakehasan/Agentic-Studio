import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from marketing_swarm.orchestration.engine import run_campaign_sync


def main() -> None:
    state = run_campaign_sync("Launch a campaign for a local-first productivity tool for remote teams.")
    print(state.package.to_markdown() if state.package else state.status)


if __name__ == "__main__":
    main()

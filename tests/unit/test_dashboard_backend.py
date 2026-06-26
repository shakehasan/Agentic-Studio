from pathlib import Path
from uuid import uuid4

from marketing_swarm.persistence.repository import SQLiteRepository
from marketing_swarm.schemas.dashboard import (
    DashboardWorkflowRecord,
    UserMemoryRecord,
    UserMemoryScope,
)


def test_dashboard_users_memory_and_workflows_are_persisted():
    base = Path("test_artifacts") / "dashboard_backend" / uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    repository = SQLiteRepository(base / "dashboard.sqlite3")

    users = repository.list_dashboard_users()
    target = users[0]

    memory = UserMemoryRecord(
        user_id=target.id,
        scope=UserMemoryScope.CHECKPOINT,
        key="run:example",
        value={"status": "awaiting_approval", "step": "qa"},
        run_id="run_example",
        created_by="user_admin",
    )
    repository.save_user_memory(memory)

    workflow = DashboardWorkflowRecord(
        run_id="run_example",
        user_id=target.id,
        requested_by="user_admin",
        brief="Create a multi-agent workflow for a campaign launch.",
        workflow_type="comprehensive_campaign",
        status="awaiting_approval",
        priority=8,
        package_id=None,
        summary="Workflow paused for reviewer approval.",
        metrics={"approval_count": 1, "agent_results": 9},
    )
    repository.save_dashboard_workflow(workflow)

    stored_memory = repository.list_user_memory(target.id, scope=UserMemoryScope.CHECKPOINT)
    stored_workflows = repository.list_dashboard_workflows(user_id=target.id)

    assert len(users) >= 3
    assert stored_memory[0].key == "run:example"
    assert stored_memory[0].value["step"] == "qa"
    assert stored_workflows[0].status == "awaiting_approval"
    assert stored_workflows[0].metrics["agent_results"] == 9


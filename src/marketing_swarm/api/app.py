"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from marketing_swarm.orchestration.engine import CampaignEngine
from marketing_swarm.schemas.brief import CampaignBrief
from marketing_swarm.schemas.dashboard import (
    DashboardCommandRequest,
    DashboardRole,
    DashboardUser,
    DashboardWorkflowRecord,
    DashboardWorkflowResult,
    UserMemoryRecord,
    UserMemoryScope,
)


class RunCreateRequest(BaseModel):
    """API request to create a campaign run."""

    brief: str
    audience: str | None = None
    goals: list[str] = []


class MemoryWriteRequest(BaseModel):
    """Request to write a dashboard user memory record."""

    scope: UserMemoryScope
    key: str
    value: dict[str, Any]
    run_id: str | None = None


def require_role(required: DashboardRole):
    """Create a FastAPI dependency that enforces dashboard roles."""

    def dependency(
        x_user_id: str = Header(default="user_admin"),
        x_user_role: DashboardRole | None = Header(default=None),
    ) -> DashboardUser:
        user = DashboardUser(
            id=x_user_id,
            name=x_user_id.replace("_", " ").title(),
            role=x_user_role or DashboardRole.ADMIN,
            title="Dashboard Operator",
            avatar_hint="OP",
        )
        if not user.can(required):
            raise HTTPException(status_code=403, detail=f"{required.value} role required")
        return user

    return dependency


def create_app() -> FastAPI:
    """Create the FastAPI app."""
    app = FastAPI(title="Agent Dashboard API", version="0.1.0")
    engine = CampaignEngine()
    engine.repository.ensure_dashboard_seed_users()

    @app.post("/runs")
    async def create_run(request: RunCreateRequest) -> dict[str, Any]:
        brief = CampaignBrief.from_text(request.brief)
        if request.audience:
            brief = brief.model_copy(update={"audience": request.audience})
        if request.goals:
            brief = brief.model_copy(update={"goals": request.goals})
        state = await engine.run(brief)
        return {"run_id": state.run_id, "status": state.status, "package_id": state.package.id if state.package else None}

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        return engine.repository.list_runs()

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> JSONResponse:
        state = engine.repository.load_state(run_id)
        if state is None:
            return JSONResponse({"error": "run not found"}, status_code=404)
        return JSONResponse(state.model_dump(mode="json"))

    @app.get("/runs/{run_id}/artifact.md")
    def get_artifact(run_id: str) -> JSONResponse:
        state = engine.repository.load_state(run_id)
        if state is None or state.package is None:
            return JSONResponse({"error": "artifact not found"}, status_code=404)
        return JSONResponse({"markdown": state.package.to_markdown()})

    @app.get("/runs/{run_id}/events")
    async def stream_events(run_id: str):
        async def event_source():
            for index in range(3):
                yield f"event: status\ndata: {json.dumps({'run_id': run_id, 'tick': index})}\n\n"
                await asyncio.sleep(0.01)

        return StreamingResponse(event_source(), media_type="text/event-stream")

    @app.websocket("/ws/runs")
    async def websocket_runs(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                payload = await websocket.receive_json()
                state = await engine.run(str(payload.get("brief", "")))
                await websocket.send_json({"run_id": state.run_id, "status": state.status.value})
        except WebSocketDisconnect:
            return

    @app.post("/approvals/{approval_id}")
    def approve(approval_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"approval_id": approval_id, "status": payload.get("status", "approve"), "accepted": True}

    @app.get("/dashboard/bootstrap")
    def dashboard_bootstrap(current: DashboardUser = Depends(require_role(DashboardRole.VIEWER))) -> dict[str, Any]:
        """Return everything the web dashboard needs for first paint."""
        users = engine.repository.list_dashboard_users()
        workflows = engine.repository.list_dashboard_workflows(limit=12)
        memory = {
            user.id: [
                record.model_dump(mode="json")
                for record in engine.repository.list_user_memory(user.id, limit=12)
            ]
            for user in users
        }
        return {
            "current_user": current.model_dump(mode="json"),
            "users": [user.model_dump(mode="json") for user in users],
            "workflows": [workflow.model_dump(mode="json") for workflow in workflows],
            "memory": memory,
            "capabilities": {
                "roles": [role.value for role in DashboardRole],
                "memory_scopes": [scope.value for scope in UserMemoryScope],
                "workflow_types": ["comprehensive_campaign", "content_sprint", "launch_plan", "qa_review"],
                "agent_count": 11,
            },
        }

    @app.get("/dashboard/users")
    def dashboard_users(current: DashboardUser = Depends(require_role(DashboardRole.VIEWER))) -> list[dict[str, Any]]:
        """List role-aware dashboard users."""
        return [user.model_dump(mode="json") for user in engine.repository.list_dashboard_users()]

    @app.get("/dashboard/users/{user_id}/memory")
    def dashboard_user_memory(
        user_id: str,
        scope: UserMemoryScope | None = None,
        current: DashboardUser = Depends(require_role(DashboardRole.VIEWER)),
    ) -> list[dict[str, Any]]:
        """Return short, long, and checkpoint memory for a user."""
        target = engine.repository.get_dashboard_user(user_id)
        if target is None:
            raise HTTPException(status_code=404, detail="dashboard user not found")
        return [
            record.model_dump(mode="json")
            for record in engine.repository.list_user_memory(user_id, scope=scope, limit=50)
        ]

    @app.post("/dashboard/users/{user_id}/memory")
    def dashboard_write_memory(
        user_id: str,
        request: MemoryWriteRequest,
        current: DashboardUser = Depends(require_role(DashboardRole.OPERATOR)),
    ) -> dict[str, Any]:
        """Write one user memory record."""
        if engine.repository.get_dashboard_user(user_id) is None:
            raise HTTPException(status_code=404, detail="dashboard user not found")
        record = UserMemoryRecord(
            user_id=user_id,
            scope=request.scope,
            key=request.key,
            value=request.value,
            run_id=request.run_id,
            created_by=current.id,
        )
        engine.repository.save_user_memory(record)
        return record.model_dump(mode="json")

    @app.post("/dashboard/agent/command")
    async def dashboard_command_agent(
        request: DashboardCommandRequest,
        current: DashboardUser = Depends(require_role(DashboardRole.OPERATOR)),
    ) -> dict[str, Any]:
        """Command the agent workforce on behalf of a selected dashboard user."""
        target = engine.repository.get_dashboard_user(request.user_id)
        if target is None:
            raise HTTPException(status_code=404, detail="dashboard user not found")

        short_record = UserMemoryRecord(
            user_id=target.id,
            scope=UserMemoryScope.SHORT,
            key="latest_command",
            value={
                "brief": request.brief,
                "workflow_type": request.workflow_type,
                "priority": request.priority,
                "channels": request.channels,
                "memory_notes": request.memory_notes,
            },
            created_by=current.id,
        )
        engine.repository.save_user_memory(short_record)
        user_memory_context = [
            record.model_dump(mode="json")
            for record in engine.repository.list_user_memory(target.id, limit=12)
        ]

        brief = CampaignBrief.from_text(request.brief).model_copy(
            update={
                "channels": request.channels,
                "metadata": {
                    "dashboard_user_id": target.id,
                    "requested_by": current.id,
                    "workflow_type": request.workflow_type,
                    "priority": request.priority,
                    "approval_required": request.approval_required,
                    "user_memory_context": user_memory_context,
                },
            }
        )
        state = await engine.run(brief)
        artifact_markdown = state.package.to_markdown() if state.package else None
        package_id = state.package.id if state.package else None
        summary = state.package.strategy_summary if state.package else f"Run paused with status {state.status.value}."
        workflow = DashboardWorkflowRecord(
            run_id=state.run_id,
            user_id=target.id,
            requested_by=current.id,
            brief=request.brief,
            workflow_type=request.workflow_type,
            status=state.status.value,
            priority=request.priority,
            package_id=package_id,
            summary=summary,
            metrics={
                "agent_results": len(state.results),
                "approval_count": len(state.approvals),
                "asset_count": len(state.package.assets) if state.package else 0,
            },
        )
        engine.repository.save_dashboard_workflow(workflow)

        checkpoint = UserMemoryRecord(
            user_id=target.id,
            scope=UserMemoryScope.CHECKPOINT,
            key=f"run:{state.run_id}",
            value={
                "run_id": state.run_id,
                "status": state.status.value,
                "route": state.plan.route.model_dump(mode="json") if state.plan else None,
                "package_id": package_id,
            },
            run_id=state.run_id,
            created_by=current.id,
        )
        long_record = UserMemoryRecord(
            user_id=target.id,
            scope=UserMemoryScope.LONG,
            key=f"campaign_summary:{state.run_id}",
            value={
                "summary": summary,
                "quality": state.package.quality_summary if state.package else {},
                "routing": state.package.routing_summary if state.package else {},
            },
            run_id=state.run_id,
            created_by=current.id,
        )
        engine.repository.save_user_memory(checkpoint)
        engine.repository.save_user_memory(long_record)

        result = DashboardWorkflowResult(
            workflow=workflow,
            memory=[short_record, checkpoint, long_record],
            artifact_markdown=artifact_markdown,
            events=[
                {"type": "route", "message": state.plan.route.reason if state.plan else "No route available"},
                {"type": "status", "message": state.status.value},
                {"type": "package", "message": f"{workflow.metrics['asset_count']} assets generated"},
            ],
            approvals=[approval.model_dump(mode="json") for approval in state.approvals],
        )
        return result.model_dump(mode="json")

    @app.get("/dashboard/workflows")
    def dashboard_workflows(
        user_id: str | None = None,
        current: DashboardUser = Depends(require_role(DashboardRole.VIEWER)),
    ) -> list[dict[str, Any]]:
        """List dashboard workflow commands."""
        return [
            workflow.model_dump(mode="json")
            for workflow in engine.repository.list_dashboard_workflows(user_id=user_id, limit=25)
        ]

    @app.get("/dashboard/workflows/{run_id}/result")
    def dashboard_workflow_result(
        run_id: str,
        current: DashboardUser = Depends(require_role(DashboardRole.VIEWER)),
    ) -> dict[str, Any]:
        """Return a completed workflow result and artifact for the web UI."""
        state = engine.repository.load_state(run_id)
        if state is None:
            raise HTTPException(status_code=404, detail="run not found")
        return {
            "run": state.model_dump(mode="json"),
            "artifact_markdown": state.package.to_markdown() if state.package else None,
            "approvals": [approval.model_dump(mode="json") for approval in state.approvals],
            "events": [
                {"type": "status", "message": state.status.value},
                {"type": "results", "message": f"{len(state.results)} agent results available"},
            ],
        }

    return app


app = create_app()

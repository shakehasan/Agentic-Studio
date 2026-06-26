"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from marketing_swarm.schemas.artifacts import CampaignPackage
from marketing_swarm.schemas.dashboard import (
    DashboardRole,
    DashboardUser,
    DashboardWorkflowRecord,
    UserMemoryRecord,
    UserMemoryScope,
)
from marketing_swarm.schemas.knowledge import KnowledgeChunk, KnowledgeSource, KnowledgeSourceKind
from marketing_swarm.schemas.state import GraphState


class SQLiteRepository:
    """SQLite repository for runs, artifacts, decisions, approvals, and evals."""

    def __init__(self, path: str | Path = "runtime/marketing_swarm.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma journal_mode=OFF")
        connection.execute("pragma synchronous=OFF")
        return connection

    def _init(self) -> None:
        """Create tables."""
        with self.connect() as connection:
            connection.executescript(
                """
                create table if not exists runs (
                    id text primary key,
                    status text not null,
                    brief text not null,
                    state_json text not null,
                    created_at text not null,
                    updated_at text not null
                );
                create table if not exists artifacts (
                    id text primary key,
                    run_id text not null,
                    name text not null,
                    kind text not null,
                    body text not null,
                    metadata_json text not null
                );
                create table if not exists events (
                    id integer primary key autoincrement,
                    run_id text not null,
                    event_type text not null,
                    payload_json text not null,
                    created_at text default current_timestamp
                );
                create table if not exists approvals (
                    id text primary key,
                    run_id text not null,
                    status text not null,
                    payload_json text not null,
                    created_at text default current_timestamp
                );
                create table if not exists knowledge_sources (
                    id text primary key,
                    namespace text not null,
                    title text not null,
                    uri text not null,
                    kind text not null,
                    text text not null,
                    metadata_json text not null,
                    created_at text not null
                );
                create table if not exists knowledge_chunks (
                    id text primary key,
                    source_id text not null,
                    namespace text not null,
                    title text not null,
                    uri text not null,
                    ordinal integer not null,
                    text text not null,
                    token_count integer not null,
                    metadata_json text not null,
                    created_at text not null,
                    foreign key(source_id) references knowledge_sources(id)
                );
                create index if not exists idx_knowledge_sources_namespace
                    on knowledge_sources(namespace);
                create index if not exists idx_knowledge_chunks_namespace
                    on knowledge_chunks(namespace);
                create table if not exists dashboard_users (
                    id text primary key,
                    name text not null,
                    role text not null,
                    title text not null,
                    team text not null,
                    status text not null,
                    avatar_hint text not null,
                    metadata_json text not null,
                    created_at text not null
                );
                create table if not exists user_memory (
                    id text primary key,
                    user_id text not null,
                    scope text not null,
                    key text not null,
                    value_json text not null,
                    run_id text,
                    created_by text,
                    created_at text not null,
                    foreign key(user_id) references dashboard_users(id)
                );
                create table if not exists dashboard_workflows (
                    id text primary key,
                    run_id text,
                    user_id text not null,
                    requested_by text not null,
                    brief text not null,
                    workflow_type text not null,
                    status text not null,
                    priority integer not null,
                    package_id text,
                    summary text not null,
                    metrics_json text not null,
                    created_at text not null,
                    foreign key(user_id) references dashboard_users(id)
                );
                create index if not exists idx_user_memory_user_scope
                    on user_memory(user_id, scope);
                create index if not exists idx_dashboard_workflows_user
                    on dashboard_workflows(user_id, created_at);
                """
            )

    def save_state(self, state: GraphState) -> None:
        """Upsert graph state."""
        payload = state.model_dump_json()
        with self.connect() as connection:
            connection.execute(
                """
                insert into runs(id, status, brief, state_json, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?)
                on conflict(id) do update set
                    status=excluded.status,
                    brief=excluded.brief,
                    state_json=excluded.state_json,
                    updated_at=excluded.updated_at
                """,
                (
                    state.run_id,
                    state.status.value,
                    state.brief.brief,
                    payload,
                    str(state.created_at),
                    str(state.updated_at),
                ),
            )

    def load_state(self, run_id: str) -> GraphState | None:
        """Load a graph state."""
        with self.connect() as connection:
            row = connection.execute("select state_json from runs where id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return GraphState.model_validate_json(row["state_json"])

    def save_package(self, package: CampaignPackage) -> None:
        """Persist package assets."""
        with self.connect() as connection:
            for asset in package.assets:
                connection.execute(
                    """
                    insert or replace into artifacts(id, run_id, name, kind, body, metadata_json)
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        package.run_id,
                        asset.name,
                        asset.kind,
                        asset.body,
                        json.dumps(asset.metadata, sort_keys=True),
                    ),
                )

    def record_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Record an auditable event."""
        with self.connect() as connection:
            connection.execute(
                "insert into events(run_id, event_type, payload_json) values (?, ?, ?)",
                (run_id, event_type, json.dumps(payload, sort_keys=True, default=str)),
            )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent runs."""
        with self.connect() as connection:
            rows = connection.execute(
                "select id, status, brief, created_at, updated_at from runs order by updated_at desc limit ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_knowledge(self, sources: list[KnowledgeSource], chunks: list[KnowledgeChunk]) -> None:
        """Persist normalized knowledge sources and chunks."""
        with self.connect() as connection:
            for source in sources:
                connection.execute(
                    """
                    insert or replace into knowledge_sources(
                        id, namespace, title, uri, kind, text, metadata_json, created_at
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source.id,
                        source.namespace,
                        source.title,
                        source.uri,
                        source.kind.value,
                        source.text,
                        json.dumps(source.metadata, sort_keys=True, default=str),
                        str(source.created_at),
                    ),
                )
            for chunk in chunks:
                connection.execute(
                    """
                    insert or replace into knowledge_chunks(
                        id, source_id, namespace, title, uri, ordinal, text, token_count, metadata_json, created_at
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        chunk.source_id,
                        chunk.namespace,
                        chunk.title,
                        chunk.uri,
                        chunk.ordinal,
                        chunk.text,
                        chunk.token_count,
                        json.dumps(chunk.metadata, sort_keys=True, default=str),
                        str(chunk.created_at),
                    ),
                )

    def list_knowledge_sources(self, *, namespace: str | None = None, limit: int = 100) -> list[KnowledgeSource]:
        """List persisted knowledge sources."""
        query = "select * from knowledge_sources"
        params: list[Any] = []
        if namespace:
            query += " where namespace = ?"
            params.append(namespace)
        query += " order by title asc limit ?"
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._source_from_row(row) for row in rows]

    def list_knowledge_chunks(self, *, namespace: str | None = None, limit: int = 1000) -> list[KnowledgeChunk]:
        """List persisted knowledge chunks."""
        query = "select * from knowledge_chunks"
        params: list[Any] = []
        if namespace:
            query += " where namespace = ?"
            params.append(namespace)
        query += " order by title asc, ordinal asc limit ?"
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._chunk_from_row(row) for row in rows]

    def _source_from_row(self, row: sqlite3.Row) -> KnowledgeSource:
        """Hydrate a source model from SQLite."""
        return KnowledgeSource(
            id=row["id"],
            namespace=row["namespace"],
            title=row["title"],
            uri=row["uri"],
            kind=KnowledgeSourceKind(row["kind"]),
            text=row["text"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
        )

    def _chunk_from_row(self, row: sqlite3.Row) -> KnowledgeChunk:
        """Hydrate a chunk model from SQLite."""
        return KnowledgeChunk(
            id=row["id"],
            source_id=row["source_id"],
            namespace=row["namespace"],
            title=row["title"],
            uri=row["uri"],
            ordinal=row["ordinal"],
            text=row["text"],
            token_count=row["token_count"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
        )

    def ensure_dashboard_seed_users(self) -> None:
        """Create demo dashboard users when the local user table is empty."""
        with self.connect() as connection:
            count = connection.execute("select count(*) from dashboard_users").fetchone()[0]
        if count:
            return
        users = [
            DashboardUser(
                id="user_admin",
                name="Avery Morgan",
                role=DashboardRole.ADMIN,
                title="Marketing Operations Lead",
                team="Growth",
                avatar_hint="AM",
                metadata={"timezone": "America/New_York", "focus": "orchestration"},
            ),
            DashboardUser(
                id="user_operator",
                name="Riley Chen",
                role=DashboardRole.OPERATOR,
                title="Campaign Strategist",
                team="Lifecycle",
                avatar_hint="RC",
                metadata={"timezone": "America/Chicago", "focus": "campaign execution"},
            ),
            DashboardUser(
                id="user_reviewer",
                name="Jordan Lee",
                role=DashboardRole.REVIEWER,
                title="Brand Reviewer",
                team="Creative",
                avatar_hint="JL",
                metadata={"timezone": "America/Los_Angeles", "focus": "quality review"},
            ),
        ]
        for user in users:
            self.save_dashboard_user(user)

    def save_dashboard_user(self, user: DashboardUser) -> None:
        """Persist a dashboard user."""
        with self.connect() as connection:
            connection.execute(
                """
                insert or replace into dashboard_users(
                    id, name, role, title, team, status, avatar_hint, metadata_json, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.name,
                    user.role.value,
                    user.title,
                    user.team,
                    user.status,
                    user.avatar_hint,
                    json.dumps(user.metadata, sort_keys=True, default=str),
                    str(user.created_at),
                ),
            )

    def list_dashboard_users(self) -> list[DashboardUser]:
        """List dashboard users."""
        self.ensure_dashboard_seed_users()
        with self.connect() as connection:
            rows = connection.execute("select * from dashboard_users order by role desc, name asc").fetchall()
        return [self._dashboard_user_from_row(row) for row in rows]

    def get_dashboard_user(self, user_id: str) -> DashboardUser | None:
        """Load one dashboard user."""
        self.ensure_dashboard_seed_users()
        with self.connect() as connection:
            row = connection.execute("select * from dashboard_users where id = ?", (user_id,)).fetchone()
        return self._dashboard_user_from_row(row) if row else None

    def save_user_memory(self, record: UserMemoryRecord) -> None:
        """Persist user-scoped short, long, or checkpoint memory."""
        with self.connect() as connection:
            connection.execute(
                """
                insert or replace into user_memory(
                    id, user_id, scope, key, value_json, run_id, created_by, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.user_id,
                    record.scope.value,
                    record.key,
                    json.dumps(record.value, sort_keys=True, default=str),
                    record.run_id,
                    record.created_by,
                    str(record.created_at),
                ),
            )

    def list_user_memory(
        self,
        user_id: str,
        *,
        scope: UserMemoryScope | None = None,
        limit: int = 50,
    ) -> list[UserMemoryRecord]:
        """List user memory records."""
        params: list[Any] = [user_id]
        query = "select * from user_memory where user_id = ?"
        if scope:
            query += " and scope = ?"
            params.append(scope.value)
        query += " order by created_at desc limit ?"
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._user_memory_from_row(row) for row in rows]

    def save_dashboard_workflow(self, workflow: DashboardWorkflowRecord) -> None:
        """Persist a dashboard workflow command record."""
        with self.connect() as connection:
            connection.execute(
                """
                insert or replace into dashboard_workflows(
                    id, run_id, user_id, requested_by, brief, workflow_type, status, priority,
                    package_id, summary, metrics_json, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow.id,
                    workflow.run_id,
                    workflow.user_id,
                    workflow.requested_by,
                    workflow.brief,
                    workflow.workflow_type,
                    workflow.status,
                    workflow.priority,
                    workflow.package_id,
                    workflow.summary,
                    json.dumps(workflow.metrics, sort_keys=True, default=str),
                    str(workflow.created_at),
                ),
            )

    def list_dashboard_workflows(self, *, user_id: str | None = None, limit: int = 25) -> list[DashboardWorkflowRecord]:
        """List recent dashboard workflow command records."""
        query = "select * from dashboard_workflows"
        params: list[Any] = []
        if user_id:
            query += " where user_id = ?"
            params.append(user_id)
        query += " order by created_at desc limit ?"
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._workflow_from_row(row) for row in rows]

    def _dashboard_user_from_row(self, row: sqlite3.Row) -> DashboardUser:
        """Hydrate a dashboard user from SQLite."""
        return DashboardUser(
            id=row["id"],
            name=row["name"],
            role=DashboardRole(row["role"]),
            title=row["title"],
            team=row["team"],
            status=row["status"],
            avatar_hint=row["avatar_hint"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
        )

    def _user_memory_from_row(self, row: sqlite3.Row) -> UserMemoryRecord:
        """Hydrate user memory from SQLite."""
        return UserMemoryRecord(
            id=row["id"],
            user_id=row["user_id"],
            scope=UserMemoryScope(row["scope"]),
            key=row["key"],
            value=json.loads(row["value_json"]),
            run_id=row["run_id"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )

    def _workflow_from_row(self, row: sqlite3.Row) -> DashboardWorkflowRecord:
        """Hydrate a workflow record from SQLite."""
        return DashboardWorkflowRecord(
            id=row["id"],
            run_id=row["run_id"],
            user_id=row["user_id"],
            requested_by=row["requested_by"],
            brief=row["brief"],
            workflow_type=row["workflow_type"],
            status=row["status"],
            priority=row["priority"],
            package_id=row["package_id"],
            summary=row["summary"],
            metrics=json.loads(row["metrics_json"]),
            created_at=row["created_at"],
        )

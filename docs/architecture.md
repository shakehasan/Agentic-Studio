# Agentic Marketing Swarm Architecture

Updated: June 2026.

Agentic Marketing Swarm is a local-first campaign orchestration project with a FastAPI backend, a Next.js dashboard, a checkpointed agent engine, local retrieval, local memory, guardrails, observability, and deterministic evals. It is intentionally free to run by default: no required API keys, business account, hosted auth, paid vector database, managed queue, or cloud database.

## System Plane

```mermaid
flowchart TB
    classDef iface fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#e0e7ff
    classDef orch  fill:#2e1065,stroke:#8b5cf6,stroke-width:2px,color:#ede9fe
    classDef agent fill:#172554,stroke:#3b82f6,stroke-width:2px,color:#dbeafe
    classDef tool  fill:#042f2e,stroke:#14b8a6,stroke-width:2px,color:#ccfbf1
    classDef rag   fill:#052e16,stroke:#22c55e,stroke-width:2px,color:#dcfce7
    classDef mem   fill:#4c0519,stroke:#f43f5e,stroke-width:2px,color:#ffe4e6
    classDef gate  fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fee2e2
    classDef obs   fill:#083344,stroke:#06b6d4,stroke-width:2px,color:#cffafe
    classDef store fill:#0f172a,stroke:#64748b,stroke-width:2px,color:#e2e8f0

    UI["Next.js dashboard<br/>React + TypeScript"]:::iface
    API["FastAPI REST<br/>runs + dashboard endpoints"]:::iface
    RBAC["Role gate<br/>admin operator reviewer viewer"]:::gate
    ENGINE["CampaignEngine"]:::orch
    ROUTER["MultiRouteRouter"]:::orch
    AGENTS["Supervisor + 10 specialists"]:::agent
    TOOLS["ToolRegistry"]:::tool
    RAG["AgenticRAGPipeline"]:::rag
    MEM["MemoryManager<br/>engine memory"]:::mem
    USERMEM[("user_memory<br/>short long checkpoint")]:::store
    WORKFLOWS[("dashboard_workflows")]:::store
    OBS["TraceRecorder + MetricsRegistry"]:::obs
    STORE[("SQLiteRepository")]:::store

    UI --> API
    API --> RBAC
    RBAC --> ENGINE
    ENGINE --> ROUTER
    ENGINE --> AGENTS
    AGENTS --> TOOLS
    AGENTS --> RAG
    ENGINE --> MEM
    RBAC --> USERMEM
    RBAC --> WORKFLOWS
    ENGINE --> OBS
    ENGINE --> STORE
    MEM --> STORE
    USERMEM --> STORE
    WORKFLOWS --> STORE
```

**System Plane.** The dashboard is the human command surface. FastAPI receives commands, applies lightweight role checks, writes dashboard memory, and forwards normalized briefs to `CampaignEngine`. The engine owns routing, checkpointing, policy decisions, specialist execution, retrieval, package synthesis, and event persistence.

## Dashboard Command Sequence

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant UI as Next.js Dashboard
    participant API as FastAPI
    participant DB as SQLiteRepository
    participant ENG as CampaignEngine
    participant AG as Specialist Agents

    U->>UI: choose target user and submit command
    UI->>API: POST /dashboard/agent/command
    API->>API: require operator or admin role
    API->>DB: write short user memory
    API->>DB: load recent user memory
    API->>ENG: run CampaignBrief with user_memory_context metadata
    ENG->>AG: route and execute specialist tasks
    ENG->>DB: persist run state, events, and package
    API->>DB: write checkpoint and long user memory
    API-->>UI: workflow, artifact, approvals, events, memory
```

**Dashboard Command Sequence.** A dashboard command always starts with short memory, so the immediate user intent is recorded before the agent workflow runs. After completion or pause, checkpoint memory links the user to the run boundary, and long memory stores reusable summary context.

## Design Contracts

| Contract | Enforced By | Effect |
|---|---|---|
| Typed briefs, tasks, routes, handoffs, results, users, memory records, and packages | Pydantic schemas in `src/marketing_swarm/schemas/` | Invalid state fails before it contaminates a run |
| Role-aware command surface | `require_role()` dependency and dashboard headers | Viewers/reviewers inspect; operators/admins command and write memory |
| User memory remains local | `user_memory` SQLite table | Multi-user continuity without hosted profile storage |
| Retrieval stays local by default | Hashing vectors, BM25, SQLite knowledge chunks | Campaign generation can run without paid search or external storage |
| Tool failures are structured | `ToolResult` and `FailureStamp` | Orchestration can distinguish tool, policy, model, validation, and infrastructure errors |
| QA cycles are bounded | `QualityPolicy` and `qa_revision_limit` | Revision loops cannot run forever |
| Evals use deterministic provider | `FakeProvider` and `EvalHarness` | CI gates remain reproducible without a live model runtime |

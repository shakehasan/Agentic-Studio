# Multi-User Agent Dashboard

The dashboard in `apps/dashboard` is a Next.js App Router interface for commanding the FastAPI backend. It gives multiple users a shared command center with role-aware controls, user memory, workflow history, agent status, approval checkpoints, and generated results.

## Capabilities

- Role-based access: admins and operators can command agents; reviewers and viewers can inspect workflow results and memory.
- User memory: short-term command notes, durable long-term preferences, and checkpoint memory created by workflow runs.
- Agent command flow: brief, workflow type, priority, channels, and approval requirement are posted to the FastAPI backend and executed through the LangGraph workflow.
- Result retrieval: the UI displays the artifact markdown, workflow timeline, approvals, and updated memory after each run.
- Demo fallback: the Next.js route handlers return seeded demo data if the FastAPI service is not reachable.
- Free local stack: local FastAPI, local SQLite, local Next.js, no required paid auth, storage, queue, or hosted model provider.

## Roles

| Role | Can Read | Can Command Agents | Can Write User Memory |
|---|---|---:|---:|
| `admin` | Yes | Yes | Yes |
| `operator` | Yes | Yes | Yes |
| `reviewer` | Yes | No | No |
| `viewer` | Yes | No | No |

The current demo role is passed through `x-user-id` and `x-user-role` headers. This is intentionally lightweight for a local prototype and can be swapped for a real auth adapter later.

## User Memory

The dashboard exposes three user-scoped memory types:

| Scope | Description |
|---|---|
| `short` | The latest command context: brief, workflow type, priority, channels, and operator memory notes. |
| `long` | Durable summaries from generated workflows, including quality and routing summaries. |
| `checkpoint` | Compact LangGraph run boundary data: run id, status, route decision, and package id. |

When `POST /dashboard/agent/command` runs, the API saves `short` memory first, loads recent memory into the campaign brief metadata, executes the LangGraph-backed agent workflow, then saves `checkpoint` and `long` memory from the result. The dashboard receives those records in the response and merges them into the selected user's memory panel.

## Local Run

Start the FastAPI backend:

```bash
uvicorn marketing_swarm.api.app:create_app --factory --reload --port 8080
```

Install and run the dashboard:

```bash
cd apps/dashboard
npm install
npm run dev
```

Open `http://localhost:3000`. To point the dashboard at a different API server, set `AGENT_DASHBOARD_API_BASE_URL` before starting Next.js.

Smoke-test the dashboard with a headless local browser:

```bash
npm run smoke:dashboard
```

## API Surface

- `GET /dashboard/bootstrap`
- `GET /dashboard/users`
- `GET /dashboard/users/{user_id}/memory`
- `POST /dashboard/users/{user_id}/memory`
- `POST /dashboard/agent/command`
- `GET /dashboard/workflows`
- `GET /dashboard/workflows/{run_id}/result`

# Memory

The project has two memory planes: engine memory for agent execution and dashboard user memory for multi-user continuity.

## Engine Memory

`MemoryManager` coordinates the runtime memory used by `CampaignEngine`, its compiled LangGraph workflow, and specialist agents.

| Tier | Lifespan | Purpose |
|---|---|---|
| Working | Current run | Active facts and transient context for the LangGraph workflow in progress. |
| Semantic | Durable knowledge | Reusable campaign, audience, market, and positioning knowledge. |
| Episodic | Run history | Past decisions, outcomes, failures, and lessons. |
| Procedural | Playbooks | Reusable methods and execution recipes. |

## Dashboard User Memory

Dashboard user memory is stored in SQLite in the `user_memory` table. It is attached to a specific dashboard user and exposed in the web UI.

| Scope | Meaning |
|---|---|
| `short` | Immediate command context: latest brief, channels, workflow type, priority, and operator notes. |
| `long` | Durable result context: campaign summaries, quality summaries, and routing summaries that should carry across sessions. |
| `checkpoint` | Audit and recovery context: run id, status, route decision, package id, and the graph boundary reached. |

When a user commands an agent workflow, the API writes `short` memory first, loads recent user memory into `CampaignBrief.metadata.user_memory_context`, runs the LangGraph-backed engine, then writes `checkpoint` and `long` memory from the result. Checkpoint memory is intentionally compact: it lets the dashboard show whether the graph completed, failed, or paused for approval without reopening the full run state. Reviewers and viewers can inspect memory; operators and admins can write memory and command agents.

Everything is local by default. Memory uses SQLite and Python data structures, not a paid vector database, hosted profile service, or business account.

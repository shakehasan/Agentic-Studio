"use client";

import { useEffect, useMemo, useState } from "react";
import { AgentGrid } from "@/components/agent-grid";
import { CommandCenter } from "@/components/command-center";
import { MemoryPanel } from "@/components/memory-panel";
import { ResultsPanel } from "@/components/results-panel";
import { RoleBadge } from "@/components/role-badge";
import { StatStrip } from "@/components/stat-strip";
import { UserRail } from "@/components/user-rail";
import { WorkflowTimeline } from "@/components/workflow-timeline";
import { baseAgents, createDemoEvents, demoBootstrap } from "@/lib/demo-data";
import type {
  AgentStatus,
  DashboardBootstrap,
  DashboardCommandPayload,
  DashboardWorkflowResult,
  DashboardWorkflowRecord,
  WorkflowEvent,
} from "@/types/dashboard";

export function DashboardShell() {
  const [bootstrap, setBootstrap] = useState<DashboardBootstrap>(demoBootstrap);
  const [selectedUserId, setSelectedUserId] = useState(demoBootstrap.users[1]?.id ?? demoBootstrap.users[0]?.id ?? "");
  const [workflows, setWorkflows] = useState<DashboardWorkflowRecord[]>(demoBootstrap.workflows);
  const [events, setEvents] = useState<WorkflowEvent[]>(createDemoEvents({
    user_id: selectedUserId,
    brief: "Demo workflow initialized.",
    workflow_type: "comprehensive_campaign",
    priority: 7,
    channels: ["content", "email", "search"],
    approval_required: true,
  }));
  const [result, setResult] = useState<DashboardWorkflowResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function loadBootstrap() {
      try {
        const response = await fetch("/api/dashboard/bootstrap", {
          headers: {
            "x-user-id": demoBootstrap.current_user.id,
            "x-user-role": demoBootstrap.current_user.role,
          },
        });
        if (!response.ok) {
          return;
        }
        const data = (await response.json()) as DashboardBootstrap;
        if (!ignore) {
          setBootstrap(data);
          setWorkflows(data.workflows);
          setSelectedUserId((currentUserId) => data.users[1]?.id ?? data.users[0]?.id ?? currentUserId);
        }
      } catch {
        if (!ignore) {
          setError("Using demo mode until the FastAPI backend is reachable.");
        }
      }
    }
    loadBootstrap();
    return () => {
      ignore = true;
    };
  }, []);

  const selectedUser = useMemo(
    () => bootstrap.users.find((user) => user.id === selectedUserId) ?? bootstrap.users[0] ?? demoBootstrap.users[0],
    [bootstrap.users, selectedUserId],
  );

  const selectedMemory = bootstrap.memory[selectedUser.id] ?? [];

  const agents: AgentStatus[] = useMemo(() => {
    if (!isRunning) {
      return baseAgents;
    }
    return baseAgents.map((agent, index) => ({
      ...agent,
      state: index < 4 ? "complete" : index < 8 ? "running" : "queued",
      progress: index < 4 ? 100 : index < 8 ? 58 : 18,
    }));
  }, [isRunning]);

  async function runWorkflow(payload: DashboardCommandPayload) {
    setIsRunning(true);
    setError(null);
    setEvents([{ type: "command", message: "Command sent to the agent workforce." }]);
    try {
      const response = await fetch("/api/dashboard/command", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-user-id": bootstrap.current_user.id,
          "x-user-role": bootstrap.current_user.role,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("Agent command failed");
      }
      const data = (await response.json()) as DashboardWorkflowResult;
      setResult(data);
      setWorkflows((current) => [data.workflow, ...current.filter((workflow) => workflow.id !== data.workflow.id)]);
      setEvents(data.events.length ? data.events : createDemoEvents(payload));
      setBootstrap((current) => ({
        ...current,
        memory: {
          ...current.memory,
          [payload.user_id]: [...data.memory, ...(current.memory[payload.user_id] ?? [])],
        },
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown dashboard error");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="dashboard">
      <div className="shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">AG</div>
            <div>
              <p className="eyebrow">Agent dashboard</p>
              <h1>Command center for multi-user agent workflows</h1>
            </div>
          </div>
          <div className="top-actions">
            <span className="status-pill">FastAPI connected or demo fallback</span>
            <RoleBadge role={bootstrap.current_user.role} />
          </div>
        </header>

        <div className="sidebar">
          <UserRail users={bootstrap.users} selectedUserId={selectedUser.id} onSelectUser={setSelectedUserId} />
          <section className="panel">
            <div className="panel-body">
              <p className="eyebrow">Role System</p>
              <h2>{bootstrap.current_user.name}</h2>
              <p className="muted">
                Admins and operators can command agents. Reviewers can inspect approvals and artifacts. Viewers can read
                results and memory only.
              </p>
              {error ? <p className="error">{error}</p> : null}
            </div>
          </section>
        </div>

        <div className="main-grid">
          <div className="stack">
            <StatStrip bootstrap={bootstrap} workflows={workflows} />
            <CommandCenter
              currentUser={bootstrap.current_user}
              isRunning={isRunning}
              targetUser={selectedUser}
              workflowTypes={bootstrap.capabilities.workflow_types}
              onRun={runWorkflow}
            />
            <AgentGrid agents={agents} />
            <MemoryPanel memory={selectedMemory} />
          </div>
          <div className="stack">
            <WorkflowTimeline events={events} workflows={workflows} />
            <ResultsPanel result={result} />
          </div>
        </div>
      </div>
    </main>
  );
}

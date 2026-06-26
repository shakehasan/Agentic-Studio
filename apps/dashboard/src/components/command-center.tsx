"use client";

import { useState } from "react";
import type { DashboardCommandPayload, DashboardRole, DashboardUser } from "@/types/dashboard";

const roleRank: Record<DashboardRole, number> = {
  viewer: 10,
  reviewer: 20,
  operator: 30,
  admin: 40,
};

interface CommandCenterProps {
  currentUser: DashboardUser;
  targetUser: DashboardUser;
  workflowTypes: string[];
  isRunning: boolean;
  onRun: (payload: DashboardCommandPayload) => Promise<void>;
}

export function CommandCenter({
  currentUser,
  targetUser,
  workflowTypes,
  isRunning,
  onRun,
}: CommandCenterProps) {
  const [brief, setBrief] = useState(
    "Launch a comprehensive campaign for a privacy-first workspace aimed at distributed marketing teams.",
  );
  const [workflowType, setWorkflowType] = useState(workflowTypes[0] ?? "comprehensive_campaign");
  const [priority, setPriority] = useState(7);
  const [channels, setChannels] = useState("content,email,search,social");
  const [approvalRequired, setApprovalRequired] = useState(true);
  const [memoryNotes, setMemoryNotes] = useState("Remember this user's preference for proof-led copy and QA checkpoints.");

  const canCommand = roleRank[currentUser.role] >= roleRank.operator;

  async function submitCommand() {
    await onRun({
      user_id: targetUser.id,
      brief,
      workflow_type: workflowType,
      priority,
      channels: channels
        .split(",")
        .map((channel) => channel.trim())
        .filter(Boolean),
      approval_required: approvalRequired,
      memory_notes: memoryNotes,
    });
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Agent Command</p>
          <h2>Comprehensive Workflow</h2>
        </div>
        <span className="status-pill">Target: {targetUser.name}</span>
      </div>
      <div className="panel-body form-grid">
        <div className="field">
          <label htmlFor="brief">Campaign or workflow brief</label>
          <textarea id="brief" value={brief} onChange={(event) => setBrief(event.target.value)} />
        </div>
        <div className="field-grid">
          <div className="field">
            <label htmlFor="workflow">Workflow</label>
            <select id="workflow" value={workflowType} onChange={(event) => setWorkflowType(event.target.value)}>
              {workflowTypes.map((workflow) => (
                <option key={workflow} value={workflow}>
                  {workflow.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="priority">Priority</label>
            <input
              id="priority"
              max={10}
              min={1}
              type="number"
              value={priority}
              onChange={(event) => setPriority(Number(event.target.value))}
            />
          </div>
          <div className="field">
            <label htmlFor="channels">Channels</label>
            <input id="channels" value={channels} onChange={(event) => setChannels(event.target.value)} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="memory">User memory note</label>
          <input id="memory" value={memoryNotes} onChange={(event) => setMemoryNotes(event.target.value)} />
        </div>
        <div className="button-row">
          <label>
            <input
              checked={approvalRequired}
              type="checkbox"
              onChange={(event) => setApprovalRequired(event.target.checked)}
            />{" "}
            Require approval checkpoint
          </label>
          <div className="button-group">
            <button className="btn ghost" type="button" onClick={() => setBrief("")}>
              Clear
            </button>
            <button className="btn primary" disabled={!canCommand || isRunning || brief.length < 8} onClick={submitCommand} type="button">
              {isRunning ? "Running workflow..." : "Run agent workflow"}
            </button>
          </div>
        </div>
        {!canCommand ? <p className="error">Current role can inspect results but cannot command agents.</p> : null}
      </div>
    </section>
  );
}


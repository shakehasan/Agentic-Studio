export type DashboardRole = "admin" | "operator" | "reviewer" | "viewer";

export type MemoryScope = "short" | "long" | "checkpoint";

export interface DashboardUser {
  id: string;
  name: string;
  role: DashboardRole;
  title: string;
  team: string;
  status: string;
  avatar_hint: string;
  metadata: Record<string, unknown>;
}

export interface UserMemoryRecord {
  id: string;
  user_id: string;
  scope: MemoryScope;
  key: string;
  value: Record<string, unknown>;
  run_id?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface DashboardWorkflowRecord {
  id: string;
  run_id?: string | null;
  user_id: string;
  requested_by: string;
  brief: string;
  workflow_type: string;
  status: string;
  priority: number;
  package_id?: string | null;
  summary: string;
  metrics: Record<string, unknown>;
  created_at: string;
}

export interface DashboardBootstrap {
  current_user: DashboardUser;
  users: DashboardUser[];
  workflows: DashboardWorkflowRecord[];
  memory: Record<string, UserMemoryRecord[]>;
  capabilities: {
    roles: DashboardRole[];
    memory_scopes: MemoryScope[];
    workflow_types: string[];
    agent_count: number;
  };
}

export interface DashboardCommandPayload {
  user_id: string;
  brief: string;
  workflow_type: string;
  priority: number;
  channels: string[];
  approval_required: boolean;
  memory_notes?: string;
}

export interface DashboardWorkflowResult {
  workflow: DashboardWorkflowRecord;
  memory: UserMemoryRecord[];
  artifact_markdown?: string | null;
  events: WorkflowEvent[];
  approvals: Array<Record<string, unknown>>;
}

export interface WorkflowEvent {
  type: string;
  message: string;
}

export interface AgentStatus {
  id: string;
  label: string;
  phase: string;
  state: "idle" | "queued" | "running" | "complete" | "review";
  progress: number;
}


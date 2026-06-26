import type {
  AgentStatus,
  DashboardBootstrap,
  DashboardCommandPayload,
  DashboardWorkflowResult,
  UserMemoryRecord,
  WorkflowEvent,
} from "@/types/dashboard";

const now = new Date().toISOString();

export const demoBootstrap: DashboardBootstrap = {
  current_user: {
    id: "user_admin",
    name: "Avery Morgan",
    role: "admin",
    title: "Marketing Operations Lead",
    team: "Growth",
    status: "active",
    avatar_hint: "AM",
    metadata: { focus: "orchestration" },
  },
  users: [
    {
      id: "user_admin",
      name: "Avery Morgan",
      role: "admin",
      title: "Marketing Operations Lead",
      team: "Growth",
      status: "active",
      avatar_hint: "AM",
      metadata: { focus: "orchestration" },
    },
    {
      id: "user_operator",
      name: "Riley Chen",
      role: "operator",
      title: "Campaign Strategist",
      team: "Lifecycle",
      status: "active",
      avatar_hint: "RC",
      metadata: { focus: "campaign execution" },
    },
    {
      id: "user_reviewer",
      name: "Jordan Lee",
      role: "reviewer",
      title: "Brand Reviewer",
      team: "Creative",
      status: "active",
      avatar_hint: "JL",
      metadata: { focus: "quality review" },
    },
  ],
  workflows: [
    {
      id: "workflow_demo",
      run_id: "run_demo",
      user_id: "user_operator",
      requested_by: "user_admin",
      brief: "Launch a local-first campaign for privacy-aware remote teams.",
      workflow_type: "comprehensive_campaign",
      status: "completed",
      priority: 7,
      package_id: "package_demo",
      summary: "Demo campaign package is ready for review.",
      metrics: { asset_count: 40, agent_results: 10, approval_count: 0 },
      created_at: now,
    },
  ],
  memory: {
    user_admin: [],
    user_operator: [
      {
        id: "umem_short_demo",
        user_id: "user_operator",
        scope: "short",
        key: "latest_command",
        value: { brief: "Launch campaign", channel: "content, email, search" },
        created_by: "user_admin",
        created_at: now,
      },
      {
        id: "umem_long_demo",
        user_id: "user_operator",
        scope: "long",
        key: "campaign_summary:run_demo",
        value: { summary: "Privacy-first narrative with proof-led activation." },
        run_id: "run_demo",
        created_by: "user_admin",
        created_at: now,
      },
      {
        id: "umem_checkpoint_demo",
        user_id: "user_operator",
        scope: "checkpoint",
        key: "run:run_demo",
        value: { status: "completed", route: "parallel_fanout" },
        run_id: "run_demo",
        created_by: "user_admin",
        created_at: now,
      },
    ],
    user_reviewer: [],
  },
  capabilities: {
    roles: ["admin", "operator", "reviewer", "viewer"],
    memory_scopes: ["short", "long", "checkpoint"],
    workflow_types: ["comprehensive_campaign", "content_sprint", "launch_plan", "qa_review"],
    agent_count: 11,
  },
};

export const baseAgents: AgentStatus[] = [
  { id: "supervisor", label: "Supervisor", phase: "Plan", state: "complete", progress: 100 },
  { id: "research", label: "Research", phase: "Discovery", state: "complete", progress: 100 },
  { id: "competitive", label: "Competitive Intel", phase: "Discovery", state: "complete", progress: 100 },
  { id: "content", label: "Content Strategy", phase: "Strategy", state: "complete", progress: 100 },
  { id: "copy", label: "Copywriter", phase: "Production", state: "complete", progress: 100 },
  { id: "seo", label: "SEO / GEO", phase: "Production", state: "complete", progress: 100 },
  { id: "social", label: "Social", phase: "Production", state: "complete", progress: 100 },
  { id: "email", label: "Email", phase: "Production", state: "complete", progress: 100 },
  { id: "creative", label: "Creative Brief", phase: "Production", state: "complete", progress: 100 },
  { id: "qa", label: "Brand Voice / QA", phase: "Review", state: "review", progress: 82 },
  { id: "analytics", label: "Analytics", phase: "Optimize", state: "complete", progress: 100 },
];

export function createDemoWorkflowResult(payload: DashboardCommandPayload): DashboardWorkflowResult {
  const runId = `run_demo_${Date.now()}`;
  const memory: UserMemoryRecord[] = [
    {
      id: `umem_short_${Date.now()}`,
      user_id: payload.user_id,
      scope: "short",
      key: "latest_command",
      value: { brief: payload.brief, workflow_type: payload.workflow_type, channels: payload.channels },
      created_by: "user_admin",
      created_at: new Date().toISOString(),
    },
    {
      id: `umem_checkpoint_${Date.now()}`,
      user_id: payload.user_id,
      scope: "checkpoint",
      key: `run:${runId}`,
      value: { run_id: runId, status: "completed", route: "parallel_fanout" },
      run_id: runId,
      created_by: "user_admin",
      created_at: new Date().toISOString(),
    },
  ];
  return {
    workflow: {
      id: `workflow_${Date.now()}`,
      run_id: runId,
      user_id: payload.user_id,
      requested_by: "user_admin",
      brief: payload.brief,
      workflow_type: payload.workflow_type,
      status: "completed",
      priority: payload.priority,
      package_id: `package_${Date.now()}`,
      summary: "Demo workflow completed locally. Connect the FastAPI backend for persisted campaign packages.",
      metrics: { asset_count: 40, agent_results: 10, approval_count: payload.approval_required ? 1 : 0 },
      created_at: new Date().toISOString(),
    },
    memory,
    artifact_markdown: `# Campaign Package\n\n## Brief\n\n${payload.brief}\n\n## Generated Plan\n\n- Discovery: research and competitive intelligence.\n- Strategy: content pillars, messaging hierarchy, and channel mix.\n- Production: copy, SEO/GEO, social, email, and creative briefs.\n- Review: brand voice QA and approval checkpoint.\n- Optimization: KPI framework and experiment backlog.\n`,
    events: createDemoEvents(payload),
    approvals: payload.approval_required ? [{ id: "approval_demo", status: "awaiting_review" }] : [],
  };
}

export function createDemoEvents(payload: DashboardCommandPayload): WorkflowEvent[] {
  return [
    { type: "route", message: `${payload.workflow_type} routed to the 11-agent workforce.` },
    { type: "memory", message: "Short-term user memory captured for the command context." },
    { type: "agents", message: "Specialists completed research, strategy, production, QA, and analytics passes." },
    { type: "package", message: "Campaign package is available in the result pane." },
  ];
}


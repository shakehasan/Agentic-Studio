import type { DashboardBootstrap, DashboardWorkflowRecord } from "@/types/dashboard";

interface StatStripProps {
  bootstrap: DashboardBootstrap;
  workflows: DashboardWorkflowRecord[];
}

export function StatStrip({ bootstrap, workflows }: StatStripProps) {
  const activeRuns = workflows.filter((workflow) => workflow.status !== "completed").length;
  const completed = workflows.filter((workflow) => workflow.status === "completed").length;
  const memories = Object.values(bootstrap.memory).flat().length;

  return (
    <section className="metric-grid" aria-label="Dashboard metrics">
      <div className="metric">
        <span className="metric-value">{bootstrap.users.length}</span>
        <span className="metric-label">role-based users</span>
      </div>
      <div className="metric">
        <span className="metric-value">{bootstrap.capabilities.agent_count}</span>
        <span className="metric-label">agents connected</span>
      </div>
      <div className="metric">
        <span className="metric-value">{activeRuns}</span>
        <span className="metric-label">active workflows</span>
      </div>
      <div className="metric">
        <span className="metric-value">{completed}/{memories}</span>
        <span className="metric-label">completed runs / memory records</span>
      </div>
    </section>
  );
}


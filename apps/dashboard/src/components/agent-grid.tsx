import type { AgentStatus } from "@/types/dashboard";

interface AgentGridProps {
  agents: AgentStatus[];
}

export function AgentGrid({ agents }: AgentGridProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Agent Mesh</p>
          <h2>Workforce Status</h2>
        </div>
      </div>
      <div className="panel-body agent-grid">
        {agents.map((agent) => (
          <article className="agent-row" key={agent.id}>
            <div className="agent-top">
              <strong>{agent.label}</strong>
              <span className="status-pill">{agent.state}</span>
            </div>
            <p className="muted">{agent.phase}</p>
            <div className="progress" aria-label={`${agent.label} progress`}>
              <span style={{ width: `${agent.progress}%` }} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}


import type { DashboardWorkflowRecord, WorkflowEvent } from "@/types/dashboard";

interface WorkflowTimelineProps {
  workflows: DashboardWorkflowRecord[];
  events: WorkflowEvent[];
}

export function WorkflowTimeline({ workflows, events }: WorkflowTimelineProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Workflow</p>
          <h2>Timeline</h2>
        </div>
      </div>
      <div className="panel-body timeline">
        {events.map((event) => (
          <div className="timeline-item" key={`${event.type}-${event.message}`}>
            <span className="timeline-dot" />
            <div>
              <strong>{event.type}</strong>
              <p className="muted">{event.message}</p>
            </div>
          </div>
        ))}
        {workflows.slice(0, 4).map((workflow) => (
          <div className="timeline-item" key={workflow.id}>
            <span className="timeline-dot" />
            <div>
              <strong>{workflow.status}</strong>
              <p className="muted">{workflow.brief}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}


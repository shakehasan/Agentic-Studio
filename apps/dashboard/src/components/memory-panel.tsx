import type { MemoryScope, UserMemoryRecord } from "@/types/dashboard";

const scopes: MemoryScope[] = ["short", "long", "checkpoint"];

interface MemoryPanelProps {
  memory: UserMemoryRecord[];
}

export function MemoryPanel({ memory }: MemoryPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">User Memory</p>
          <h2>Short, Long, Checkpoint</h2>
        </div>
      </div>
      <div className="panel-body memory-grid">
        {scopes.map((scope) => {
          const records = memory.filter((record) => record.scope === scope);
          return (
            <article className="memory-column" key={scope}>
              <header>
                <strong>{scope}</strong>
                <span className="scope-badge">{records.length}</span>
              </header>
              <div className="memory-list">
                {records.length ? (
                  records.map((record) => (
                    <div className="memory-item" key={record.id}>
                      <strong>{record.key}</strong>
                      <p className="muted">{JSON.stringify(record.value).slice(0, 120)}</p>
                    </div>
                  ))
                ) : (
                  <p className="muted">No {scope} memory yet.</p>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}


"use client";

import { useState } from "react";
import type { DashboardWorkflowResult } from "@/types/dashboard";

interface ResultsPanelProps {
  result: DashboardWorkflowResult | null;
}

type ResultTab = "artifact" | "workflow" | "approvals";

export function ResultsPanel({ result }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<ResultTab>("artifact");
  const tabs: ResultTab[] = ["artifact", "workflow", "approvals"];

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Result Retrieval</p>
          <h2>Agent Output</h2>
        </div>
      </div>
      <div className="panel-body">
        <div className="result-tabs" role="tablist" aria-label="Result tabs">
          {tabs.map((tab) => (
            <button
              className={`tab ${activeTab === tab ? "active" : ""}`}
              key={tab}
              onClick={() => setActiveTab(tab)}
              role="tab"
              type="button"
            >
              {tab}
            </button>
          ))}
        </div>
        {!result ? (
          <div className="empty-state">Run a workflow to retrieve the generated campaign package here.</div>
        ) : activeTab === "artifact" ? (
          <pre className="artifact">{result.artifact_markdown ?? "No artifact is available yet."}</pre>
        ) : activeTab === "workflow" ? (
          <pre className="artifact">{JSON.stringify(result.workflow, null, 2)}</pre>
        ) : (
          <pre className="artifact">{JSON.stringify(result.approvals, null, 2)}</pre>
        )}
      </div>
    </section>
  );
}


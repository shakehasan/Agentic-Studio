import { demoBootstrap, createDemoWorkflowResult } from "@/lib/demo-data";
import type { DashboardBootstrap, DashboardCommandPayload, DashboardWorkflowResult } from "@/types/dashboard";

const API_BASE = process.env.AGENT_DASHBOARD_API_BASE_URL ?? "http://127.0.0.1:8080";

export async function fetchBackendJson<T>(
  path: string,
  init: RequestInit = {},
  fallback: T,
): Promise<T> {
  try {
    const headers = new Headers(init.headers);
    if (!headers.has("content-type")) {
      headers.set("content-type", "application/json");
    }
    if (!headers.has("x-user-id")) {
      headers.set("x-user-id", "user_admin");
    }
    if (!headers.has("x-user-role")) {
      headers.set("x-user-role", "admin");
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function getBootstrap(headers: Headers): Promise<DashboardBootstrap> {
  return fetchBackendJson<DashboardBootstrap>(
    "/dashboard/bootstrap",
    {
      headers: {
        "x-user-id": headers.get("x-user-id") ?? "user_admin",
        "x-user-role": headers.get("x-user-role") ?? "admin",
      },
    },
    demoBootstrap,
  );
}

export async function commandAgent(
  payload: DashboardCommandPayload,
  headers: Headers,
): Promise<DashboardWorkflowResult> {
  return fetchBackendJson<DashboardWorkflowResult>(
    "/dashboard/agent/command",
    {
      method: "POST",
      headers: {
        "x-user-id": headers.get("x-user-id") ?? "user_admin",
        "x-user-role": headers.get("x-user-role") ?? "admin",
      },
      body: JSON.stringify(payload),
    },
    createDemoWorkflowResult(payload),
  );
}

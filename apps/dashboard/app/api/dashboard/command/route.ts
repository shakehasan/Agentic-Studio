import { commandAgent } from "@/lib/backend";
import type { DashboardCommandPayload } from "@/types/dashboard";

export async function POST(request: Request) {
  const payload = (await request.json()) as DashboardCommandPayload;
  const data = await commandAgent(payload, request.headers);
  return Response.json(data);
}


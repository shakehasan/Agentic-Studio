import { getBootstrap } from "@/lib/backend";

export async function GET(request: Request) {
  const data = await getBootstrap(request.headers);
  return Response.json(data);
}


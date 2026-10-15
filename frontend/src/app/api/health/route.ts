import { API_URL } from "@/lib/api";

export const dynamic = "force-dynamic";

/**
 * Reports whether the API is up, and wakes it if it is asleep.
 *
 * A free Render instance sleeps after 15 idle minutes, and waking it takes
 * 30-60s — which would otherwise be the next visitor's page load. The
 * keep-warm workflow (.github/workflows/keep-warm.yml) calls this route, so
 * it does not need to know the API's own URL.
 */
export async function GET() {
  const started = Date.now();
  try {
    const response = await fetch(`${API_URL}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    return Response.json(
      { api: response.ok ? "ok" : "error", status: response.status, ms: Date.now() - started },
      { status: response.ok ? 200 : 502 },
    );
  } catch (error) {
    return Response.json(
      { api: "unreachable", error: String(error), ms: Date.now() - started },
      { status: 502 },
    );
  }
}

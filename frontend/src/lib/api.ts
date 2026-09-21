const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

/**
 * Server-side fetch for PUBLIC data only (player/team/tournament listings,
 * standings, rankings, ...). Used from Server Components — talks to
 * Django directly, no auth involved. For anything that needs the current
 * user's identity, use lib/session.ts; for authenticated mutations from
 * Client Components, use lib/clientApi.ts (which goes through the
 * /api/proxy BFF route so the JWT never reaches the browser).
 */
export async function apiGet<T>(path: string, revalidateSeconds = 30): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: revalidateSeconds },
  });
  if (!res.ok) {
    throw new Error(`GET ${path} failed with ${res.status}`);
  }
  return res.json();
}

export async function apiGetOrNull<T>(path: string, revalidateSeconds = 30): Promise<T | null> {
  try {
    return await apiGet<T>(path, revalidateSeconds);
  } catch {
    return null;
  }
}

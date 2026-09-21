import { cookies } from "next/headers";

import { ACCESS_COOKIE } from "./authCookies";
import type { CurrentUser } from "./types";

const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

/**
 * Reads the current user server-side from the httpOnly access cookie.
 * Deliberately does NOT attempt a refresh here — Server Components can't
 * set cookies during render. If the access token has expired, the user
 * shows as logged out until they next hit a mutation (which goes through
 * the /api/proxy route and refreshes transparently) or log back in.
 */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  const store = await cookies();
  const token = store.get(ACCESS_COOKIE)?.value;
  if (!token) return null;

  const res = await fetch(`${API_URL}/auth/me/`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

/**
 * Authenticated server-side GET, for Server Components that need data
 * scoped to the current user (e.g. "does this user administer this
 * tournament?"). Read-only by design — no refresh-on-401 here, since
 * Server Components can't set cookies mid-render (see getCurrentUser).
 * Returns null on any failure (missing session, 401, 403, ...) so callers
 * can treat "not available" as "don't show this" rather than crashing.
 */
export async function apiGetAuthed<T>(path: string): Promise<T | null> {
  const store = await cookies();
  const token = store.get(ACCESS_COOKIE)?.value;
  if (!token) return null;

  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

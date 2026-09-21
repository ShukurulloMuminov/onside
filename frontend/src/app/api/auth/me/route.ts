import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, ACCESS_MAX_AGE, cookieOptions, REFRESH_COOKIE } from "@/lib/authCookies";

const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

export async function GET() {
  const store = await cookies();
  let token = store.get(ACCESS_COOKIE)?.value;
  const refreshToken = store.get(REFRESH_COOKIE)?.value;

  if (!token && !refreshToken) {
    return NextResponse.json({ user: null });
  }

  let res = token
    ? await fetch(`${API_URL}/auth/me/`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" })
    : null;

  let refreshedToken: string | null = null;
  if ((!res || res.status === 401) && refreshToken) {
    const refreshRes = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      refreshedToken = data.access;
      token = refreshedToken ?? undefined;
      res = await fetch(`${API_URL}/auth/me/`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
    }
  }

  if (!res || !res.ok) {
    return NextResponse.json({ user: null });
  }

  const user = await res.json();
  const response = NextResponse.json({ user });
  if (refreshedToken) {
    response.cookies.set(ACCESS_COOKIE, refreshedToken, { ...cookieOptions, maxAge: ACCESS_MAX_AGE });
  }
  return response;
}

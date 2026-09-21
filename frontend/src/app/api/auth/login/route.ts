import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, ACCESS_MAX_AGE, cookieOptions, REFRESH_COOKIE, REFRESH_MAX_AGE } from "@/lib/authCookies";

const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const tokenRes = await fetch(`${API_URL}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const tokenData = await tokenRes.json();
  if (!tokenRes.ok) {
    return NextResponse.json(tokenData, { status: tokenRes.status });
  }

  const meRes = await fetch(`${API_URL}/auth/me/`, {
    headers: { Authorization: `Bearer ${tokenData.access}` },
  });
  const user = await meRes.json();

  const store = await cookies();
  store.set(ACCESS_COOKIE, tokenData.access, { ...cookieOptions, maxAge: ACCESS_MAX_AGE });
  store.set(REFRESH_COOKIE, tokenData.refresh, { ...cookieOptions, maxAge: REFRESH_MAX_AGE });

  return NextResponse.json({ user });
}

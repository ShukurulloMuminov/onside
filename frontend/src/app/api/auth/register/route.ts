import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, ACCESS_MAX_AGE, cookieOptions, REFRESH_COOKIE, REFRESH_MAX_AGE } from "@/lib/authCookies";

const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

export async function POST(req: NextRequest) {
  const contentType = req.headers.get("content-type") ?? "";
  const isMultipart = contentType.startsWith("multipart/form-data");

  // A picked avatar file arrives as multipart/form-data — forwarded as
  // FormData so fetch regenerates a correct boundary (reading it as text
  // would corrupt the binary data). Plain registrations stay JSON.
  let registerRes: Response;
  let username: string;
  let password: string;
  if (isMultipart) {
    const formData = await req.formData();
    username = String(formData.get("username") ?? "");
    password = String(formData.get("password") ?? "");
    registerRes = await fetch(`${API_URL}/auth/register/`, { method: "POST", body: formData });
  } else {
    const body = await req.json();
    username = body.username;
    password = body.password;
    registerRes = await fetch(`${API_URL}/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  const registerData = await registerRes.json();
  if (!registerRes.ok) {
    return NextResponse.json(registerData, { status: registerRes.status });
  }

  const tokenRes = await fetch(`${API_URL}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
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

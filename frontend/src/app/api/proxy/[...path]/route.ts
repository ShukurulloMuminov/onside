import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, ACCESS_MAX_AGE, cookieOptions, REFRESH_COOKIE } from "@/lib/authCookies";

const API_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8010/api/v1";

async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  const res = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.access ?? null;
}

async function forward(req: NextRequest, path: string[], method: string) {
  const store = await cookies();
  const accessToken = store.get(ACCESS_COOKIE)?.value;
  const refreshToken = store.get(REFRESH_COOKIE)?.value;

  const targetPath = "/" + path.join("/") + "/";
  const url = `${API_URL}${targetPath}${req.nextUrl.search}`;

  const hasBody = !["GET", "DELETE", "HEAD"].includes(method);
  const contentType = req.headers.get("content-type") ?? "";
  const isMultipart = contentType.startsWith("multipart/form-data");

  // Multipart bodies (avatar/logo uploads) go through as FormData so fetch
  // regenerates a correct Content-Type + boundary — reading them as text
  // would corrupt the binary file data. Everything else (JSON) is passed
  // through as raw text with its original Content-Type preserved.
  const body: BodyInit | undefined = !hasBody
    ? undefined
    : isMultipart
      ? await req.formData()
      : await req.text();

  const doFetch = (token?: string) =>
    fetch(url, {
      method,
      headers: {
        ...(hasBody && !isMultipart ? { "Content-Type": contentType || "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body,
    });

  let res = await doFetch(accessToken);
  let newAccessToken: string | null = null;

  if (res.status === 401 && refreshToken) {
    newAccessToken = await refreshAccessToken(refreshToken);
    if (newAccessToken) {
      res = await doFetch(newAccessToken);
    }
  }

  const responseText = await res.text();
  const response = new NextResponse(responseText || null, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });

  if (newAccessToken) {
    response.cookies.set(ACCESS_COOKIE, newAccessToken, { ...cookieOptions, maxAge: ACCESS_MAX_AGE });
  }
  return response;
}

type RouteParams = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, { params }: RouteParams) {
  return forward(req, (await params).path, "GET");
}
export async function POST(req: NextRequest, { params }: RouteParams) {
  return forward(req, (await params).path, "POST");
}
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  return forward(req, (await params).path, "PATCH");
}
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  return forward(req, (await params).path, "DELETE");
}

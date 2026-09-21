/**
 * Client Component fetch helper. Always goes through /api/proxy so the
 * browser never sees the Django origin or the JWT — the proxy route
 * attaches the access token server-side and silently refreshes it on a
 * 401 (see app/api/proxy/[...path]/route.ts).
 */
export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super(`API request failed with ${status}`);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const res = await fetch(`/api/proxy${path}`, {
    ...options,
    headers: {
      // For FormData, no Content-Type here — the browser sets
      // multipart/form-data with the correct boundary itself.
      ...(options.body && !isFormData ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
    credentials: "include",
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, data);
  }
  return data as T;
}

function encodeBody(body: unknown): BodyInit | undefined {
  if (body === undefined) return undefined;
  return body instanceof FormData ? body : JSON.stringify(body);
}

export const clientApi = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: encodeBody(body) }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body: encodeBody(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

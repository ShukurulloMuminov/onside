export const ACCESS_COOKIE = "onside_access";
export const REFRESH_COOKIE = "onside_refresh";

// Slightly shorter than the backend's actual token lifetimes (30 min /
// 14 days) so the cookie never outlives a token the browser still holds.
export const ACCESS_MAX_AGE = 60 * 28;
export const REFRESH_MAX_AGE = 60 * 60 * 24 * 13;

export const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

const DJANGO_ORIGIN = process.env.NEXT_PUBLIC_DJANGO_ORIGIN ?? "http://127.0.0.1:8010";

/**
 * Most API responses return absolute media URLs (DRF includes the request
 * in serializer context automatically), but a few computed endpoints
 * (rankings, standings, bracket) build serializers by hand without a
 * request in context, so ImageField falls back to a root-relative path.
 * Resolving both cases here keeps every <img> consumer simple.
 */
export function resolveMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^(https?|blob|data):/.test(url)) return url;
  return `${DJANGO_ORIGIN}${url.startsWith("/") ? "" : "/"}${url}`;
}

import Link from "next/link";

export default function Pagination({
  count,
  pageSize,
  currentPage,
  makeHref,
}: {
  count: number;
  pageSize: number;
  currentPage: number;
  makeHref: (page: number) => string;
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;

  const pages = pageNumbersToShow(currentPage, totalPages);

  return (
    <nav className="flex items-center justify-center gap-1.5 pt-2" aria-label="Sahifalash">
      <PageLink href={makeHref(currentPage - 1)} disabled={currentPage <= 1}>
        &larr;
      </PageLink>
      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`ellipsis-${i}`} className="px-1.5 text-sm text-muted">
            …
          </span>
        ) : (
          <PageLink key={p} href={makeHref(p)} active={p === currentPage}>
            {p}
          </PageLink>
        ),
      )}
      <PageLink href={makeHref(currentPage + 1)} disabled={currentPage >= totalPages}>
        &rarr;
      </PageLink>
    </nav>
  );
}

function PageLink({
  href,
  children,
  active,
  disabled,
}: {
  href: string;
  children: React.ReactNode;
  active?: boolean;
  disabled?: boolean;
}) {
  const base = "flex h-9 min-w-9 items-center justify-center rounded-full px-2.5 text-sm font-medium transition";
  if (disabled) {
    return <span className={`${base} text-muted/40`}>{children}</span>;
  }
  return (
    <Link href={href} className={`${base} ${active ? "bg-blue text-white" : "text-foreground hover:bg-surface"}`}>
      {children}
    </Link>
  );
}

function pageNumbersToShow(current: number, total: number): (number | "...")[] {
  const delta = 1;
  const left = Math.max(2, current - delta);
  const right = Math.min(total - 1, current + delta);

  const range: (number | "...")[] = [1];
  if (left > 2) range.push("...");
  for (let i = left; i <= right; i++) range.push(i);
  if (right < total - 1) range.push("...");
  if (total > 1) range.push(total);
  return range;
}

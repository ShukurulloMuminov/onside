import Link from "next/link";

import Pagination from "@/components/Pagination";
import TeamCard from "@/components/TeamCard";
import { apiGetOrNull } from "@/lib/api";
import type { Paginated, Team } from "@/lib/types";

const PAGE_SIZE = 20;

export default async function TeamsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; page?: string }>;
}) {
  const params = await searchParams;
  const currentPage = Math.max(1, Number(params.page) || 1);
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (currentPage > 1) query.set("page", String(currentPage));

  const teams = await apiGetOrNull<Paginated<Team>>(`/teams/?${query.toString()}`, 10);

  function makeHref(page: number) {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    if (page > 1) q.set("page", String(page));
    const qs = q.toString();
    return qs ? `/teams?${qs}` : "/teams";
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Jamoalar</h1>
          <p className="text-sm text-muted">Barcha ro&apos;yxatdan o&apos;tgan jamoalar.</p>
        </div>
        <Link
          href="/teams/new"
          className="rounded-full bg-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-dark"
        >
          + Yangi jamoa yaratish
        </Link>
      </div>

      <form className="card flex items-end gap-3 p-4" method="get">
        <label className="flex flex-1 flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Qidiruv</span>
          <input name="search" defaultValue={params.search} placeholder="Jamoa nomi yoki shahar" className="input" />
        </label>
        <button type="submit" className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark">
          Qidirish
        </button>
      </form>

      {teams && teams.results.length > 0 ? (
        <div className="grid gap-3">
          {teams.results.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      ) : (
        <div className="card p-6 text-center text-sm text-muted">Jamoalar topilmadi.</div>
      )}

      {teams ? <Pagination count={teams.count} pageSize={PAGE_SIZE} currentPage={currentPage} makeHref={makeHref} /> : null}
    </div>
  );
}

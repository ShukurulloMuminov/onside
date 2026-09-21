import Pagination from "@/components/Pagination";
import TournamentCard from "@/components/TournamentCard";
import { TOURNAMENT_STATUS_LABEL } from "@/lib/format";
import { apiGetOrNull } from "@/lib/api";
import type { Paginated, Tournament, TournamentStatus } from "@/lib/types";

const STATUSES: TournamentStatus[] = [
  "registration_open",
  "registration_closed",
  "in_progress",
  "finished",
];
const PAGE_SIZE = 20;

export default async function TournamentsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; city?: string; status?: string; page?: string }>;
}) {
  const params = await searchParams;
  const currentPage = Math.max(1, Number(params.page) || 1);
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.city) query.set("city", params.city);
  if (params.status) query.set("status", params.status);
  if (currentPage > 1) query.set("page", String(currentPage));

  const tournaments = await apiGetOrNull<Paginated<Tournament>>(`/tournaments/?${query.toString()}`, 10);

  function makeHref(page: number) {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    if (params.city) q.set("city", params.city);
    if (params.status) q.set("status", params.status);
    if (page > 1) q.set("page", String(page));
    const qs = q.toString();
    return qs ? `/tournaments?${qs}` : "/tournaments";
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Turnirlar</h1>
        <p className="text-sm text-muted">Yaqin va faol turnirlarni toping.</p>
      </div>

      <form className="card flex flex-wrap items-end gap-3 p-4" method="get">
        <label className="flex flex-1 min-w-[180px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Qidiruv</span>
          <input name="search" defaultValue={params.search} placeholder="Turnir nomi" className="input" />
        </label>
        <label className="flex min-w-[140px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Shahar</span>
          <input name="city" defaultValue={params.city} className="input" />
        </label>
        <label className="flex min-w-[180px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Holat</span>
          <select name="status" defaultValue={params.status ?? ""} className="input">
            <option value="">Barchasi</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {TOURNAMENT_STATUS_LABEL[s]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark">
          Qidirish
        </button>
      </form>

      {tournaments && tournaments.results.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tournaments.results.map((t) => (
            <TournamentCard key={t.id} tournament={t} />
          ))}
        </div>
      ) : (
        <div className="card p-6 text-center text-sm text-muted">Turnirlar topilmadi.</div>
      )}

      {tournaments ? (
        <Pagination count={tournaments.count} pageSize={PAGE_SIZE} currentPage={currentPage} makeHref={makeHref} />
      ) : null}
    </div>
  );
}

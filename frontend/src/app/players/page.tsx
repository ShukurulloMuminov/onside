import Pagination from "@/components/Pagination";
import PlayerCard from "@/components/PlayerCard";
import { POSITION_LABEL } from "@/lib/format";
import { apiGetOrNull } from "@/lib/api";
import type { Paginated, PlayerProfile, Position } from "@/lib/types";

const POSITIONS: Position[] = ["GK", "DF", "MF", "FW"];
const PAGE_SIZE = 20;

export default async function PlayersPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; city?: string; position?: string; page?: string }>;
}) {
  const params = await searchParams;
  const playerIdMatch = params.search?.trim().match(/^#?(\d+)$/);
  const currentPage = Math.max(1, Number(params.page) || 1);

  let players: Paginated<PlayerProfile> | null;
  if (playerIdMatch) {
    // Player ID isn't a real DB column (it's derived from the pk), so a
    // numeric search goes straight to the detail lookup instead of the
    // text search endpoint.
    const single = await apiGetOrNull<PlayerProfile>(`/players/${playerIdMatch[1]}/`, 10);
    players = single ? { count: 1, next: null, previous: null, results: [single] } : { count: 0, next: null, previous: null, results: [] };
  } else {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.city) query.set("city", params.city);
    if (params.position) query.set("position", params.position);
    if (currentPage > 1) query.set("page", String(currentPage));
    players = await apiGetOrNull<Paginated<PlayerProfile>>(`/players/?${query.toString()}`, 10);
  }

  function makeHref(page: number) {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.city) query.set("city", params.city);
    if (params.position) query.set("position", params.position);
    if (page > 1) query.set("page", String(page));
    const qs = query.toString();
    return qs ? `/players?${qs}` : "/players";
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">O&apos;yinchilar</h1>
        <p className="text-sm text-muted">Player ID orqali qidiring yoki shahar/pozitsiya bo&apos;yicha filtrlang.</p>
      </div>

      <form className="card flex flex-wrap items-end gap-3 p-4" method="get">
        <label className="flex flex-1 min-w-[180px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Qidiruv</span>
          <input name="search" defaultValue={params.search} placeholder="Ism yoki Player ID" className="input" />
        </label>
        <label className="flex min-w-[140px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Shahar</span>
          <input name="city" defaultValue={params.city} className="input" />
        </label>
        <label className="flex min-w-[160px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Pozitsiya</span>
          <select name="position" defaultValue={params.position ?? ""} className="input">
            <option value="">Barchasi</option>
            {POSITIONS.map((p) => (
              <option key={p} value={p}>
                {POSITION_LABEL[p]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark">
          Qidirish
        </button>
      </form>

      {players && players.results.length > 0 ? (
        <div className="grid gap-3">
          {players.results.map((player) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      ) : (
        <div className="card p-6 text-center text-sm text-muted">Hech kim topilmadi.</div>
      )}

      {players && !playerIdMatch ? (
        <Pagination count={players.count} pageSize={PAGE_SIZE} currentPage={currentPage} makeHref={makeHref} />
      ) : null}
    </div>
  );
}

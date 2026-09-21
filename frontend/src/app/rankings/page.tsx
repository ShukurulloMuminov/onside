import Link from "next/link";

import Avatar from "@/components/Avatar";
import { apiGetOrNull } from "@/lib/api";
import type { Paginated, RankingRow, Tournament } from "@/lib/types";

export default async function RankingsPage({
  searchParams,
}: {
  searchParams: Promise<{ scope?: string; tournament?: string }>;
}) {
  const params = await searchParams;
  const scope = params.scope === "tournament" ? "tournament" : "global";

  const tournaments = await apiGetOrNull<Paginated<Tournament>>("/tournaments/?ordering=-start_date", 60);
  const tournamentSlug = params.tournament || tournaments?.results[0]?.slug;

  const query = new URLSearchParams({ scope, limit: "50" });
  if (scope === "tournament" && tournamentSlug) query.set("tournament", tournamentSlug);

  const rankings =
    scope === "tournament" && !tournamentSlug
      ? []
      : (await apiGetOrNull<RankingRow[]>(`/rankings/players/?${query.toString()}`, 15)) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Reyting</h1>
        <p className="text-sm text-muted">Gollar, assistlar, g&apos;alabalar va MVP asosida hisoblangan reyting.</p>
      </div>

      <form className="card flex flex-wrap items-end gap-3 p-4" method="get">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Ko&apos;lam</span>
          <select name="scope" defaultValue={scope} className="input">
            <option value="global">Umumiy</option>
            <option value="tournament">Turnir bo&apos;yicha</option>
          </select>
        </label>
        <label className="flex min-w-[220px] flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Turnir</span>
          <select name="tournament" defaultValue={tournamentSlug} className="input">
            {tournaments?.results.map((t) => (
              <option key={t.slug} value={t.slug}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark">
          Ko&apos;rsatish
        </button>
      </form>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
              <th className="py-3 pl-4">#</th>
              <th className="py-3">O&apos;yinchi</th>
              <th className="px-2 py-3 text-center">O&apos;yin</th>
              <th className="px-2 py-3 text-center">Gol</th>
              <th className="px-2 py-3 text-center">Assist</th>
              <th className="px-2 py-3 text-center">G&apos;alaba</th>
              <th className="px-2 py-3 text-center">MVP</th>
              <th className="py-3 pr-4 text-center">Ball</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((row, i) => (
              <tr key={row.player.id} className="border-b border-border last:border-0">
                <td className="py-3 pl-4 font-medium text-muted">{i + 1}</td>
                <td className="py-3">
                  <Link
                    href={`/players/${row.player.player_id.replace("#", "")}`}
                    className="flex items-center gap-2 font-medium text-foreground hover:text-blue"
                  >
                    <Avatar src={row.player.avatar} name={row.player.full_name} size={28} />
                    {row.player.full_name}
                  </Link>
                </td>
                <td className="px-2 py-3 text-center">{row.matches}</td>
                <td className="px-2 py-3 text-center">{row.goals}</td>
                <td className="px-2 py-3 text-center">{row.assists}</td>
                <td className="px-2 py-3 text-center">{row.wins}</td>
                <td className="px-2 py-3 text-center">{row.mvp}</td>
                <td className="py-3 pr-4 text-center font-bold text-navy">{row.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rankings.length === 0 ? <p className="p-6 text-center text-sm text-muted">Ma&apos;lumot yo&apos;q.</p> : null}
      </div>
    </div>
  );
}

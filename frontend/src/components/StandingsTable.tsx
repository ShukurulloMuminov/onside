import Link from "next/link";

import type { GroupStandingRow } from "@/lib/types";

export default function StandingsTable({ rows }: { rows: GroupStandingRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
            <th className="py-2 pr-2">#</th>
            <th className="py-2 pr-2">Jamoa</th>
            <th className="px-2 py-2 text-center">O</th>
            <th className="px-2 py-2 text-center">G</th>
            <th className="px-2 py-2 text-center">D</th>
            <th className="px-2 py-2 text-center">M</th>
            <th className="px-2 py-2 text-center">GF</th>
            <th className="px-2 py-2 text-center">GQ</th>
            <th className="px-2 py-2 text-center">FarQ</th>
            <th className="py-2 pl-2 text-center">Ball</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.registration_id}
              className={`border-b border-border last:border-0 ${row.qualifies ? "bg-blue-light/40" : ""}`}
            >
              <td className="py-2 pr-2 font-medium text-muted">{row.position}</td>
              <td className="py-2 pr-2 font-medium text-foreground">
                <Link href={`/teams/${row.team.slug}`} className="hover:text-blue">
                  {row.team.name}
                </Link>
              </td>
              <td className="px-2 py-2 text-center">{row.played}</td>
              <td className="px-2 py-2 text-center">{row.won}</td>
              <td className="px-2 py-2 text-center">{row.draw}</td>
              <td className="px-2 py-2 text-center">{row.lost}</td>
              <td className="px-2 py-2 text-center">{row.goals_for}</td>
              <td className="px-2 py-2 text-center">{row.goals_against}</td>
              <td className="px-2 py-2 text-center">
                {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
              </td>
              <td className="py-2 pl-2 text-center font-bold text-navy">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

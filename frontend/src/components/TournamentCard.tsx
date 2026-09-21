import Link from "next/link";

import { formatDate, TOURNAMENT_STATUS_LABEL } from "@/lib/format";
import type { Tournament } from "@/lib/types";

import Badge from "./Badge";

const STATUS_TONE: Record<Tournament["status"], "neutral" | "win" | "draw" | "navy"> = {
  draft: "neutral",
  pending_approval: "draw",
  published: "neutral",
  registration_open: "win",
  registration_closed: "draw",
  in_progress: "navy",
  finished: "neutral",
  cancelled: "neutral",
};

const STATUS_BAR: Record<Tournament["status"], string> = {
  draft: "bg-muted/40",
  pending_approval: "bg-draw",
  published: "bg-muted/40",
  registration_open: "bg-win",
  registration_closed: "bg-draw",
  in_progress: "bg-blue",
  finished: "bg-muted/40",
  cancelled: "bg-loss",
};

export default function TournamentCard({ tournament }: { tournament: Tournament }) {
  const fillPct = tournament.max_teams > 0 ? Math.min(100, (tournament.team_count / tournament.max_teams) * 100) : 0;

  return (
    <Link href={`/tournaments/${tournament.slug}`} className="card card-interactive flex flex-col overflow-hidden">
      <span className={`h-1 w-full ${STATUS_BAR[tournament.status]}`} />
      <div className="flex flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-bold tracking-tight text-foreground">{tournament.name}</h3>
          <Badge tone={STATUS_TONE[tournament.status]}>{TOURNAMENT_STATUS_LABEL[tournament.status]}</Badge>
        </div>
        <p className="text-sm text-muted">
          {tournament.city || "Shahar ko'rsatilmagan"} · {formatDate(tournament.start_date)}
        </p>
        <div className="flex flex-col gap-1.5">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
            <div className="h-full rounded-full bg-blue" style={{ width: `${fillPct}%` }} />
          </div>
          <p className="text-xs font-medium text-muted">
            {tournament.team_count} / {tournament.max_teams} jamoa
          </p>
        </div>
      </div>
    </Link>
  );
}

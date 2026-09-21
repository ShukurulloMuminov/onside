import Link from "next/link";

import { formatDate, formatTime, MATCH_STATUS_LABEL } from "@/lib/format";
import type { Match } from "@/lib/types";

import Avatar from "./Avatar";
import Badge from "./Badge";

export default function MatchCard({ match }: { match: Match }) {
  const isFinished = match.status === "finished";

  return (
    <Link href={`/matches/${match.id}`} className="card card-interactive flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between text-xs text-muted">
        <span>
          {formatDate(match.scheduled_date)} {formatTime(match.scheduled_time)}
        </span>
        <Badge tone={isFinished ? "neutral" : match.status === "live" ? "win" : "neutral"}>
          {MATCH_STATUS_LABEL[match.status]}
        </Badge>
      </div>
      <div className="flex items-center justify-between gap-3">
        <TeamRow name={match.home_team?.name ?? "TBD"} logo={match.home_team?.logo} />
        <div className="shrink-0 text-xl font-extrabold tracking-tight text-navy">
          {isFinished || match.status === "live" ? (
            <span>
              {match.home_score ?? 0}<span className="mx-1 text-muted">:</span>{match.away_score ?? 0}
            </span>
          ) : (
            <span className="text-sm font-semibold text-muted">vs</span>
          )}
        </div>
        <TeamRow name={match.away_team?.name ?? "TBD"} logo={match.away_team?.logo} reverse />
      </div>
      {match.venue ? <p className="text-xs text-muted">{match.venue}</p> : null}
    </Link>
  );
}

function TeamRow({ name, logo, reverse }: { name: string; logo?: string | null; reverse?: boolean }) {
  return (
    <div className={`flex min-w-0 flex-1 items-center gap-2 ${reverse ? "flex-row-reverse text-right" : ""}`}>
      <Avatar src={logo} name={name} size={28} rounded="md" />
      <span className="truncate text-sm font-medium text-foreground">{name}</span>
    </div>
  );
}

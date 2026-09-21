import { notFound } from "next/navigation";
import Link from "next/link";

import Avatar from "@/components/Avatar";
import Badge from "@/components/Badge";
import MatchAdminPanel from "@/components/MatchAdminPanel";
import MatchConfirmPanel from "@/components/MatchConfirmPanel";
import { apiGetOrNull } from "@/lib/api";
import { formatDate, formatTime, MATCH_STATUS_LABEL } from "@/lib/format";
import { apiGetAuthed, getCurrentUser } from "@/lib/session";
import type { Match, Team, TeamMembership } from "@/lib/types";

const EVENT_ICON: Record<string, string> = {
  goal: "⚽",
  assist: "🎯",
  yellow_card: "🟨",
  red_card: "🟥",
  own_goal: "⚽️(o'z darvozasiga)",
  substitution: "🔄",
  mvp: "⭐",
};

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  // no-store: the admin panel below posts result/event edits and lands
  // back here expecting to see them reflected immediately.
  const [match, currentUser] = await Promise.all([
    apiGetOrNull<Match>(`/matches/${id}/`, 0),
    getCurrentUser(),
  ]);

  if (!match) notFound();

  const registrations = currentUser
    ? await apiGetAuthed(`/tournaments/${match.tournament_slug}/registrations/`)
    : null;
  const isAdmin = registrations !== null;

  const [homeRoster, awayRoster, homeTeam, awayTeam] = await Promise.all([
    match.home_team ? apiGetOrNull<TeamMembership[]>(`/teams/${match.home_team.slug}/members/`, 30) : null,
    match.away_team ? apiGetOrNull<TeamMembership[]>(`/teams/${match.away_team.slug}/members/`, 30) : null,
    match.home_team ? apiGetOrNull<Team>(`/teams/${match.home_team.slug}/`, 30) : null,
    match.away_team ? apiGetOrNull<Team>(`/teams/${match.away_team.slug}/`, 30) : null,
  ]);

  const isHomeCaptain = Boolean(currentUser && homeTeam?.captain.username === currentUser.username);
  const isAwayCaptain = Boolean(currentUser && awayTeam?.captain.username === currentUser.username);
  const isCaptain = isHomeCaptain || isAwayCaptain;

  return (
    <div className="flex flex-col gap-6">
      <div className="card flex flex-col gap-4 p-6">
        <div className="flex items-center justify-between text-sm text-muted">
          <Link href={`/tournaments/${match.tournament_slug}`} className="font-medium text-blue hover:text-blue-dark">
            {match.tournament_name}
          </Link>
          <Badge tone={match.status === "live" ? "win" : "neutral"}>{MATCH_STATUS_LABEL[match.status]}</Badge>
        </div>

        <div className="flex items-center justify-between gap-4">
          <TeamColumn name={match.home_team?.name ?? "TBD"} logo={match.home_team?.logo} slug={match.home_team?.slug} />
          <div className="shrink-0 text-center">
            <p className="text-3xl font-bold text-navy">
              {match.home_score ?? "-"} : {match.away_score ?? "-"}
            </p>
            {match.penalty_home_score !== null ? (
              <p className="text-xs text-muted">
                Penalti: {match.penalty_home_score} - {match.penalty_away_score}
              </p>
            ) : null}
          </div>
          <TeamColumn name={match.away_team?.name ?? "TBD"} logo={match.away_team?.logo} slug={match.away_team?.slug} reverse />
        </div>

        <p className="text-center text-sm text-muted">
          {formatDate(match.scheduled_date)} {formatTime(match.scheduled_time)}
          {match.venue ? ` · ${match.venue}` : ""}
          {match.referee ? ` · Hakam: ${match.referee}` : ""}
        </p>
      </div>

      {match.events.length > 0 ? (
        <div className="card p-6">
          <h2 className="mb-3 font-semibold text-foreground">O&apos;yin lavhalari</h2>
          <ul className="flex flex-col gap-2">
            {match.events.map((event) => (
              <li key={event.id} className="flex items-center gap-3 text-sm">
                <span className="w-10 text-muted">{event.minute != null ? `${event.minute}'` : ""}</span>
                <span>{EVENT_ICON[event.type] ?? "•"}</span>
                <span className="font-medium text-foreground">{event.player.full_name}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!isAdmin && isCaptain && match.status === "pending_confirmation" ? (
        <MatchConfirmPanel match={match} />
      ) : null}

      {isAdmin ? (
        <MatchAdminPanel
          match={match}
          homeRoster={homeRoster ?? []}
          awayRoster={awayRoster ?? []}
        />
      ) : null}
    </div>
  );
}

function TeamColumn({
  name,
  logo,
  slug,
  reverse,
}: {
  name: string;
  logo?: string | null;
  slug?: string;
  reverse?: boolean;
}) {
  const content = (
    <div className={`flex flex-1 flex-col items-center gap-2 ${reverse ? "" : ""}`}>
      <Avatar src={logo} name={name} size={48} rounded="md" />
      <span className="text-center text-sm font-semibold text-foreground">{name}</span>
    </div>
  );
  return slug ? <Link href={`/teams/${slug}`}>{content}</Link> : content;
}

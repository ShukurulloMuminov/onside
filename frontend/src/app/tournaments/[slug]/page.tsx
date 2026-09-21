import { notFound } from "next/navigation";

import Badge from "@/components/Badge";
import ApplyToTournamentPanel from "@/components/ApplyToTournamentPanel";
import TournamentAdminPanel from "@/components/TournamentAdminPanel";
import TournamentSettingsForm from "@/components/TournamentSettingsForm";
import TournamentTabs from "@/components/TournamentTabs";
import { apiGetOrNull } from "@/lib/api";
import { formatDate, TOURNAMENT_FORMAT_LABEL, TOURNAMENT_STATUS_LABEL } from "@/lib/format";
import { apiGetAuthed, getCurrentUser } from "@/lib/session";
import type {
  Match,
  Tournament,
  TournamentBracket,
  TournamentRegistration,
  TournamentStandings,
} from "@/lib/types";

export default async function TournamentDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  // no-store: registration approval, group/knockout generation, and match
  // results all land the admin back on this page expecting to see the
  // result immediately, not up to 10s of stale cache.
  const [tournament, standings, bracket, matches, currentUser] = await Promise.all([
    apiGetOrNull<Tournament>(`/tournaments/${slug}/`, 0),
    apiGetOrNull<TournamentStandings>(`/tournaments/${slug}/standings/`, 0),
    apiGetOrNull<TournamentBracket>(`/tournaments/${slug}/bracket/`, 0),
    apiGetOrNull<Match[]>(`/tournaments/${slug}/matches/`, 0),
    getCurrentUser(),
  ]);

  if (!tournament) notFound();

  const registrations = currentUser
    ? await apiGetAuthed<TournamentRegistration[]>(`/tournaments/${slug}/registrations/`)
    : null;
  const isAdmin = registrations !== null;

  return (
    <div className="flex flex-col gap-6">
      <div className="card flex flex-col gap-3 p-6">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="text-2xl font-bold text-foreground">{tournament.name}</h1>
          <Badge tone="navy">{TOURNAMENT_STATUS_LABEL[tournament.status]}</Badge>
        </div>
        <p className="text-sm text-muted">
          {tournament.city} {tournament.venue ? `· ${tournament.venue}` : ""} · {formatDate(tournament.start_date)}
          {tournament.end_date ? ` – ${formatDate(tournament.end_date)}` : ""}
        </p>
        <p className="text-sm text-muted">
          {TOURNAMENT_FORMAT_LABEL[tournament.format]} · {tournament.team_count}/{tournament.max_teams} jamoa
          {tournament.organizer ? ` · Tashkilotchi: ${tournament.organizer}` : ""}
        </p>
        {tournament.description ? <p className="max-w-2xl text-sm text-foreground">{tournament.description}</p> : null}
        {tournament.prize_info ? (
          <p className="text-sm font-medium text-navy">Mukofot: {tournament.prize_info}</p>
        ) : null}
      </div>

      {currentUser && !isAdmin && tournament.status === "registration_open" ? (
        <ApplyToTournamentPanel tournamentSlug={tournament.slug} />
      ) : null}

      {isAdmin && registrations ? (
        <>
          <TournamentAdminPanel
            tournament={tournament}
            registrations={registrations}
            hasGroups={standings ? standings.groups.length > 0 : false}
            hasBracket={bracket ? bracket.rounds.length > 0 : false}
          />
          <TournamentSettingsForm key={tournament.groups_count} tournament={tournament} />
        </>
      ) : null}

      <TournamentTabs
        standings={standings ?? { groups: [] }}
        bracket={bracket ?? { rounds: [] }}
        matches={matches ?? []}
      />
    </div>
  );
}

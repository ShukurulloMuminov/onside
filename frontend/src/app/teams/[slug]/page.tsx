import { notFound } from "next/navigation";

import Avatar from "@/components/Avatar";
import PitchLineup from "@/components/PitchLineup";
import PlayerCard from "@/components/PlayerCard";
import StatTile from "@/components/StatTile";
import TeamEditForm from "@/components/TeamEditForm";
import TeamLineupEditForm from "@/components/TeamLineupEditForm";
import TeamManagePanel from "@/components/TeamManagePanel";
import { apiGetOrNull } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { getCurrentUser } from "@/lib/session";
import type { Team, TeamLineup, TeamMembership } from "@/lib/types";

export default async function TeamDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // no-store: this page is where invite/accept/edit actions land immediately
  // after the user performs them, so it must always reflect the current
  // state rather than serve a stale cached response.
  const [team, members, lineup, currentUser] = await Promise.all([
    apiGetOrNull<Team>(`/teams/${slug}/`, 0),
    apiGetOrNull<TeamMembership[]>(`/teams/${slug}/members/`, 0),
    apiGetOrNull<TeamLineup>(`/teams/${slug}/lineup/`, 0),
    getCurrentUser(),
  ]);

  if (!team) notFound();

  const isCaptain = currentUser?.username === team.captain.username;
  const hasLineup = lineup ? lineup.slots.some((s) => s.player) : false;

  return (
    <div className="flex flex-col gap-6">
      <div className="card flex flex-col items-start gap-4 p-6 sm:flex-row sm:items-center">
        <div className="rounded-xl ring-4 ring-blue-light">
          <Avatar src={team.logo} name={team.name} size={72} rounded="md" />
        </div>
        <div className="flex-1">
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">{team.name}</h1>
          <p className="text-sm text-muted">
            {team.city}
            {team.founded_date ? ` · ${formatDate(team.founded_date)} dan buyon` : ""}
          </p>
          <p className="mt-1 text-sm text-muted">
            Sardor: <span className="font-medium text-foreground">{team.captain.full_name}</span>
          </p>
          {team.description ? <p className="mt-3 max-w-xl text-sm text-foreground">{team.description}</p> : null}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="O'yinlar" value={team.matches_total} />
        <StatTile label="G'alabalar" value={team.wins_total} />
        <StatTile label="Duranglar" value={team.draws_total} />
        <StatTile label="Mag'lubiyatlar" value={team.losses_total} />
        <StatTile label="Urilgan gol" value={team.goals_for_total} />
        <StatTile label="O'tkazilgan gol" value={team.goals_against_total} />
        <StatTile label="Turnirlar" value={team.tournaments_total} />
        <StatTile label="Sovrinlar" value={team.trophies_total} />
      </div>

      {isCaptain ? (
        <>
          <TeamManagePanel team={team} />
          <TeamEditForm team={team} />
          <TeamLineupEditForm
            // Remount when squad_size changes: internal formation/assignments
            // state is only computed from props on first mount (a plain
            // useState re-render won't pick up new initialLineup/squadSize
            // otherwise), so a stale 11-a-side lineup could linger in the
            // editor after switching to 5x5/7x7.
            key={team.squad_size}
            teamSlug={team.slug}
            squadSize={team.squad_size}
            members={members ?? []}
            initialLineup={lineup}
          />
        </>
      ) : hasLineup && lineup ? (
        <div className="card p-6">
          <h2 className="mb-4 font-semibold text-foreground">Asosiy tarkib</h2>
          <PitchLineup formation={lineup.formation} slots={lineup.slots} />
        </div>
      ) : null}

      <div>
        <h2 className="mb-3 text-lg font-bold text-foreground">Tarkib ({team.member_count})</h2>
        <div className="grid gap-3">
          {members?.map((m) => <PlayerCard key={m.id} player={m.player} />)}
        </div>
      </div>
    </div>
  );
}

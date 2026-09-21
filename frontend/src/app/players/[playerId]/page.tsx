import { notFound } from "next/navigation";

import Avatar from "@/components/Avatar";
import Badge from "@/components/Badge";
import EditProfileForm from "@/components/EditProfileForm";
import StatTile from "@/components/StatTile";
import { apiGetOrNull } from "@/lib/api";
import { POSITION_LABEL } from "@/lib/format";
import { getCurrentUser } from "@/lib/session";
import type { PlayerProfile } from "@/lib/types";

export default async function PlayerDetailPage({
  params,
}: {
  params: Promise<{ playerId: string }>;
}) {
  const { playerId } = await params;
  const [player, currentUser] = await Promise.all([
    apiGetOrNull<PlayerProfile>(`/players/${playerId}/`, 10),
    getCurrentUser(),
  ]);

  if (!player) notFound();

  const isOwnProfile = currentUser?.username === player.username;

  return (
    <div className="flex flex-col gap-6">
      <div className="card flex flex-col items-start gap-4 p-6 sm:flex-row sm:items-center">
        <div className="rounded-full ring-4 ring-blue-light">
          <Avatar src={player.avatar} name={player.full_name} size={80} />
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground">{player.full_name}</h1>
            <Badge>{player.player_id}</Badge>
            {player.level ? (
              <Badge tone="navy">
                {player.level.icon} {player.level.name}
              </Badge>
            ) : null}
          </div>
          <p className="text-sm text-muted">
            {POSITION_LABEL[player.position]}
            {player.city ? ` · ${player.city}` : ""}
          </p>
          {player.badges.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-2">
              {player.badges.map((pb) => (
                <span
                  key={pb.id}
                  title={pb.badge.description}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-light px-2.5 py-1 text-xs font-medium text-blue-dark"
                >
                  <span>{pb.badge.icon}</span>
                  {pb.badge.name}
                </span>
              ))}
            </div>
          ) : null}
          {player.current_team ? (
            <a href={`/teams/${player.current_team.slug}`} className="mt-1 inline-block text-sm font-medium text-blue">
              {player.current_team.name}
            </a>
          ) : (
            <p className="mt-1 text-sm text-muted">Jamoasi yo&apos;q</p>
          )}
          {player.bio ? <p className="mt-3 max-w-xl text-sm text-foreground">{player.bio}</p> : null}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
        <StatTile label="O'yinlar" value={player.matches_total} />
        <StatTile label="Gollar" value={player.goals_total} />
        <StatTile label="Assistlar" value={player.assists_total} />
        <StatTile label="G'alabalar" value={player.wins_total} />
        <StatTile label="MVP" value={player.mvp_total} />
        <StatTile label="Sariq karta" value={player.yellow_cards_total} />
        <StatTile label="Qizil karta" value={player.red_cards_total} />
        <StatTile label="Turnirlar" value={player.tournaments_total} />
      </div>

      {isOwnProfile ? <EditProfileForm player={player} /> : null}
    </div>
  );
}

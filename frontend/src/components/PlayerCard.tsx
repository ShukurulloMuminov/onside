import Link from "next/link";

import { POSITION_LABEL } from "@/lib/format";
import type { PlayerProfile } from "@/lib/types";

import Avatar from "./Avatar";

export default function PlayerCard({ player }: { player: PlayerProfile }) {
  return (
    <Link
      href={`/players/${player.player_id.replace("#", "")}`}
      className="card card-interactive flex items-center gap-4 p-4"
    >
      <div className="relative shrink-0">
        <Avatar src={player.avatar} name={player.full_name} size={48} />
        {player.level ? (
          <span
            title={player.level.name}
            className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-surface text-[11px] shadow ring-1 ring-border"
          >
            {player.level.icon}
          </span>
        ) : null}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate font-semibold text-foreground">{player.full_name}</p>
          <span className="shrink-0 text-xs text-muted">{player.player_id}</span>
        </div>
        <p className="truncate text-sm text-muted">
          {POSITION_LABEL[player.position]}
          {player.city ? ` · ${player.city}` : ""}
          {player.current_team ? ` · ${player.current_team.name}` : ""}
        </p>
      </div>
      <div className="hidden shrink-0 gap-4 text-center sm:flex">
        <Stat label="Gol" value={player.goals_total} />
        <Stat label="Pas" value={player.assists_total} />
        <Stat label="O'yin" value={player.matches_total} />
      </div>
    </Link>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-sm font-bold text-navy">{value}</p>
      <p className="text-[11px] text-muted">{label}</p>
    </div>
  );
}

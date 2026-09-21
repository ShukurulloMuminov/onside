import Link from "next/link";

import type { Team } from "@/lib/types";

import Avatar from "./Avatar";

export default function TeamCard({ team }: { team: Team }) {
  return (
    <Link href={`/teams/${team.slug}`} className="card card-interactive flex items-center gap-4 p-4">
      <Avatar src={team.logo} name={team.name} size={48} rounded="md" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-foreground">{team.name}</p>
        <p className="truncate text-sm text-muted">
          {team.city} · {team.member_count} a&apos;zo
        </p>
      </div>
      <div className="hidden shrink-0 gap-4 text-center sm:flex">
        <Stat label="G'alaba" value={team.wins_total} />
        <Stat label="Turnir" value={team.tournaments_total} />
        <Stat label="Sovrin" value={team.trophies_total} />
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

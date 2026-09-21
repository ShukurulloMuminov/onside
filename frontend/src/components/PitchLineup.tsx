import { slotsFor, squadSizeForFormation } from "@/lib/formations";
import type { TeamLineupSlotData } from "@/lib/types";

import Avatar from "./Avatar";

export default function PitchLineup({
  formation,
  slots,
}: {
  formation: string;
  slots: TeamLineupSlotData[];
}) {
  const positions = slotsFor(squadSizeForFormation(formation), formation);
  const playerByCode = new Map(slots.map((s) => [s.code, s.player]));

  return (
    <div className="relative mx-auto aspect-[2/3] w-full max-w-sm overflow-hidden rounded-xl border border-border bg-win">
      <PitchMarkings />
      {positions.map((slot) => {
        const player = playerByCode.get(slot.code) ?? null;
        return (
          <div
            key={slot.code}
            className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
            style={{ left: `${slot.x}%`, top: `${slot.y}%` }}
          >
            {player ? (
              <>
                <Avatar src={player.avatar} name={player.full_name} size={36} />
                <span className="max-w-[72px] truncate rounded bg-black/40 px-1 text-[10px] font-medium leading-tight text-white">
                  {player.full_name.split(" ")[0]}
                </span>
              </>
            ) : (
              <>
                <div className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-dashed border-white/60 text-[10px] font-semibold text-white/80">
                  {slot.label}
                </div>
                <span className="text-[10px] text-white/60">bo&apos;sh</span>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PitchMarkings() {
  return (
    <svg viewBox="0 0 100 150" className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
      <rect x="0" y="0" width="100" height="150" fill="none" />
      <g stroke="rgba(255,255,255,0.5)" strokeWidth="0.6" fill="none">
        <rect x="3" y="3" width="94" height="144" />
        <line x1="3" y1="75" x2="97" y2="75" />
        <circle cx="50" cy="75" r="12" />
        <circle cx="50" cy="75" r="0.8" fill="rgba(255,255,255,0.5)" />
        {/* Top (opponent) penalty area */}
        <rect x="25" y="3" width="50" height="18" />
        <rect x="38" y="3" width="24" height="8" />
        <circle cx="50" cy="24" r="0.8" fill="rgba(255,255,255,0.5)" />
        {/* Bottom (own) penalty area */}
        <rect x="25" y="129" width="50" height="18" />
        <rect x="38" y="139" width="24" height="8" />
        <circle cx="50" cy="126" r="0.8" fill="rgba(255,255,255,0.5)" />
      </g>
    </svg>
  );
}

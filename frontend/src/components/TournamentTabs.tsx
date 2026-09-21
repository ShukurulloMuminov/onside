"use client";

import { useState } from "react";

import BracketView from "@/components/BracketView";
import MatchCard from "@/components/MatchCard";
import StandingsTable from "@/components/StandingsTable";
import type { Match, TournamentBracket, TournamentStandings } from "@/lib/types";

type Tab = "standings" | "bracket" | "matches";

export default function TournamentTabs({
  standings,
  bracket,
  matches,
}: {
  standings: TournamentStandings;
  bracket: TournamentBracket;
  matches: Match[];
}) {
  const availableTabs: { id: Tab; label: string; show: boolean }[] = [
    { id: "standings", label: "Jadval", show: standings.groups.length > 0 },
    { id: "bracket", label: "Playoff", show: bracket.rounds.length > 0 },
    { id: "matches", label: "O'yinlar", show: matches.length > 0 },
  ];
  const firstAvailable = availableTabs.find((t) => t.show)?.id ?? "matches";
  const [tab, setTab] = useState<Tab>(firstAvailable);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-1 border-b border-border">
        {availableTabs
          .filter((t) => t.show)
          .map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm font-medium ${
                tab === t.id ? "border-b-2 border-blue text-blue" : "text-muted hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
      </div>

      {tab === "standings" && (
        <div className="flex flex-col gap-6">
          {standings.groups.map((group) => (
            <div key={group.id} className="card p-4">
              <h3 className="mb-3 font-semibold text-foreground">Guruh {group.name}</h3>
              <StandingsTable rows={group.standings} />
            </div>
          ))}
        </div>
      )}

      {tab === "bracket" && <BracketView rounds={bracket.rounds} />}

      {tab === "matches" && (
        <div className="grid gap-3 sm:grid-cols-2">
          {matches.map((m) => (
            <MatchCard key={m.id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}

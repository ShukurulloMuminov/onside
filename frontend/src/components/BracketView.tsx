import Link from "next/link";

import type { KnockoutRoundBracket } from "@/lib/types";

import Avatar from "./Avatar";

const ROUND_LABEL: Record<string, string> = {
  round_of_16: "1/8 final",
  quarterfinal: "Chorak final",
  semifinal: "Yarim final",
  final: "Final",
  third_place: "3-o'rin uchun",
};

const ROUND_WIDTH = 232;
const CONNECTOR_WIDTH = 32;
const SLOT_HEIGHT = 96; // vertical space allocated per first-round match

/**
 * Renders a single-elimination bracket tree with connector lines between
 * rounds, not just a stack of columns. The alignment trick: position match
 * `i` of round `r` (0-indexed, `count(r)` matches in that round) at
 * vertical center `(i + 0.5) / count(r)` of a SHARED container height.
 * That formula is self-consistent across rounds — the center of round
 * r+1's match `i` naturally lands exactly halfway between round r's
 * matches `2i` and `2i+1` — so connector lines always meet cleanly
 * without any extra per-round offset math.
 */
export default function BracketView({ rounds }: { rounds: KnockoutRoundBracket[] }) {
  if (rounds.length === 0) {
    return <p className="text-sm text-muted">Playoff bosqichi hali shakllantirilmagan.</p>;
  }

  // The 3rd-place match doesn't feed into anything else in the tree — it's
  // fed by the two semifinal losers, off to the side. Rendering it inline
  // with the main rounds would draw a connector line from the Final,
  // falsely implying the Final feeds into it. Render it separately instead.
  const mainRounds = rounds.filter((r) => r.name !== "third_place");
  const thirdPlaceRound = rounds.find((r) => r.name === "third_place");

  const containerHeight = mainRounds[0].matches.length * SLOT_HEIGHT;

  return (
    <div className="overflow-x-auto pb-4">
      <div className="flex items-start gap-8">
        <div className="flex" style={{ height: containerHeight + 32 }}>
          {mainRounds.map((round, roundIndex) => (
            <div key={round.name} className="flex shrink-0" style={{ width: ROUND_WIDTH }}>
              <div className="flex w-full flex-col">
                <p className="mb-4 text-center text-xs font-semibold uppercase tracking-wide text-muted">
                  {ROUND_LABEL[round.name] ?? round.name}
                </p>
                <div className="relative flex-1">
                  {round.matches.map((match, i) => (
                    <div
                      key={match.id}
                      className="absolute w-full px-1"
                      style={{
                        top: `${((i + 0.5) / round.matches.length) * 100}%`,
                        transform: "translateY(-50%)",
                      }}
                    >
                      <MatchBox match={match} />
                    </div>
                  ))}
                </div>
              </div>
              {roundIndex < mainRounds.length - 1 ? (
                <div className="relative shrink-0" style={{ width: CONNECTOR_WIDTH, marginTop: 32 }}>
                  <Connectors count={round.matches.length} />
                </div>
              ) : null}
            </div>
          ))}
        </div>
        {thirdPlaceRound ? (
          <div className="shrink-0 pt-8" style={{ width: ROUND_WIDTH }}>
            <p className="mb-4 text-center text-xs font-semibold uppercase tracking-wide text-muted">
              {ROUND_LABEL[thirdPlaceRound.name] ?? thirdPlaceRound.name}
            </p>
            {thirdPlaceRound.matches.map((match) => (
              <MatchBox key={match.id} match={match} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Connectors({ count }: { count: number }) {
  const pairs = Math.floor(count / 2);
  return (
    <>
      {Array.from({ length: pairs }, (_, pairIndex) => {
        const topPct = ((2 * pairIndex + 0.5) / count) * 100;
        const bottomPct = ((2 * pairIndex + 1.5) / count) * 100;
        return (
          <div
            key={pairIndex}
            className="absolute right-0 border-t-2 border-r-2 border-b-2 border-border"
            style={{ top: `${topPct}%`, height: `${bottomPct - topPct}%`, width: "100%" }}
          />
        );
      })}
    </>
  );
}

function MatchBox({ match }: { match: KnockoutRoundBracket["matches"][number] }) {
  return (
    <Link href={`/matches/${match.id}`} className="card flex flex-col gap-1 p-2.5">
      <BracketTeamRow
        name={match.home_team?.name ?? "TBD"}
        logo={match.home_team?.logo}
        score={match.home_score}
        winner={match.status === "finished" && (match.home_score ?? 0) > (match.away_score ?? 0)}
      />
      <BracketTeamRow
        name={match.away_team?.name ?? "TBD"}
        logo={match.away_team?.logo}
        score={match.away_score}
        winner={match.status === "finished" && (match.away_score ?? 0) > (match.home_score ?? 0)}
      />
    </Link>
  );
}

function BracketTeamRow({
  name,
  logo,
  score,
  winner,
}: {
  name: string;
  logo?: string | null;
  score: number | null;
  winner: boolean;
}) {
  return (
    <div className={`flex items-center justify-between gap-2 rounded px-1.5 py-1 ${winner ? "bg-blue-light" : ""}`}>
      <div className="flex min-w-0 items-center gap-2">
        <Avatar src={logo} name={name} size={20} rounded="md" />
        <span className={`truncate text-sm ${winner ? "font-semibold text-navy" : "text-foreground"}`}>
          {name}
        </span>
      </div>
      <span className={`text-sm ${winner ? "font-bold text-navy" : "text-muted"}`}>{score ?? "-"}</span>
    </div>
  );
}

import Link from "next/link";

import MatchCard from "@/components/MatchCard";
import TournamentCard from "@/components/TournamentCard";
import { apiGetOrNull } from "@/lib/api";
import type { Match, Paginated, PlayerProfile, RankingRow, Team, Tournament } from "@/lib/types";

export default async function HomePage() {
  const [tournaments, matches, rankings, playerCount, teamCount, tournamentCount] = await Promise.all([
    apiGetOrNull<Paginated<Tournament>>("/tournaments/?status=in_progress&ordering=-start_date"),
    apiGetOrNull<Paginated<Match>>("/matches/?status=finished&ordering=-scheduled_date"),
    apiGetOrNull<RankingRow[]>("/rankings/players/?scope=global&limit=5"),
    apiGetOrNull<Paginated<PlayerProfile>>("/players/?page_size=1"),
    apiGetOrNull<Paginated<Team>>("/teams/?page_size=1"),
    apiGetOrNull<Paginated<Tournament>>("/tournaments/?page_size=1"),
  ]);

  const stats = [
    { label: "Futbolchi", value: playerCount?.count ?? 0 },
    { label: "Jamoa", value: teamCount?.count ?? 0 },
    { label: "Turnir", value: tournamentCount?.count ?? 0 },
    { label: "Yakunlangan o'yin", value: matches?.count ?? 0 },
  ];

  return (
    <div className="flex flex-col gap-14">
      <section className="hero-pattern flex flex-col items-start gap-6 rounded-2xl p-10 text-white sm:p-14">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent ring-1 ring-inset ring-white/15">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          Havaskor futbol platformasi
        </span>
        <h1 className="max-w-2xl text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl">
          Futbolchi <span className="text-accent">&rarr;</span> jamoa <span className="text-accent">&rarr;</span>{" "}
          turnir <span className="text-accent">&rarr;</span> statistika <span className="text-accent">&rarr;</span>{" "}
          reyting
        </h1>
        <p className="max-w-xl text-base text-white/75 sm:text-lg">
          OnSide.uz — o&apos;z profilingizni yarating, jamoa tuzing, turnirlarda qatnashing va har bir
          o&apos;yiningiz statistikaga aylansin.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/register" className="btn-primary px-6 py-3">
            Ro&apos;yxatdan o&apos;tish
          </Link>
          <Link
            href="/tournaments"
            className="inline-flex items-center justify-center rounded-full border border-white/25 px-6 py-3 font-semibold text-white transition hover:border-white/50 hover:bg-white/10"
          >
            Turnirlarni ko&apos;rish
          </Link>
        </div>

        <div className="mt-2 grid w-full grid-cols-2 gap-4 border-t border-white/10 pt-6 sm:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label}>
              <p className="text-2xl font-extrabold tracking-tight sm:text-3xl">{s.value}</p>
              <p className="text-xs text-white/60 sm:text-sm">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <Section title="Faol turnirlar" href="/tournaments">
        {tournaments && tournaments.results.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tournaments.results.slice(0, 3).map((t) => (
              <TournamentCard key={t.id} tournament={t} />
            ))}
          </div>
        ) : (
          <EmptyState text="Hozircha faol turnirlar yo'q." />
        )}
      </Section>

      <div className="grid gap-10 lg:grid-cols-2">
        <Section title="So'nggi natijalar" href="/rankings">
          {matches && matches.results.length > 0 ? (
            <div className="flex flex-col gap-3">
              {matches.results.slice(0, 4).map((m) => (
                <MatchCard key={m.id} match={m} />
              ))}
            </div>
          ) : (
            <EmptyState text="Hali yakunlangan o'yinlar yo'q." />
          )}
        </Section>

        <Section title="Top futbolchilar" href="/rankings">
          {rankings && rankings.length > 0 ? (
            <ol className="card divide-y divide-border overflow-hidden">
              {rankings.map((row, i) => (
                <li key={row.player.id} className="flex items-center gap-3 px-4 py-3 transition hover:bg-blue-light/40">
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      i === 0
                        ? "bg-draw/15 text-draw"
                        : i === 1
                          ? "bg-muted/15 text-muted"
                          : i === 2
                            ? "bg-loss/10 text-loss"
                            : "text-muted"
                    }`}
                  >
                    {i + 1}
                  </span>
                  <Link href={`/players/${row.player.player_id.replace("#", "")}`} className="flex-1 truncate font-medium hover:text-blue">
                    {row.player.full_name}
                  </Link>
                  <span className="text-sm font-semibold text-navy">{row.goals} gol</span>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState text="Reyting hali shakllanmagan." />
          )}
        </Section>
      </div>
    </div>
  );
}

function Section({ title, href, children }: { title: string; href: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-extrabold tracking-tight text-foreground">{title}</h2>
        <Link href={href} className="text-sm font-semibold text-blue hover:text-blue-dark">
          Barchasi &rarr;
        </Link>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="card p-6 text-center text-sm text-muted">{text}</div>;
}

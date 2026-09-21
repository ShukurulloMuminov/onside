import Link from "next/link";
import { redirect } from "next/navigation";

import AwardBadgePanel from "@/components/AwardBadgePanel";
import InvitationsList from "@/components/InvitationsList";
import { apiGetOrNull } from "@/lib/api";
import { apiGetAuthed, getCurrentUser } from "@/lib/session";
import type { Badge, Paginated, PlayerProfile, TeamInvitation, Tournament } from "@/lib/types";

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const [profile, invitations] = await Promise.all([
    apiGetOrNull<Paginated<PlayerProfile>>(`/players/?search=${encodeURIComponent(user.username)}`),
    apiGetAuthed<Paginated<TeamInvitation>>("/teams/invitations/"),
  ]);
  const pendingInvitations = (invitations?.results ?? []).filter((inv) => inv.status === "pending");
  const myProfile = profile?.results.find((p) => p.username === user.username) ?? null;

  const myTournaments =
    user.role === "tournament_admin" || user.role === "super_admin"
      ? await apiGetAuthed<Tournament[]>("/tournaments/mine/")
      : null;

  const badges =
    user.role === "super_admin" ? await apiGetOrNull<Paginated<Badge>>("/badges/?page_size=100") : null;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Xush kelibsiz, {user.first_name || user.username}
        </h1>
        <p className="text-sm text-muted">
          {myProfile ? (
            <Link href={`/players/${myProfile.player_id.replace("#", "")}`} className="text-blue hover:text-blue-dark">
              Profilingizni ko&apos;rish ({myProfile.player_id})
            </Link>
          ) : null}
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold text-foreground">Jamoa takliflari</h2>
        <InvitationsList initial={pendingInvitations} />
      </section>

      {myTournaments ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-foreground">Boshqarayotgan turnirlaringiz</h2>
          {myTournaments.length === 0 ? (
            <p className="card p-6 text-center text-sm text-muted">Hozircha turnir tayinlanmagan.</p>
          ) : (
            <div className="grid gap-3">
              {myTournaments.map((t) => (
                <Link key={t.id} href={`/tournaments/${t.slug}`} className="card flex items-center justify-between p-4 hover:border-blue">
                  <div>
                    <p className="font-semibold text-foreground">{t.name}</p>
                    <p className="text-sm text-muted">{t.city} · {t.team_count}/{t.max_teams} jamoa</p>
                  </div>
                  <span className="text-sm font-medium text-blue">Boshqarish &rarr;</span>
                </Link>
              ))}
            </div>
          )}
        </section>
      ) : null}

      {user.role === "super_admin" ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-foreground">Super Admin</h2>
          <div className="card flex flex-col gap-2 p-6">
            <p className="text-sm text-muted">
              Foydalanuvchilar, yangi badge&apos;lar, level&apos;lar, reklamalar va boshqa chuqur sozlamalar
              uchun Django admin panelidan foydalaning.
            </p>
            <a
              href={`${process.env.NEXT_PUBLIC_DJANGO_ORIGIN ?? "http://127.0.0.1:8010"}/admin/`}
              target="_blank"
              rel="noreferrer"
              className="w-fit rounded-full bg-navy px-5 py-2 text-sm font-semibold text-white hover:opacity-90"
            >
              Django admin&apos;ni ochish
            </a>
          </div>
          {badges && badges.results.length > 0 ? <AwardBadgePanel badges={badges.results} /> : null}
        </section>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold text-foreground">Tezkor havolalar</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <QuickLink href="/teams/new" label="Yangi jamoa yaratish" />
          <QuickLink href="/teams" label="Jamoalarni qidirish" />
          <QuickLink href="/tournaments" label="Turnirlarni ko'rish" />
          <QuickLink href="/rankings" label="Reytingni ko'rish" />
        </div>
      </section>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="card p-4 text-sm font-medium text-foreground hover:border-blue hover:text-blue">
      {label}
    </Link>
  );
}

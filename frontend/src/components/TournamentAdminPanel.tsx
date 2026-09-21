"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import Avatar from "@/components/Avatar";
import Badge from "@/components/Badge";
import { ApiError, clientApi } from "@/lib/clientApi";
import type { Tournament, TournamentRegistration } from "@/lib/types";

const STATUS_TONE = {
  pending: "draw",
  approved: "win",
  rejected: "loss",
  withdrawn: "neutral",
} as const;

export default function TournamentAdminPanel({
  tournament,
  registrations,
  hasGroups,
  hasBracket,
}: {
  tournament: Tournament;
  registrations: TournamentRegistration[];
  hasGroups: boolean;
  hasBracket: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function review(id: number, approve: boolean) {
    setBusy(`review-${id}`);
    setError(null);
    try {
      await clientApi.post(`/tournaments/${tournament.slug}/registrations/${id}/${approve ? "approve" : "reject"}`);
      router.refresh();
    } catch {
      setError("Amalni bajarib bo'lmadi.");
    } finally {
      setBusy(null);
    }
  }

  async function generateGroups() {
    setBusy("groups");
    setError(null);
    try {
      await clientApi.post(`/tournaments/${tournament.slug}/generate-groups`);
      router.refresh();
    } catch (err) {
      setError(errorMessage(err, "Guruhlarni yaratib bo'lmadi."));
    } finally {
      setBusy(null);
    }
  }

  async function generateKnockout() {
    setBusy("knockout");
    setError(null);
    try {
      await clientApi.post(`/tournaments/${tournament.slug}/generate-knockout`);
      router.refresh();
    } catch (err) {
      setError(errorMessage(err, "Playoffni yaratib bo'lmadi."));
    } finally {
      setBusy(null);
    }
  }

  const pending = registrations.filter((r) => r.status === "pending");
  const approvedCount = registrations.filter((r) => r.status === "approved").length;
  const teamsNeededForGroups = tournament.groups_count * 2;
  const notEnoughForGroups = tournament.groups_count < 1 || approvedCount < teamsNeededForGroups;

  return (
    <div className="card flex flex-col gap-4 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold text-foreground">Turnir boshqaruvi</h2>
        <div className="flex flex-wrap gap-2">
          {!hasGroups ? (
            <button
              onClick={generateGroups}
              disabled={busy === "groups" || notEnoughForGroups}
              title={
                notEnoughForGroups
                  ? `Kamida ${teamsNeededForGroups} ta tasdiqlangan jamoa kerak (hozir ${approvedCount} ta). Turnir sozlamalaridan guruhlar sonini o'zgartiring.`
                  : undefined
              }
              className="rounded-full bg-navy px-4 py-1.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              Guruhlarni yaratish
            </button>
          ) : !hasBracket ? (
            <button
              onClick={generateKnockout}
              disabled={busy === "knockout"}
              className="rounded-full bg-navy px-4 py-1.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              Playoffni yaratish
            </button>
          ) : null}
        </div>
      </div>

      {!hasGroups && notEnoughForGroups ? (
        <p className="text-sm text-draw">
          Guruhlarni yaratish uchun kamida <strong>{teamsNeededForGroups}</strong> ta tasdiqlangan jamoa kerak
          (hozir <strong>{approvedCount}</strong> ta). Kerak bo&apos;lsa, quyidagi &quot;Turnir
          sozlamalari&quot;dan guruhlar sonini kamaytiring.
        </p>
      ) : null}

      {error ? <p className="text-sm text-loss">{error}</p> : null}

      {pending.length === 0 ? (
        <p className="text-sm text-muted">Ko&apos;rib chiqilishi kerak bo&apos;lgan arizalar yo&apos;q.</p>
      ) : (
        <div className="flex flex-col divide-y divide-border">
          {pending.map((reg) => (
            <div key={reg.id} className="flex items-center justify-between gap-3 py-3">
              <div className="flex items-center gap-3">
                <Avatar src={reg.team.logo} name={reg.team.name} size={32} rounded="md" />
                <div>
                  <p className="text-sm font-medium text-foreground">{reg.team.name}</p>
                  <Badge tone={STATUS_TONE[reg.status]}>{reg.status}</Badge>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => review(reg.id, true)}
                  disabled={busy === `review-${reg.id}`}
                  className="rounded-full bg-win px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                >
                  Tasdiqlash
                </button>
                <button
                  onClick={() => review(reg.id, false)}
                  disabled={busy === `review-${reg.id}`}
                  className="rounded-full bg-loss px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                >
                  Rad etish
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function errorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.data) {
    const first = Object.values(err.data as Record<string, unknown>)[0];
    return Array.isArray(first) ? String(first[0]) : fallback;
  }
  return fallback;
}

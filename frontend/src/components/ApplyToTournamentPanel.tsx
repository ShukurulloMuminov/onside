"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, clientApi } from "@/lib/clientApi";

export default function ApplyToTournamentPanel({ tournamentSlug }: { tournamentSlug: string }) {
  const router = useRouter();
  const [teamSlug, setTeamSlug] = useState("");
  const [status, setStatus] = useState<{ type: "ok" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      await clientApi.post(`/tournaments/${tournamentSlug}/register`, { team_slug: teamSlug });
      setStatus({ type: "ok", message: "Ariza yuborildi. Turnir admini ko'rib chiqadi." });
      setTeamSlug("");
      router.refresh();
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const firstError = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setStatus({
        type: "error",
        message: Array.isArray(firstError) ? String(firstError[0]) : "Ariza yuborishda xatolik yuz berdi.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card flex flex-col gap-3 p-6">
      <h2 className="font-semibold text-foreground">Turnirga ariza berish</h2>
      <p className="text-sm text-muted">Faqat jamoa sardori ariza bera oladi. Jamoangiz slug&apos;ini kiriting.</p>
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 min-w-[200px] flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Jamoa (slug)</span>
          <input required className="input" placeholder="masalan: qarshi-fc" value={teamSlug} onChange={(e) => setTeamSlug(e.target.value)} />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
        >
          {loading ? "Yuborilmoqda..." : "Ariza berish"}
        </button>
      </form>
      {status ? <p className={`text-sm ${status.type === "ok" ? "text-win" : "text-loss"}`}>{status.message}</p> : null}
    </div>
  );
}

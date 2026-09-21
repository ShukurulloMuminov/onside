"use client";

import { FormEvent, useState } from "react";

import { ApiError, clientApi } from "@/lib/clientApi";
import type { Badge } from "@/lib/types";

export default function AwardBadgePanel({ badges }: { badges: Badge[] }) {
  const [playerId, setPlayerId] = useState("");
  const [badgeId, setBadgeId] = useState<number | string>(badges[0]?.id ?? "");
  const [status, setStatus] = useState<{ type: "ok" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      await clientApi.post(`/badges/${badgeId}/award`, { player_id: playerId });
      const badgeName = badges.find((b) => b.id === Number(badgeId))?.name ?? "";
      setStatus({ type: "ok", message: `"${badgeName}" nishoni #${playerId.replace("#", "")} o'yinchisiga berildi.` });
      setPlayerId("");
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const firstError = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setStatus({
        type: "error",
        message: Array.isArray(firstError) ? String(firstError[0]) : "Nishon berishda xatolik yuz berdi.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-3 p-6">
      <h3 className="font-semibold text-foreground">O&apos;yinchiga nishon (badge) berish</h3>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 min-w-[140px] flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Player ID</span>
          <input required className="input" placeholder="#1024" value={playerId} onChange={(e) => setPlayerId(e.target.value)} />
        </label>
        <label className="flex flex-1 min-w-[180px] flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Nishon</span>
          <select className="input" value={badgeId} onChange={(e) => setBadgeId(e.target.value)}>
            {badges.map((b) => (
              <option key={b.id} value={b.id}>
                {b.icon} {b.name}
              </option>
            ))}
          </select>
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
        >
          {loading ? "Berilmoqda..." : "Berish"}
        </button>
      </div>
      {status ? <p className={`text-sm ${status.type === "ok" ? "text-win" : "text-loss"}`}>{status.message}</p> : null}
    </form>
  );
}

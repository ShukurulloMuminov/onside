"use client";

import { FormEvent, useState } from "react";

import { ApiError, clientApi } from "@/lib/clientApi";
import type { Team } from "@/lib/types";

export default function TeamManagePanel({ team }: { team: Team }) {
  const [playerId, setPlayerId] = useState("");
  const [status, setStatus] = useState<{ type: "ok" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleInvite(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      await clientApi.post(`/teams/${team.slug}/invite`, { player_id: playerId });
      setStatus({ type: "ok", message: `Taklif #${playerId.replace("#", "")} raqamli o'yinchiga yuborildi.` });
      setPlayerId("");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? (Object.values(err.data as Record<string, unknown>)[0] as string) ?? "Xatolik yuz berdi."
          : "Xatolik yuz berdi.";
      setStatus({ type: "error", message: Array.isArray(message) ? message[0] : String(message) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card flex flex-col gap-3 p-6">
      <h2 className="font-semibold text-foreground">Jamoa boshqaruvi</h2>
      <p className="text-sm text-muted">O&apos;yinchining Player ID raqami orqali jamoaga taklif yuboring.</p>
      <form onSubmit={handleInvite} className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 min-w-[160px] flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Player ID</span>
          <input
            required
            className="input"
            placeholder="#1024"
            value={playerId}
            onChange={(e) => setPlayerId(e.target.value)}
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
        >
          {loading ? "Yuborilmoqda..." : "Taklif yuborish"}
        </button>
      </form>
      {status ? (
        <p className={`text-sm ${status.type === "ok" ? "text-win" : "text-loss"}`}>{status.message}</p>
      ) : null}
    </div>
  );
}

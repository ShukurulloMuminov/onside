"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, clientApi } from "@/lib/clientApi";
import type { Match } from "@/lib/types";

export default function MatchConfirmPanel({ match }: { match: Match }) {
  const router = useRouter();
  const [saving, setSaving] = useState<"confirm" | "dispute" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function act(action: "confirm" | "dispute") {
    setSaving(action);
    setError(null);
    try {
      await clientApi.post(`/matches/${match.id}/${action}`);
      router.refresh();
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const detail = data && typeof data === "object" ? (data as Record<string, unknown>).detail : null;
      setError(typeof detail === "string" ? detail : "Amalni bajarib bo'lmadi.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="card flex flex-col gap-3 p-6">
      <h2 className="font-semibold text-foreground">Natijani tasdiqlash</h2>
      <p className="text-sm text-muted">
        Hakam/administrator natijani kiritdi:{" "}
        <strong className="text-foreground">
          {match.home_score} : {match.away_score}
        </strong>
        . Rozi bo&apos;lsangiz tasdiqlang — bitta sardor tasdiqlashi kifoya. Noto&apos;g&apos;ri deb hisoblasangiz,
        rad eting — natija administratorga qaytariladi.
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => act("confirm")}
          disabled={saving !== null}
          className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
        >
          {saving === "confirm" ? "Yuborilmoqda..." : "Tasdiqlayman"}
        </button>
        <button
          onClick={() => act("dispute")}
          disabled={saving !== null}
          className="w-fit rounded-full border border-border px-5 py-2 text-sm font-semibold text-foreground hover:bg-surface disabled:opacity-50"
        >
          {saving === "dispute" ? "Yuborilmoqda..." : "Rad etaman"}
        </button>
      </div>
      {error ? <p className="text-sm text-loss">{error}</p> : null}
    </div>
  );
}

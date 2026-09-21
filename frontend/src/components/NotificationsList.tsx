"use client";

import Link from "next/link";
import { useState } from "react";

import { clientApi } from "@/lib/clientApi";
import type { AppNotification, NotificationType } from "@/lib/types";

const TYPE_ICON: Record<NotificationType, string> = {
  team_invite: "👥",
  registration_approved: "✅",
  registration_rejected: "🚫",
  tournament_started: "🏁",
  badge_earned: "🏅",
  level_up: "⬆️",
  match_result: "⚽",
  match_disputed: "⚠️",
};

export default function NotificationsList({ initial }: { initial: AppNotification[] }) {
  const [items, setItems] = useState(initial);
  const [busy, setBusy] = useState(false);

  const unreadCount = items.filter((n) => !n.is_read).length;

  async function markRead(notification: AppNotification) {
    if (notification.is_read) return;
    setItems((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)));
    try {
      await clientApi.post(`/notifications/${notification.id}/mark-read`);
    } catch {
      // best-effort — a stale read state self-corrects on the next page load
    }
  }

  async function markAllRead() {
    setBusy(true);
    try {
      await clientApi.post("/notifications/mark-all-read");
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } finally {
      setBusy(false);
    }
  }

  if (items.length === 0) {
    return <p className="card p-6 text-center text-sm text-muted">Hozircha bildirishnomalar yo&apos;q.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {unreadCount > 0 ? (
        <button
          onClick={markAllRead}
          disabled={busy}
          className="w-fit self-end rounded-full border border-border px-4 py-1.5 text-xs font-medium text-foreground hover:bg-surface disabled:opacity-50"
        >
          Hammasini o&apos;qilgan deb belgilash
        </button>
      ) : null}
      <div className="card divide-y divide-border">
        {items.map((n) => (
          <Link
            key={n.id}
            href={n.link || "#"}
            onClick={() => markRead(n)}
            className={`flex items-start gap-3 p-4 text-sm transition hover:bg-surface ${n.is_read ? "" : "bg-blue-light/40"}`}
          >
            <span className="text-lg leading-none">{TYPE_ICON[n.type] ?? "🔔"}</span>
            <div className="flex-1">
              <p className={n.is_read ? "text-foreground" : "font-semibold text-foreground"}>{n.message}</p>
              <p className="mt-1 text-xs text-muted">{new Date(n.created_at).toLocaleString("uz-UZ")}</p>
            </div>
            {!n.is_read ? <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue" /> : null}
          </Link>
        ))}
      </div>
    </div>
  );
}

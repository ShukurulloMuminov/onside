"use client";

import { useState } from "react";

import Avatar from "@/components/Avatar";
import { clientApi } from "@/lib/clientApi";
import type { TeamInvitation } from "@/lib/types";

export default function InvitationsList({ initial }: { initial: TeamInvitation[] }) {
  const [invitations, setInvitations] = useState(initial);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function respond(id: number, accept: boolean) {
    setBusyId(id);
    try {
      await clientApi.post(`/teams/invitations/${id}/${accept ? "accept" : "reject"}`);
      setInvitations((prev) => prev.filter((inv) => inv.id !== id));
    } finally {
      setBusyId(null);
    }
  }

  if (invitations.length === 0) {
    return <p className="card p-6 text-center text-sm text-muted">Yangi takliflar yo&apos;q.</p>;
  }

  return (
    <div className="card divide-y divide-border">
      {invitations.map((inv) => (
        <div key={inv.id} className="flex items-center justify-between gap-3 p-4">
          <div className="flex items-center gap-3">
            <Avatar src={inv.team.logo} name={inv.team.name} size={36} rounded="md" />
            <div>
              <p className="text-sm font-medium text-foreground">{inv.team.name}</p>
              <p className="text-xs text-muted">Jamoaga taklif qilindingiz</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => respond(inv.id, true)}
              disabled={busyId === inv.id}
              className="rounded-full bg-win px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              Qabul qilish
            </button>
            <button
              onClick={() => respond(inv.id, false)}
              disabled={busyId === inv.id}
              className="rounded-full bg-loss px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              Rad etish
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

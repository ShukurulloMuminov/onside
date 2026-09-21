"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import PitchLineup from "@/components/PitchLineup";
import { ApiError, clientApi } from "@/lib/clientApi";
import { DEFAULT_FORMATION_BY_SIZE, formationNames, slotsFor, type SquadSize } from "@/lib/formations";
import type { TeamLineup, TeamMembership } from "@/lib/types";

export default function TeamLineupEditForm({
  teamSlug,
  squadSize,
  members,
  initialLineup,
}: {
  teamSlug: string;
  squadSize: SquadSize;
  members: TeamMembership[];
  initialLineup: TeamLineup | null;
}) {
  const router = useRouter();
  const availableFormations = formationNames(squadSize);
  const initialFormationValid = initialLineup && availableFormations.includes(initialLineup.formation);

  const [formation, setFormation] = useState<string>(
    initialFormationValid ? initialLineup!.formation : DEFAULT_FORMATION_BY_SIZE[squadSize]
  );
  const [assignments, setAssignments] = useState<Record<string, number | null>>(() => {
    if (!initialFormationValid) return {};
    const initial: Record<string, number | null> = {};
    for (const slot of initialLineup!.slots) {
      if (slot.player) initial[slot.code] = slot.player.id;
    }
    return initial;
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const memberById = useMemo(() => new Map(members.map((m) => [m.player.id, m.player])), [members]);
  const currentSlots = slotsFor(squadSize, formation);

  const previewSlots = currentSlots.map((slot) => ({
    code: slot.code,
    player: assignments[slot.code] ? memberById.get(assignments[slot.code]!) ?? null : null,
  }));

  function handleFormationChange(next: string) {
    setFormation(next);
    setAssignments({});
    setSaved(false);
  }

  function handleSlotChange(code: string, playerId: string) {
    setAssignments((prev) => ({ ...prev, [code]: playerId ? Number(playerId) : null }));
    setSaved(false);
  }

  const usedElsewhere = (code: string) =>
    new Set(Object.entries(assignments).filter(([c, v]) => c !== code && v != null).map(([, v]) => v));

  async function handleSubmit() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, number> = {};
      for (const [code, playerId] of Object.entries(assignments)) {
        if (playerId != null) payload[code] = playerId;
      }
      await clientApi.patch(`/teams/${teamSlug}/lineup`, { formation, assignments: payload });
      setSaved(true);
      router.refresh();
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const firstError = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setError(Array.isArray(firstError) ? String(firstError[0]) : "Tarkibni saqlashda xatolik yuz berdi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card grid gap-6 p-6 md:grid-cols-[minmax(0,280px)_1fr]">
      <PitchLineup formation={formation} slots={previewSlots} />

      <div className="flex flex-col gap-4">
        <div>
          <h2 className="font-semibold text-foreground">Asosiy tarkibni belgilash</h2>
          <p className="text-sm text-muted">
            {squadSize}x{squadSize} jamoa uchun formatsiyani tanlang va har bir o&apos;ringa jamoadoshingizni
            tayinlang.
          </p>
        </div>

        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Formatsiya</span>
          <select className="input w-40" value={formation} onChange={(e) => handleFormationChange(e.target.value)}>
            {availableFormations.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {currentSlots.map((slot) => {
            const taken = usedElsewhere(slot.code);
            return (
              <label key={slot.code} className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-muted">{slot.label}</span>
                <select
                  className="input"
                  value={assignments[slot.code] ?? ""}
                  onChange={(e) => handleSlotChange(slot.code, e.target.value)}
                >
                  <option value="">Bo&apos;sh</option>
                  {members.map((m) => (
                    <option key={m.player.id} value={m.player.id} disabled={taken.has(m.player.id)}>
                      {m.player.full_name}
                    </option>
                  ))}
                </select>
              </label>
            );
          })}
        </div>

        {error ? <p className="text-sm text-loss">{error}</p> : null}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
          >
            {saving ? "Saqlanmoqda..." : "Tarkibni saqlash"}
          </button>
          {saved ? <span className="text-sm text-win">Saqlandi</span> : null}
        </div>
      </div>
    </div>
  );
}

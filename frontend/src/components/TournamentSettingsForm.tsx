"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import ImageInput from "@/components/ImageInput";
import { clientApi } from "@/lib/clientApi";
import { TOURNAMENT_STATUS_LABEL } from "@/lib/format";
import type { Tournament, TournamentStatus } from "@/lib/types";

const STATUSES: TournamentStatus[] = [
  "draft",
  "pending_approval",
  "published",
  "registration_open",
  "registration_closed",
  "in_progress",
  "finished",
  "cancelled",
];

export default function TournamentSettingsForm({ tournament }: { tournament: Tournament }) {
  const router = useRouter();
  const [form, setForm] = useState({
    name: tournament.name,
    description: tournament.description,
    organizer: tournament.organizer,
    city: tournament.city,
    venue: tournament.venue,
    start_date: tournament.start_date ?? "",
    end_date: tournament.end_date ?? "",
    status: tournament.status,
    max_teams: tournament.max_teams,
    prize_info: tournament.prize_info,
    groups_count: tournament.groups_count,
    teams_per_group: tournament.teams_per_group,
    qualifiers_per_group: tournament.qualifiers_per_group,
    require_match_confirmation: tournament.require_match_confirmation,
  });
  const [banner, setBanner] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setSaved(false);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    const formData = new FormData();
    for (const [key, value] of Object.entries(form)) {
      formData.set(key, String(value));
    }
    if (banner) formData.set("banner", banner);

    await clientApi.patch(`/tournaments/${tournament.slug}`, formData);
    setSaving(false);
    setSaved(true);
    router.refresh();
  }

  const teamsNeededForGroups = form.groups_count * 2;

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Turnir sozlamalari</h2>
      <ImageInput label="Banner" name="banner" currentUrl={tournament.banner} fallbackName={tournament.name} rounded="md" onChange={setBanner} />

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Nomi</span>
          <input required className="input" value={form.name} onChange={(e) => update("name", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Holat</span>
          <select className="input" value={form.status} onChange={(e) => update("status", e.target.value as TournamentStatus)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {TOURNAMENT_STATUS_LABEL[s]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Shahar</span>
          <input className="input" value={form.city} onChange={(e) => update("city", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Maydon</span>
          <input className="input" value={form.venue} onChange={(e) => update("venue", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Boshlanish sanasi</span>
          <input type="date" className="input" value={form.start_date} onChange={(e) => update("start_date", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Tugash sanasi</span>
          <input type="date" className="input" value={form.end_date} onChange={(e) => update("end_date", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Tashkilotchi</span>
          <input className="input" value={form.organizer} onChange={(e) => update("organizer", e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Mukofot</span>
          <input className="input" value={form.prize_info} onChange={(e) => update("prize_info", e.target.value)} />
        </label>
      </div>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium text-foreground">Tavsif</span>
        <textarea className="input" rows={3} value={form.description} onChange={(e) => update("description", e.target.value)} />
      </label>

      <div className="rounded-lg border border-border p-4">
        <p className="mb-3 text-sm font-medium text-foreground">Guruh bosqichi sozlamalari</p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-muted">Max jamoa</span>
            <input
              type="number"
              min={2}
              className="input"
              value={form.max_teams}
              onChange={(e) => update("max_teams", Number(e.target.value))}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-muted">Guruhlar soni</span>
            <input
              type="number"
              min={1}
              className="input"
              value={form.groups_count}
              onChange={(e) => update("groups_count", Number(e.target.value))}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-muted">Guruhda jamoa</span>
            <input
              type="number"
              min={2}
              className="input"
              value={form.teams_per_group}
              onChange={(e) => update("teams_per_group", Number(e.target.value))}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-muted">O&apos;tadigan soni</span>
            <input
              type="number"
              min={1}
              className="input"
              value={form.qualifiers_per_group}
              onChange={(e) => update("qualifiers_per_group", Number(e.target.value))}
            />
          </label>
        </div>
        {form.groups_count > 0 ? (
          <p className="mt-3 text-xs text-muted">
            Guruhlarni yaratish uchun kamida <strong>{teamsNeededForGroups}</strong> ta tasdiqlangan jamoa kerak
            bo&apos;ladi ({form.groups_count} guruh &times; 2). Jamoalar guruhlarga <strong>tasodifiy</strong>{" "}
            taqsimlanadi.
          </p>
        ) : null}
      </div>

      <label className="flex items-start gap-3 rounded-lg border border-border p-4 text-sm">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={form.require_match_confirmation}
          onChange={(e) => update("require_match_confirmation", e.target.checked)}
        />
        <span>
          <span className="block font-medium text-foreground">Natijani sardorlar tasdiqlashi shart</span>
          <span className="block text-muted">
            Yoqilsa, administrator kiritgan natija ikkala jamoa sardori tasdiqlaguncha &quot;kutilmoqda&quot;
            holatida turadi. Administrator istalgan vaqtda majburan yakunlashi mumkin.
          </span>
        </span>
      </label>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={saving}
          className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
        >
          {saving ? "Saqlanmoqda..." : "Saqlash"}
        </button>
        {saved ? <span className="text-sm text-win">Saqlandi</span> : null}
      </div>
    </form>
  );
}

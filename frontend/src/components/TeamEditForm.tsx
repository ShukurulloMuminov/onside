"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import ImageInput from "@/components/ImageInput";
import { clientApi } from "@/lib/clientApi";
import { SQUAD_SIZES } from "@/lib/formations";
import type { Team } from "@/lib/types";

export default function TeamEditForm({ team }: { team: Team }) {
  const router = useRouter();
  const [city, setCity] = useState(team.city);
  const [description, setDescription] = useState(team.description);
  const [squadSize, setSquadSize] = useState(team.squad_size);
  const [logo, setLogo] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    const formData = new FormData();
    formData.set("city", city);
    formData.set("description", description);
    formData.set("squad_size", String(squadSize));
    if (logo) formData.set("logo", logo);

    await clientApi.patch(`/teams/${team.slug}`, formData);
    setSaving(false);
    setSaved(true);
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Jamoa ma&apos;lumotlarini tahrirlash</h2>
      <ImageInput label="Logotip" name="logo" currentUrl={team.logo} fallbackName={team.name} rounded="md" onChange={setLogo} />
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Shahar</span>
          <input className="input" value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">O&apos;yinchilar soni</span>
          <select
            className="input"
            value={squadSize}
            onChange={(e) => setSquadSize(Number(e.target.value) as Team["squad_size"])}
          >
            {SQUAD_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}x{s}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium text-foreground">Tavsif</span>
        <textarea className="input" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      {squadSize !== team.squad_size ? (
        <p className="text-sm text-draw">
          O&apos;yinchilar sonini o&apos;zgartirsangiz, asosiy tarkibni yangi formatsiyaga moslab qayta
          belgilashingiz kerak bo&apos;ladi.
        </p>
      ) : null}
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

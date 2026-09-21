"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import ImageInput from "@/components/ImageInput";
import { clientApi } from "@/lib/clientApi";
import { POSITION_LABEL } from "@/lib/format";
import type { PlayerProfile, Position } from "@/lib/types";

const POSITIONS: Position[] = ["GK", "DF", "MF", "FW"];

export default function EditProfileForm({ player }: { player: PlayerProfile }) {
  const router = useRouter();
  const [city, setCity] = useState(player.city);
  const [position, setPosition] = useState<Position | "">(player.position);
  const [bio, setBio] = useState(player.bio);
  const [avatar, setAvatar] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    const formData = new FormData();
    formData.set("city", city);
    formData.set("position", position);
    formData.set("bio", bio);
    if (avatar) formData.set("avatar", avatar);

    await clientApi.patch(`/players/${player.player_id.replace("#", "")}`, formData);
    setSaving(false);
    setSaved(true);
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Profilni tahrirlash</h2>
      <ImageInput
        label="Avatar"
        name="avatar"
        currentUrl={player.avatar}
        fallbackName={player.full_name}
        onChange={setAvatar}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Shahar</span>
          <input className="input" value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Pozitsiya</span>
          <select className="input" value={position} onChange={(e) => setPosition(e.target.value as Position)}>
            {POSITIONS.map((p) => (
              <option key={p} value={p}>
                {POSITION_LABEL[p]}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium text-foreground">Bio</span>
        <textarea className="input" rows={3} value={bio} onChange={(e) => setBio(e.target.value)} />
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

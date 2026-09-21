"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import ImageInput from "@/components/ImageInput";
import { ApiError, clientApi } from "@/lib/clientApi";
import { SQUAD_SIZES } from "@/lib/formations";
import type { Team } from "@/lib/types";

export default function NewTeamPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [description, setDescription] = useState("");
  const [squadSize, setSquadSize] = useState(11);
  const [logo, setLogo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.set("name", name);
      formData.set("city", city);
      formData.set("description", description);
      formData.set("squad_size", String(squadSize));
      if (logo) formData.set("logo", logo);

      const team = await clientApi.post<Team>("/teams", formData);
      router.push(`/teams/${team.slug}`);
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const firstError = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setError(
        Array.isArray(firstError)
          ? String(firstError[0])
          : err instanceof ApiError && err.status === 401
            ? "Jamoa yaratish uchun avval tizimga kiring."
            : "Jamoa yaratishda xatolik yuz berdi."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="card p-8">
        <h1 className="mb-2 text-xl font-bold text-foreground">Yangi jamoa yaratish</h1>
        <p className="mb-6 text-sm text-muted">Siz avtomatik ravishda jamoa sardori bo&apos;lasiz.</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <ImageInput
            label="Jamoa logotipi"
            name="logo"
            fallbackName={name || "Jamoa"}
            rounded="md"
            onChange={setLogo}
          />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-foreground">Jamoa nomi</span>
            <input required className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium text-foreground">Shahar</span>
              <input required className="input" value={city} onChange={(e) => setCity(e.target.value)} />
            </label>
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium text-foreground">O&apos;yinchilar soni</span>
              <select className="input" value={squadSize} onChange={(e) => setSquadSize(Number(e.target.value))}>
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
          {error ? <p className="text-sm text-loss">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="mt-2 rounded-full bg-blue px-4 py-2.5 font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
          >
            {loading ? "Yaratilmoqda..." : "Jamoa yaratish"}
          </button>
        </form>
      </div>
    </div>
  );
}

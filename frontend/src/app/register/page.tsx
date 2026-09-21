"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import GoogleSignInButton from "@/components/GoogleSignInButton";
import ImageInput from "@/components/ImageInput";
import { POSITION_LABEL } from "@/lib/format";
import type { Position } from "@/lib/types";

const POSITIONS: Position[] = ["GK", "DF", "MF", "FW"];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    city: "",
    position: "MF" as Position,
  });
  const [avatar, setAvatar] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    let body: BodyInit;
    let headers: HeadersInit | undefined;
    if (avatar) {
      const formData = new FormData();
      for (const [key, value] of Object.entries(form)) formData.set(key, value);
      formData.set("avatar", avatar);
      body = formData;
    } else {
      body = JSON.stringify(form);
      headers = { "Content-Type": "application/json" };
    }

    const res = await fetch("/api/auth/register", { method: "POST", headers, body });
    setLoading(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const firstError = Object.values(data)[0];
      setError(Array.isArray(firstError) ? String(firstError[0]) : "Ro'yxatdan o'tishda xatolik yuz berdi.");
      return;
    }
    router.push("/dashboard");
    router.refresh();
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="card p-8">
        <h1 className="mb-6 text-xl font-bold text-foreground">Ro&apos;yxatdan o&apos;tish</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Ism">
              <input required className="input" value={form.first_name} onChange={(e) => update("first_name", e.target.value)} />
            </Field>
            <Field label="Familiya">
              <input required className="input" value={form.last_name} onChange={(e) => update("last_name", e.target.value)} />
            </Field>
          </div>
          <Field label="Username">
            <input required className="input" value={form.username} onChange={(e) => update("username", e.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Email">
              <input type="email" className="input" value={form.email} onChange={(e) => update("email", e.target.value)} />
            </Field>
            <Field label="Telefon">
              <input className="input" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
            </Field>
          </div>
          <Field label="Parol">
            <input required type="password" minLength={8} className="input" value={form.password} onChange={(e) => update("password", e.target.value)} />
          </Field>
          <ImageInput label="Profil rasmi" name="avatar" fallbackName={form.first_name || form.username || "?"} onChange={setAvatar} />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Shahar">
              <input className="input" value={form.city} onChange={(e) => update("city", e.target.value)} />
            </Field>
            <Field label="Pozitsiya">
              <select className="input" value={form.position} onChange={(e) => update("position", e.target.value as Position)}>
                {POSITIONS.map((p) => (
                  <option key={p} value={p}>
                    {POSITION_LABEL[p]}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          {error ? <p className="text-sm text-loss">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="mt-2 rounded-full bg-blue px-4 py-2.5 font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
          >
            {loading ? "Yuborilmoqda..." : "Ro'yxatdan o'tish"}
          </button>
        </form>
        <div className="mt-4">
          <GoogleSignInButton />
        </div>
        <p className="mt-4 text-center text-sm text-muted">
          Hisobingiz bormi?{" "}
          <Link href="/login" className="font-medium text-blue">
            Kirish
          </Link>
        </p>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      {children}
    </label>
  );
}

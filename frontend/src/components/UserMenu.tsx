"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { CurrentUser } from "@/lib/types";

const ROLE_LABEL: Record<CurrentUser["role"], string> = {
  player: "O'yinchi",
  tournament_admin: "Turnir admini",
  super_admin: "Super admin",
};

export default function UserMenu({ user }: { user: CurrentUser | null }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="rounded-full px-4 py-1.5 text-sm font-medium text-white/90 hover:text-white"
        >
          Kirish
        </Link>
        <Link href="/register" className="btn-primary px-4 py-1.5 text-sm">
          Ro&apos;yxatdan o&apos;tish
        </Link>
      </div>
    );
  }

  async function handleLogout() {
    setLoading(true);
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
    setLoading(false);
  }

  return (
    <div className="flex items-center gap-3">
      <Link href="/dashboard" className="text-sm text-white/90 hover:text-white">
        <span className="font-semibold">{user.first_name || user.username}</span>
        <span className="ml-1.5 rounded-full bg-white/15 px-2 py-0.5 text-xs">
          {ROLE_LABEL[user.role]}
        </span>
      </Link>
      <button
        onClick={handleLogout}
        disabled={loading}
        className="rounded-full px-3 py-1.5 text-sm text-white/70 hover:text-white disabled:opacity-50"
      >
        Chiqish
      </button>
    </div>
  );
}

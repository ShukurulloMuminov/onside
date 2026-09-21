import Link from "next/link";

import { getCurrentUser } from "@/lib/session";

import NotificationBell from "./NotificationBell";
import UserMenu from "./UserMenu";

const NAV_LINKS = [
  { href: "/players", label: "O'yinchilar" },
  { href: "/teams", label: "Jamoalar" },
  { href: "/tournaments", label: "Turnirlar" },
  { href: "/rankings", label: "Reyting" },
];

export default async function Navbar() {
  const user = await getCurrentUser();

  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-navy/95 backdrop-blur supports-[backdrop-filter]:bg-navy/85">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5 text-lg font-bold tracking-tight text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue to-accent text-sm font-black shadow-lg shadow-blue/30 transition-transform group-hover:scale-105">
            OS
          </span>
          <span>
            OnSide<span className="text-accent">.uz</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3.5 py-2 text-sm font-medium text-white/75 transition hover:bg-white/10 hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1">
          {user ? <NotificationBell /> : null}
          <UserMenu user={user} />
        </div>
      </div>
      <nav className="flex items-center gap-4 overflow-x-auto border-t border-white/10 px-4 py-2 md:hidden">
        {NAV_LINKS.map((link) => (
          <Link key={link.href} href={link.href} className="shrink-0 text-sm text-white/80">
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

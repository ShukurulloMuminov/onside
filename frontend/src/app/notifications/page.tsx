import { redirect } from "next/navigation";

import NotificationsList from "@/components/NotificationsList";
import { apiGetAuthed, getCurrentUser } from "@/lib/session";
import type { AppNotification, Paginated } from "@/lib/types";

export default async function NotificationsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const notifications = await apiGetAuthed<Paginated<AppNotification>>("/notifications/?page_size=50");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-foreground">Bildirishnomalar</h1>
      <NotificationsList initial={notifications?.results ?? []} />
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, clientApi } from "@/lib/clientApi";
import type { Match, MatchEventType, MatchStatus, TeamMembership } from "@/lib/types";

// "finished" is deliberately excluded — the backend rejects a direct PATCH
// to that status (see matches/serializers.py validate_status). A match can
// only become finished via ResultForm's submit-result / force-finalize.
const STATUS_OPTIONS: Exclude<MatchStatus, "finished">[] = ["scheduled", "live", "postponed", "cancelled"];
const EVENT_OPTIONS: { value: MatchEventType; label: string }[] = [
  { value: "goal", label: "Gol" },
  { value: "assist", label: "Assist" },
  { value: "yellow_card", label: "Sariq karta" },
  { value: "red_card", label: "Qizil karta" },
  { value: "own_goal", label: "O'z darvozasiga gol" },
  { value: "substitution", label: "Almashtirish" },
  { value: "mvp", label: "MVP" },
];

export default function MatchAdminPanel({
  match,
  homeRoster,
  awayRoster,
}: {
  match: Match;
  homeRoster: TeamMembership[];
  awayRoster: TeamMembership[];
}) {
  const router = useRouter();

  return (
    <div className="flex flex-col gap-4">
      <ResultForm match={match} onSaved={() => router.refresh()} />
      <ScheduleForm match={match} onSaved={() => router.refresh()} />
      {match.home_registration && match.away_registration ? (
        <EventForm
          matchId={match.id}
          homeRegistration={match.home_registration}
          awayRegistration={match.away_registration}
          homeRoster={homeRoster}
          awayRoster={awayRoster}
          onSaved={() => router.refresh()}
        />
      ) : null}
    </div>
  );
}

function ResultForm({ match, onSaved }: { match: Match; onSaved: () => void }) {
  const [homeScore, setHomeScore] = useState(match.home_score?.toString() ?? "");
  const [awayScore, setAwayScore] = useState(match.away_score?.toString() ?? "");
  const [penaltyHome, setPenaltyHome] = useState(match.penalty_home_score?.toString() ?? "");
  const [penaltyAway, setPenaltyAway] = useState(match.penalty_away_score?.toString() ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isPending = match.status === "pending_confirmation";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (homeScore === "" || awayScore === "") return;
    setSaving(true);
    setError(null);
    try {
      await clientApi.post(`/matches/${match.id}/submit-result`, {
        home_score: Number(homeScore),
        away_score: Number(awayScore),
        penalty_home_score: penaltyHome === "" ? null : Number(penaltyHome),
        penalty_away_score: penaltyAway === "" ? null : Number(penaltyAway),
      });
      onSaved();
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const first = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setError(Array.isArray(first) ? String(first[0]) : "Saqlashda xatolik yuz berdi.");
    } finally {
      setSaving(false);
    }
  }

  async function handleForceFinalize() {
    setSaving(true);
    setError(null);
    try {
      await clientApi.post(`/matches/${match.id}/force-finalize`);
      onSaved();
    } catch {
      setError("Yakunlab bo'lmadi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Natijani kiritish</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Uy hisobi</span>
          <input type="number" min={0} className="input" value={homeScore} onChange={(e) => setHomeScore(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Mehmon hisobi</span>
          <input type="number" min={0} className="input" value={awayScore} onChange={(e) => setAwayScore(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Penalti (uy)</span>
          <input type="number" min={0} className="input" value={penaltyHome} onChange={(e) => setPenaltyHome(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Penalti (mehmon)</span>
          <input type="number" min={0} className="input" value={penaltyAway} onChange={(e) => setPenaltyAway(e.target.value)} />
        </label>
      </div>

      {isPending ? (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3 text-sm">
          <p className="font-medium text-foreground">Sardorning javobini kutmoqda</p>
          <p className="text-muted">
            Istalgan sardor tasdiqlasa — yakunlanadi; rad etsa — natija tozalanib qayta kiritish kerak bo&apos;ladi.
          </p>
          <button
            type="button"
            onClick={handleForceFinalize}
            disabled={saving}
            className="w-fit rounded-full border border-border px-4 py-1.5 text-sm font-medium text-foreground hover:bg-surface disabled:opacity-50"
          >
            Majburan yakunlash
          </button>
        </div>
      ) : null}

      {error ? <p className="text-sm text-loss">{error}</p> : null}
      <button
        type="submit"
        disabled={saving}
        className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
      >
        {saving ? "Saqlanmoqda..." : "Natijani yuborish"}
      </button>
    </form>
  );
}

function ScheduleForm({ match, onSaved }: { match: Match; onSaved: () => void }) {
  const [status, setStatus] = useState<Exclude<MatchStatus, "finished">>(
    match.status === "finished" ? "scheduled" : match.status
  );
  const [scheduledDate, setScheduledDate] = useState(match.scheduled_date ?? "");
  const [scheduledTime, setScheduledTime] = useState(match.scheduled_time ?? "");
  const [venue, setVenue] = useState(match.venue);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await clientApi.patch(`/matches/${match.id}`, {
        status,
        scheduled_date: scheduledDate || null,
        scheduled_time: scheduledTime || null,
        venue,
      });
      onSaved();
    } catch {
      setError("Saqlashda xatolik yuz berdi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Jadval va holat</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Holat</span>
          <select
            className="input"
            value={status}
            onChange={(e) => setStatus(e.target.value as Exclude<MatchStatus, "finished">)}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Maydon</span>
          <input className="input" value={venue} onChange={(e) => setVenue(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Sana</span>
          <input type="date" className="input" value={scheduledDate ?? ""} onChange={(e) => setScheduledDate(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Vaqt</span>
          <input type="time" className="input" value={scheduledTime ?? ""} onChange={(e) => setScheduledTime(e.target.value)} />
        </label>
      </div>
      {error ? <p className="text-sm text-loss">{error}</p> : null}
      <button
        type="submit"
        disabled={saving}
        className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
      >
        {saving ? "Saqlanmoqda..." : "Saqlash"}
      </button>
    </form>
  );
}

function EventForm({
  matchId,
  homeRegistration,
  awayRegistration,
  homeRoster,
  awayRoster,
  onSaved,
}: {
  matchId: number;
  homeRegistration: number;
  awayRegistration: number;
  homeRoster: TeamMembership[];
  awayRoster: TeamMembership[];
  onSaved: () => void;
}) {
  const [type, setType] = useState<MatchEventType>("goal");
  const [playerId, setPlayerId] = useState("");
  const [minute, setMinute] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const options = [
    ...homeRoster.map((m) => ({ id: m.player.id, label: m.player.full_name, teamRegistration: homeRegistration })),
    ...awayRoster.map((m) => ({ id: m.player.id, label: m.player.full_name, teamRegistration: awayRegistration })),
  ];

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const selected = options.find((o) => String(o.id) === playerId);
    if (!selected) return;
    setSaving(true);
    setError(null);
    try {
      await clientApi.post(`/matches/${matchId}/events`, {
        type,
        player: selected.id,
        team_registration: selected.teamRegistration,
        minute: minute === "" ? null : Number(minute),
      });
      setMinute("");
      onSaved();
    } catch (err) {
      const data = err instanceof ApiError ? err.data : null;
      const first = data ? Object.values(data as Record<string, unknown>)[0] : null;
      setError(Array.isArray(first) ? String(first[0]) : "Voqeani qo'shib bo'lmadi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6">
      <h2 className="font-semibold text-foreground">Voqea qo&apos;shish</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Turi</span>
          <select className="input" value={type} onChange={(e) => setType(e.target.value as MatchEventType)}>
            {EVENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm sm:col-span-2">
          <span className="font-medium text-foreground">O&apos;yinchi</span>
          <select required className="input" value={playerId} onChange={(e) => setPlayerId(e.target.value)}>
            <option value="">Tanlang</option>
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-foreground">Daqiqa</span>
          <input type="number" min={0} max={130} className="input" value={minute} onChange={(e) => setMinute(e.target.value)} />
        </label>
      </div>
      {error ? <p className="text-sm text-loss">{error}</p> : null}
      <button
        type="submit"
        disabled={saving}
        className="w-fit rounded-full bg-blue px-5 py-2 text-sm font-semibold text-white hover:bg-blue-dark disabled:opacity-50"
      >
        {saving ? "Qo'shilmoqda..." : "Qo'shish"}
      </button>
    </form>
  );
}

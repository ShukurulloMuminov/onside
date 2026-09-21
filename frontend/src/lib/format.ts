import type { MatchStatus, Position, TournamentFormat, TournamentStatus } from "./types";

export const POSITION_LABEL: Record<Position | "", string> = {
  GK: "Darvozabon",
  DF: "Himoyachi",
  MF: "Yarim himoyachi",
  FW: "Hujumchi",
  "": "—",
};

export const TOURNAMENT_FORMAT_LABEL: Record<TournamentFormat, string> = {
  league: "Liga",
  group_stage: "Guruh bosqichi",
  playoff: "Playoff",
  group_playoff: "Guruh + Playoff",
};

export const TOURNAMENT_STATUS_LABEL: Record<TournamentStatus, string> = {
  draft: "Qoralama",
  pending_approval: "Tasdiqlanmoqda",
  published: "E'lon qilingan",
  registration_open: "Ro'yxatdan o'tish ochiq",
  registration_closed: "Ro'yxatdan o'tish yopiq",
  in_progress: "Davom etmoqda",
  finished: "Yakunlangan",
  cancelled: "Bekor qilingan",
};

export const MATCH_STATUS_LABEL: Record<MatchStatus, string> = {
  scheduled: "Rejalashtirilgan",
  live: "Jonli",
  finished: "Yakunlangan",
  postponed: "Ko'chirilgan",
  cancelled: "Bekor qilingan",
  pending_confirmation: "Tasdiqlanmoqda",
};

export function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function formatDate(value: string | null): string {
  if (!value) return "TBD";
  return new Date(value).toLocaleDateString("uz-UZ", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatTime(value: string | null): string {
  if (!value) return "";
  return value.slice(0, 5);
}

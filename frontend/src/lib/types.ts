export type Position = "GK" | "DF" | "MF" | "FW";

export interface TeamSummary {
  id: number;
  name: string;
  slug: string;
}

export interface Level {
  id: number;
  order: number;
  name: string;
  icon: string;
  description: string;
  required_points: number;
}

export interface Badge {
  id: number;
  name: string;
  icon: string;
  description: string;
  criteria: string;
  is_automatic: boolean;
}

export interface PlayerBadge {
  id: number;
  badge: Badge;
  created_at: string;
}

export interface PlayerProfile {
  id: number;
  player_id: string;
  full_name: string;
  username: string;
  avatar: string | null;
  city: string;
  position: Position | "";
  bio: string;
  current_team: TeamSummary | null;
  level: Level | null;
  badges: PlayerBadge[];
  matches_total: number;
  wins_total: number;
  goals_total: number;
  assists_total: number;
  mvp_total: number;
  yellow_cards_total: number;
  red_cards_total: number;
  tournaments_total: number;
  rating_avg: string;
}

export interface Team {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  captain: PlayerProfile;
  city: string;
  founded_date: string | null;
  description: string;
  squad_size: 5 | 7 | 11;
  member_count: number;
  matches_total: number;
  wins_total: number;
  draws_total: number;
  losses_total: number;
  goals_for_total: number;
  goals_against_total: number;
  tournaments_total: number;
  trophies_total: number;
}

export interface TeamLineupSlotData {
  code: string;
  player: PlayerProfile | null;
}

export interface TeamLineup {
  formation: string;
  slots: TeamLineupSlotData[];
}

export interface TeamMembership {
  id: number;
  player: PlayerProfile;
  is_active: boolean;
  created_at: string;
  left_at: string | null;
}

export interface TeamInvitation {
  id: number;
  team: Team;
  invited_player: PlayerProfile;
  invited_by: number;
  status: "pending" | "accepted" | "rejected" | "cancelled";
  created_at: string;
  responded_at: string | null;
}

export type TournamentFormat = "league" | "group_stage" | "playoff" | "group_playoff";
export type TournamentStatus =
  | "draft"
  | "pending_approval"
  | "published"
  | "registration_open"
  | "registration_closed"
  | "in_progress"
  | "finished"
  | "cancelled";

export interface Tournament {
  id: number;
  name: string;
  slug: string;
  banner: string | null;
  description: string;
  organizer: string;
  city: string;
  venue: string;
  start_date: string | null;
  end_date: string | null;
  format: TournamentFormat;
  status: TournamentStatus;
  max_teams: number;
  prize_info: string;
  points_win: number;
  points_draw: number;
  points_loss: number;
  tie_breaker_config: string[];
  groups_count: number;
  teams_per_group: number;
  qualifiers_per_group: number;
  require_match_confirmation: boolean;
  team_count: number;
}

export interface TournamentRegistration {
  id: number;
  tournament: number;
  team: Team;
  status: "pending" | "approved" | "rejected" | "withdrawn";
  applied_by: number;
  reviewed_by: number | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface GroupStandingRow {
  registration_id: number;
  team: TeamSummary;
  played: number;
  won: number;
  draw: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  position: number;
  qualifies: boolean;
}

export interface GroupStandings {
  id: number;
  name: string;
  standings: GroupStandingRow[];
}

export interface TournamentStandings {
  groups: GroupStandings[];
}

export type MatchStatus =
  | "scheduled"
  | "live"
  | "finished"
  | "postponed"
  | "cancelled"
  | "pending_confirmation";

export type MatchEventType =
  | "goal"
  | "assist"
  | "yellow_card"
  | "red_card"
  | "own_goal"
  | "substitution"
  | "mvp";

export interface MatchEvent {
  id: number;
  match: number;
  type: MatchEventType;
  player: PlayerProfile;
  team_registration: number;
  minute: number | null;
  related_event: number | null;
  created_at: string;
}

export interface MatchTeamRef {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
}

export interface Match {
  id: number;
  tournament: number;
  tournament_slug: string;
  tournament_name: string;
  stage: number | null;
  group: number | null;
  knockout_round: number | null;
  home_registration: number | null;
  away_registration: number | null;
  home_team: MatchTeamRef | null;
  away_team: MatchTeamRef | null;
  scheduled_date: string | null;
  scheduled_time: string | null;
  venue: string;
  referee: string;
  status: MatchStatus;
  home_score: number | null;
  away_score: number | null;
  penalty_home_score: number | null;
  penalty_away_score: number | null;
  feeds_into_match: number | null;
  feeds_into_slot: "home" | "away" | "";
  events: MatchEvent[];
  confirmed_registrations: number[];
}

export interface KnockoutRoundBracket {
  name: string;
  order: number;
  matches: Match[];
}

export interface TournamentBracket {
  rounds: KnockoutRoundBracket[];
}

export interface RankingRow {
  player: PlayerProfile;
  score: number;
  goals: number;
  assists: number;
  wins: number;
  mvp: number;
  matches: number;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  phone: string | null;
  first_name: string;
  last_name: string;
  city: string;
  role: "player" | "tournament_admin" | "super_admin";
  is_superuser: boolean;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type NotificationType =
  | "team_invite"
  | "registration_approved"
  | "registration_rejected"
  | "tournament_started"
  | "badge_earned"
  | "level_up"
  | "match_result"
  | "match_disputed";

export interface AppNotification {
  id: number;
  type: NotificationType;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

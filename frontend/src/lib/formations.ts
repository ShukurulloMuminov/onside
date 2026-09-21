export type SquadSize = 5 | 7 | 11;

export interface SlotPosition {
  code: string;
  label: string;
  x: number; // percent, 0 = left touchline, 100 = right touchline
  y: number; // percent, 0 = opponent goal (top), 100 = own goal (bottom)
}

/**
 * Pitch coordinates for each squad size's formations. Mirrors the slot
 * codes defined in backend/teams/formations.py — the backend owns which
 * codes are valid for a formation (and which formations are valid for a
 * given squad size), this owns where they're drawn.
 *
 * Split by squad size because amateur football is frequently played
 * 5-a-side or 7-a-side, not just the full 11 — a small roster shouldn't
 * be forced onto an 11-player pitch.
 */
export const FORMATIONS_BY_SIZE: Record<SquadSize, Record<string, SlotPosition[]>> = {
  5: {
    "1-2-1": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 50, y: 72 },
      { code: "MF1", label: "MF", x: 30, y: 48 },
      { code: "MF2", label: "MF", x: 70, y: 48 },
      { code: "FW1", label: "FW", x: 50, y: 18 },
    ],
    "2-1-1": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 30, y: 72 },
      { code: "DF2", label: "DF", x: 70, y: 72 },
      { code: "MF1", label: "MF", x: 50, y: 45 },
      { code: "FW1", label: "FW", x: 50, y: 15 },
    ],
    "2-2": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 30, y: 68 },
      { code: "DF2", label: "DF", x: 70, y: 68 },
      { code: "FW1", label: "FW", x: 35, y: 25 },
      { code: "FW2", label: "FW", x: 65, y: 25 },
    ],
  },
  7: {
    "3-2-1": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 20, y: 72 },
      { code: "DF2", label: "DF", x: 50, y: 75 },
      { code: "DF3", label: "DF", x: 80, y: 72 },
      { code: "MF1", label: "MF", x: 32, y: 45 },
      { code: "MF2", label: "MF", x: 68, y: 45 },
      { code: "FW1", label: "FW", x: 50, y: 15 },
    ],
    "2-3-1": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 30, y: 72 },
      { code: "DF2", label: "DF", x: 70, y: 72 },
      { code: "MF1", label: "MF", x: 20, y: 48 },
      { code: "MF2", label: "MF", x: 50, y: 50 },
      { code: "MF3", label: "MF", x: 80, y: 48 },
      { code: "FW1", label: "FW", x: 50, y: 15 },
    ],
    "3-1-2": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "DF1", label: "DF", x: 20, y: 72 },
      { code: "DF2", label: "DF", x: 50, y: 75 },
      { code: "DF3", label: "DF", x: 80, y: 72 },
      { code: "MF1", label: "MF", x: 50, y: 48 },
      { code: "FW1", label: "FW", x: 35, y: 18 },
      { code: "FW2", label: "FW", x: 65, y: 18 },
    ],
  },
  11: {
    "4-4-2": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "LB", label: "LB", x: 15, y: 72 },
      { code: "CB1", label: "CB", x: 38, y: 75 },
      { code: "CB2", label: "CB", x: 62, y: 75 },
      { code: "RB", label: "RB", x: 85, y: 72 },
      { code: "LM", label: "LM", x: 15, y: 45 },
      { code: "CM1", label: "CM", x: 38, y: 48 },
      { code: "CM2", label: "CM", x: 62, y: 48 },
      { code: "RM", label: "RM", x: 85, y: 45 },
      { code: "ST1", label: "ST", x: 38, y: 15 },
      { code: "ST2", label: "ST", x: 62, y: 15 },
    ],
    "4-3-3": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "LB", label: "LB", x: 15, y: 72 },
      { code: "CB1", label: "CB", x: 38, y: 75 },
      { code: "CB2", label: "CB", x: 62, y: 75 },
      { code: "RB", label: "RB", x: 85, y: 72 },
      { code: "CM1", label: "CM", x: 30, y: 50 },
      { code: "CM2", label: "CM", x: 50, y: 55 },
      { code: "CM3", label: "CM", x: 70, y: 50 },
      { code: "LW", label: "LW", x: 15, y: 20 },
      { code: "ST", label: "ST", x: 50, y: 12 },
      { code: "RW", label: "RW", x: 85, y: 20 },
    ],
    "3-5-2": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "CB1", label: "CB", x: 30, y: 75 },
      { code: "CB2", label: "CB", x: 50, y: 78 },
      { code: "CB3", label: "CB", x: 70, y: 75 },
      { code: "LM", label: "LM", x: 12, y: 45 },
      { code: "CM1", label: "CM", x: 32, y: 50 },
      { code: "CM2", label: "CM", x: 50, y: 53 },
      { code: "CM3", label: "CM", x: 68, y: 50 },
      { code: "RM", label: "RM", x: 88, y: 45 },
      { code: "ST1", label: "ST", x: 38, y: 15 },
      { code: "ST2", label: "ST", x: 62, y: 15 },
    ],
    "4-2-3-1": [
      { code: "GK", label: "GK", x: 50, y: 92 },
      { code: "LB", label: "LB", x: 15, y: 72 },
      { code: "CB1", label: "CB", x: 38, y: 75 },
      { code: "CB2", label: "CB", x: 62, y: 75 },
      { code: "RB", label: "RB", x: 85, y: 72 },
      { code: "CDM1", label: "CDM", x: 38, y: 58 },
      { code: "CDM2", label: "CDM", x: 62, y: 58 },
      { code: "LAM", label: "LAM", x: 20, y: 35 },
      { code: "CAM", label: "CAM", x: 50, y: 32 },
      { code: "RAM", label: "RAM", x: 80, y: 35 },
      { code: "ST", label: "ST", x: 50, y: 12 },
    ],
  },
};

export const SQUAD_SIZES: SquadSize[] = [5, 7, 11];

export const DEFAULT_FORMATION_BY_SIZE: Record<SquadSize, string> = {
  5: "1-2-1",
  7: "3-2-1",
  11: "4-4-2",
};

export function formationNames(squadSize: SquadSize): string[] {
  return Object.keys(FORMATIONS_BY_SIZE[squadSize]);
}

export function slotsFor(squadSize: SquadSize, formation: string): SlotPosition[] {
  return FORMATIONS_BY_SIZE[squadSize]?.[formation] ?? FORMATIONS_BY_SIZE[11]["4-4-2"];
}

/** Finds which squad size a formation name belongs to (a lineup fetched
 * from the API only carries the formation string, not the squad size). */
export function squadSizeForFormation(formation: string): SquadSize {
  for (const size of SQUAD_SIZES) {
    if (formation in FORMATIONS_BY_SIZE[size]) return size;
  }
  return 11;
}

"""Canonical slot codes per squad size + formation. Purely structural
(which named positions exist) — the frontend owns the pitch x/y
coordinates for rendering, since that's a presentation concern, not
domain data.

Keyed by squad size (players per side, including the goalkeeper) because
amateur football is frequently played 5-a-side or 7-a-side, not just the
full 11 — each size gets its own formation set rather than forcing a
smaller squad to fill an 11-player pitch."""

SQUAD_SIZES: list[int] = [5, 7, 11]

FORMATIONS_BY_SIZE: dict[int, dict[str, list[str]]] = {
    5: {
        "1-2-1": ["GK", "DF1", "MF1", "MF2", "FW1"],
        "2-1-1": ["GK", "DF1", "DF2", "MF1", "FW1"],
        "2-2": ["GK", "DF1", "DF2", "FW1", "FW2"],
    },
    7: {
        "3-2-1": ["GK", "DF1", "DF2", "DF3", "MF1", "MF2", "FW1"],
        "2-3-1": ["GK", "DF1", "DF2", "MF1", "MF2", "MF3", "FW1"],
        "3-1-2": ["GK", "DF1", "DF2", "DF3", "MF1", "FW1", "FW2"],
    },
    11: {
        "4-4-2": ["GK", "LB", "CB1", "CB2", "RB", "LM", "CM1", "CM2", "RM", "ST1", "ST2"],
        "4-3-3": ["GK", "LB", "CB1", "CB2", "RB", "CM1", "CM2", "CM3", "LW", "ST", "RW"],
        "3-5-2": ["GK", "CB1", "CB2", "CB3", "LM", "CM1", "CM2", "CM3", "RM", "ST1", "ST2"],
        "4-2-3-1": ["GK", "LB", "CB1", "CB2", "RB", "CDM1", "CDM2", "LAM", "CAM", "RAM", "ST"],
    },
}

DEFAULT_SQUAD_SIZE = 11
DEFAULT_FORMATION_BY_SIZE = {5: "1-2-1", 7: "3-2-1", 11: "4-4-2"}


def formation_choices() -> list[tuple[str, str]]:
    """All (formation_name, formation_name) pairs across every squad
    size, for the model field's `choices` — validity against a specific
    team's squad_size is still enforced in the service layer, this just
    bounds the column to known formation names."""
    names: set[str] = set()
    for formations in FORMATIONS_BY_SIZE.values():
        names.update(formations)
    return [(name, name) for name in sorted(names)]

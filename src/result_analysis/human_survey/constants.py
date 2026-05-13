"""Domain constants for survey (human-vs-AI) analysis."""

from __future__ import annotations

# Low-N thresholds (aligned with human-validation figure scripts).
SURVEY_LOW_N_RESPONSES: int = 20
SURVEY_LOW_N_PARTICIPANTS: int = 5

PERSONA_ORDER: tuple[str, ...] = (
    "Libertarian",
    "Collectivist",
    "Nationalist",
    "Globalist",
    "Tech Optimist",
    "Tech Sceptic",
    "Religious",
    "Secularist",
)

PERSONA_COLORS: dict[str, str] = {
    "Libertarian": "#d97757",
    "Collectivist": "#5b8aa6",
    "Nationalist": "#d97757",
    "Globalist": "#5b8aa6",
    "Tech Optimist": "#d97757",
    "Tech Sceptic": "#5b8aa6",
    "Religious": "#d97757",
    "Secularist": "#5b8aa6",
    "Centrist": "#888888",
}

AXIS_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("Economic", "Libertarian", "Collectivist"),
    ("Identity", "Nationalist", "Globalist"),
    ("Technology", "Tech Optimist", "Tech Sceptic"),
    ("Society", "Religious", "Secularist"),
)

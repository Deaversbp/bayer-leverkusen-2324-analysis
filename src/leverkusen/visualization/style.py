"""Football-facing convention, applicable only after explicit semantic validation."""

LEVERKUSEN_COLOR = "#B51232"
OPPONENT_COLOR = "#30343B"
ACTION_COLOR = "#A65F00"
PITCH_BACKGROUND = "#FAFAF7"
PITCH_LINE_COLOR = "#7B8186"
POLYGON_COLOR = "#91A5B0"
POLYGON_ALPHA = 0.20
UNRESOLVED_COLOR = "#666666"
OUTFIELD_MARKER = "o"
KEEPER_MARKER = "s"
EVENT_MARKER = "D"
ACTOR_EDGE_COLOR = "#111111"
ACTOR_HALO_LINEWIDTH = 1.6
TEAM_TEXT_COLOR = "#FFFFFF"
TEAM_LABELS = {"leverkusen": "L", "opponent": "O", "unresolved": "?"}
PROVIDER_ACTION_ARROW = {
    "arrowstyle": "->",
    "linestyle": "-",
    "color": ACTION_COLOR,
    "linewidth": 1.8,
}
EVENT_TRANSITION_ARROW = {
    "arrowstyle": "->",
    "linestyle": "--",
    "color": ACTION_COLOR,
    "linewidth": 1.8,
}
PROVIDER_ACTION_MEANING = "recorded action vector; explicit provider start and end"
EVENT_TRANSITION_MEANING = "event-to-event progression indicator; physical path unknown"
GEOMETRY_OVERLAY_STYLE = {"color": OPPONENT_COLOR, "linestyle": ":", "linewidth": 1.0}

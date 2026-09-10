# Semantic visualization convention — Phase 2C

**10 September 2026: LOCKED within the approved restricted semantic scope.**
Phase 2C = **LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE**, following human
approval in [methods section 40](methods_specification.md#40-human-approved-phase-2c-restricted-semantic-scope-lock).
The convention was established conditionally on 9 September while Phase 2C was
VALIDATED PARTIALLY — NOT LOCKED; that historical finding remains unchanged.
Unrestricted football-facing application is not authorized. Apply these team colors
only when `semantics_status = validated_core_event_team_scope`, as defined in
[methods section 38](methods_specification.md#38-phase-2c-teamrole-semantics-and-attacking-orientation).
An event type alone is not sufficient. Unsupported frames retain unresolved
labels and cannot receive Leverkusen/opponent semantic colors. The convention does not resolve the
remaining frame semantics or authorize tactical interpretation.

The executable source of plotting constants is
[`style.py`](../src/leverkusen/visualization/style.py). New plots consume those
constants directly; historical diagnostic plots retain their original styling.

| Meaning | Constant / convention |
| --- | --- |
| Bayer Leverkusen | `LEVERKUSEN_COLOR = #B51232`, red; point text **L** |
| Opponent | `OPPONENT_COLOR = #30343B`, charcoal; point text **O** |
| Event/action emphasis | `ACTION_COLOR = #A65F00`, dark gold; event start diamond, explicit end cross |
| Unresolved team | `UNRESOLVED_COLOR = #666666`; literal **T/F** in native audit plots, never L/O |
| Pitch | `PITCH_BACKGROUND = #FAFAF7`; lines `#7B8186` |
| Supplied visible polygon | `POLYGON_COLOR = #91A5B0`, alpha `0.20` |
| Outfield observation | Circle (`o`) |
| Keeper observation | Square (`s`), literal keeper flag; no identity inference |
| Actor | Unfilled outer halo, edge `#111111`, linewidth `1.6`; retain team fill |
| Team text | White `#FFFFFF`; L/O distinguishes sides without hue |
| Geometry overlay | Charcoal dotted line, linewidth `1.0`; subordinate to observations |

Dark team fills and gold marks contrast with the pale pitch. White L/O letters,
marker shapes, actor halos and explicit legends make meaning independent of
color. This is a plotting convention, not a claim of full accessibility in
every export size: preserve legible labels when resizing. Opponent kit colors
are not used. Do not make polygon presence, hull area, fill opacity or a smooth
line imply complete observation, controlled space, formation or confidence.

## Axes and provenance

Use the 120 × 80 StatsBomb grid with y increasing downward on the plot. Show the
nominal pitch boundary and retain supplied out-of-bounds points. In a validated
native panel the **event team** attacks increasing x. In the paired normalized
panel the **explicit target team (Leverkusen)** attacks increasing x: identity
for its events, a 180-degree rotation of **both x and y** for opponent events.
Transform polygon, observations, actor, event start and explicit end together.
No half/home/away flip, x-only reflection, clipping or coordinate repair occurs.

Unsupported examples retain a native panel with literal T/F annotations and
an empty normalized panel explaining the reason. Never decorate these with a
guessed attacking direction. A figure must name its exact event type, event
team, possession team, period, match, event ID, semantic/orientation status and
pinned source. Points remain anonymous observations in a single event frame.

## Arrow contract

The following arrow semantics are locked within the approved scope. No sequence
plotting implementation or inferred movement is authorized by this convention.

**Solid arrow (`PROVIDER_ACTION_ARROW`) = recorded action vector.** Draw only
when the provider gives a valid event start and end, e.g. pass, carry or shot
projected to pitch x/y. A shot's third coordinate is height and is not plotted.
The segment does not measure a continuously tracked ball trajectory. Direction
language requires a validated reference and a named target team; a positive
delta x is an axial displacement toward that target's attacking end, not proof
of increasing danger or decreasing Euclidean distance to goal.

**Dashed arrow (`EVENT_TRANSITION_ARROW`) = event-to-event progression
indicator.** Reserved for future distinct event observations. It does not imply
the physical ball path between events. No such transitions or sequences are
constructed in Phase 2C. Both arrow styles use the centralized gold color, and
their line styles and legends must remain distinct.

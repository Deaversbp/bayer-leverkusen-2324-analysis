"""Inherited Phase 3A trusted progression state; no segmentation or reset replay.

Extracted unchanged from reset_rule_replay.State for reusable measurement guards.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def flag(value):
    if str(value).lower() not in {"true", "false"}:
        raise ValueError(f"Invalid Boolean: {value!r}")
    return str(value).lower() == "true"


@dataclass
class State:
    peak: float = np.nan
    peak_time: float = np.nan
    previous_end: float = np.nan
    nonpositive: int = 0
    recent: list = field(default_factory=list)
    relocation_pending: bool = False
    relocation_affected: bool = False

    def observe(self, row):
        """Inherit trusted-vector, restart and relocation measurement conventions."""
        context = str(row.provider_context)
        failed = row.event_type == "Pass" and "pass.outcome:" in context
        restart = pd.notna(row.restart_context) and bool(str(row.restart_context))
        safe = (
            flag(row.safe_action)
            and row.event_team_id == 904
            and row.event_type in {"Pass", "Carry"}
        )
        if (
            row.event_type
            in {"Clearance", "Miscontrol", "Dispossessed", "Ball Recovery"}
            or failed
            or "ball_receipt.outcome:Incomplete" in context
        ):
            self.relocation_pending = True
        if failed:
            self.nonpositive = 0
        if not safe or failed:
            return None
        assert np.isfinite([row.start_x, row.end_x, row.period_seconds]).all()
        old_peak = self.peak
        if (
            pd.notna(self.previous_end)
            and row.start_x < self.previous_end - 1e-9
            and self.relocation_pending
        ):
            self.relocation_affected = True
        self.relocation_pending = False
        for x in [row.end_x] if restart else [row.start_x, row.end_x]:
            if pd.isna(self.peak) or x >= self.peak:
                self.peak, self.peak_time = x, row.period_seconds
                self.relocation_affected = False
        dx = row.end_x - row.start_x
        if restart:
            self.nonpositive, self.recent = 0, []
        else:
            self.nonpositive = self.nonpositive + 1 if dx <= 0 else 0
            self.recent = (self.recent + [max(-dx, 0)])[-3:]
        self.previous_end = row.end_x
        return dict(
            dx=dx,
            restart=restart,
            eligible=not restart and not self.relocation_affected,
            forward_peak=dx > 0 and (pd.isna(old_peak) or row.end_x > old_peak),
            retreat=max(0, self.peak - row.end_x),
        )



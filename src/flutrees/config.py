from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Optional
from .layout import FigureStyle, FIGURE_FIELDS, finite_number


@dataclass(frozen=True)
class RunConfig:
    mafft: str = "mafft"
    threads: Optional[int] = None
    start_residue: int = 84
    end_residue: int = 284
    max_depth: int = 10
    min_split: int = 5
    min_freq: float = 0.05
    prune_cutoff: int = 10
    tree_mode: str = "frequency"
    reference_id: Optional[str] = None
    reproducible: Optional[bool] = None
    figure_width: float = 14.0
    figure_height: float = 8.5
    level_spacing: float = 1.0
    node_spacing: float = 1.0
    line_width: float = 1.5

    def __post_init__(self) -> None:
        for name in ("start_residue", "end_residue", "max_depth", "min_split", "prune_cutoff"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer, not a Boolean, float, or string.")
        if self.threads is not None and type(self.threads) is not int:
            raise ValueError("Threads must be an integer, not a Boolean, float, or string.")
        if not isinstance(self.mafft, str) or not self.mafft.strip() or "\x00" in self.mafft:
            raise ValueError("MAFFT must be a nonempty executable name or path without null characters.")
        if self.reproducible is not None and type(self.reproducible) is not bool:
            raise ValueError("Reproducible alignment must be True, False, or None for the mode default.")
        if not isinstance(self.tree_mode, str) or self.tree_mode not in {"frequency", "balanced", "diversity", "all"}:
            raise ValueError("Tree mode must be frequency, balanced, diversity, or all.")
        if self.reference_id is not None and (not isinstance(self.reference_id, str) or not self.reference_id.strip()):
            raise ValueError("Reference ID must be a nonempty string.")
        if self.start_residue < 1 or self.end_residue < self.start_residue:
            raise ValueError("Residue window must satisfy 1 <= start <= end.")
        if not 0 <= self.max_depth <= 20:
            raise ValueError("Maximum tree depth must be between 0 and 20.")
        if self.min_split < 1 or self.prune_cutoff < 1:
            raise ValueError("Minimum split and pruning counts must be at least 1.")
        finite_number(self.min_freq, "Minimum frequency", 0, 0.5)
        if self.threads is not None and self.threads < 1:
            raise ValueError("Threads must be at least 1.")
        self.figure_style()

    def figure_style(self) -> FigureStyle:
        return FigureStyle(**{name: getattr(self, name) for name in FIGURE_FIELDS})

    @staticmethod
    def default_run_id() -> str:
        return datetime.now().strftime("run%Y%m%d_%H%M%S_%f")

    def resolved_threads(self) -> int:
        if self.threads is not None:
            return int(self.threads)
        slurm = os.environ.get("SLURM_CPUS_PER_TASK")
        if slurm:
            try:
                return max(1, int(slurm))
            except ValueError:
                pass
        return 8

    def tree_modes(self) -> tuple[str, ...]:
        return ("frequency", "balanced", "diversity") if self.tree_mode == "all" else (self.tree_mode,)

    def resolved_reproducible(self) -> bool:
        """Keep the single frequency workflow unchanged; stabilize new views."""
        if self.reproducible is not None:
            return self.reproducible
        return self.tree_mode != "frequency"

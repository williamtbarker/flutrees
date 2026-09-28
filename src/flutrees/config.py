from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import math
from typing import Optional


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

    def __post_init__(self) -> None:
        if self.start_residue < 1 or self.end_residue < self.start_residue:
            raise ValueError("Residue window must satisfy 1 <= start <= end.")
        if not 0 <= self.max_depth <= 20:
            raise ValueError("Maximum tree depth must be between 0 and 20.")
        if self.min_split < 1 or self.prune_cutoff < 1:
            raise ValueError("Minimum split and pruning counts must be at least 1.")
        if not math.isfinite(self.min_freq) or not 0 <= self.min_freq <= 0.5:
            raise ValueError("Minimum frequency must be between 0 and 0.5.")
        if self.threads is not None and self.threads < 1:
            raise ValueError("Threads must be at least 1.")

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

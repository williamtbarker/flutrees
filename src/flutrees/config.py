from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
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

    @staticmethod
    def default_run_id() -> str:
        return datetime.now().strftime("run%Y%m%d_%H%M%S")

    def resolved_threads(self) -> int:
        if self.threads is not None:
            return int(self.threads)
        slurm = os.environ.get("SLURM_CPUS_PER_TASK")
        if slurm:
            try:
                return int(slurm)
            except ValueError:
                pass
        return 8

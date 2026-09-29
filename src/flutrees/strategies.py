"""Deterministic split strategies over one shared set of mutation observations."""

from decimal import Decimal
from enum import Enum
from math import ceil, fsum, log2


class SplitStrategy(str, Enum):
    FREQUENCY = "frequency"
    BALANCED = "balanced"
    DIVERSITY = "diversity"


DESCRIPTIONS = {
    "frequency": "Frequency (legacy): select the most prevalent eligible substitution.",
    "balanced": "Balanced: select the most even eligible positive/negative partition.",
    "diversity": "Diversity: reduce residue diversity at other completely observed positions.",
}
STRATEGY_VERSION = "1"


def entropy(counts):
    """Categorical Shannon entropy in bits; zero-count categories contribute zero."""
    n = sum(counts)
    if not n:
        return 0.0
    return -fsum((c / n) * log2(c / n) for c in counts if c)


class SplitSelector:
    """Share eligibility rules while keeping frequency encounter-order tie breaks."""

    def __init__(self, mutations, unknown, min_split, min_freq, strategy):
        self.mutations = mutations
        self.unknown = unknown
        self.min_split = min_split
        self.min_freq = min_freq
        self.strategy = SplitStrategy(strategy)
        self.positions = {}
        for mutation, ids in mutations.items():
            self.positions.setdefault(int(mutation[1:-1]), []).append(ids)

    def candidates(self, seqs, used):
        n = len(seqs)
        threshold = max(ceil(Decimal(str(self.min_freq)) * n), self.min_split)
        candidates = []
        for mutation, ids in self.mutations.items():
            if mutation in used or seqs & self.unknown.get(int(mutation[1:-1]), set()):
                continue
            positive = seqs & ids
            if min(len(positive), n - len(positive)) >= threshold:
                candidates.append((mutation, positive))
        return candidates

    def choose(self, seqs, used):
        candidates = self.candidates(seqs, used)
        if not candidates:
            return None
        n = len(seqs)
        if self.strategy == SplitStrategy.FREQUENCY:
            return max(candidates, key=lambda item: len(item[1]))[0]
        if self.strategy == SplitStrategy.BALANCED:
            return max(candidates, key=lambda item: (min(len(item[1]), n - len(item[1])), len(item[1])))[0]
        scores = self.diversity_scores(seqs, candidates)
        # Twelve-decimal quantization avoids platform-dependent floating-point tie noise.
        return max(candidates, key=lambda item: (
            round(scores[item[0]], 12), min(len(item[1]), n - len(item[1])), len(item[1])
        ))[0]

    def diversity_scores(self, seqs, candidates):
        """Sum information gains at other fully observed residue positions.

        Positions, not binary mutation features, receive equal weight. The split
        position is excluded, so a candidate does not earn credit for predicting
        itself or mutually exclusive substitutions at the same site. Missing
        positions are excluded for every candidate in the node, never imputed.
        """
        n = len(seqs)
        profiles = []
        for position, categories in self.positions.items():
            if seqs & self.unknown.get(position, set()):
                continue
            groups = [seqs & ids for ids in categories]
            counts = [len(group) for group in groups]
            counts.append(n - sum(counts))  # observed reference category
            parent = entropy(counts)
            if parent:
                profiles.append((position, groups, counts, parent))
        scores = {}
        for mutation, positive in candidates:
            w = len(positive)
            position = int(mutation[1:-1])
            gains = []
            for other_position, groups, counts, parent in profiles:
                if other_position == position:
                    continue
                left = [len(positive & group) for group in groups]
                left.append(w - sum(left))
                right = [count - count_left for count, count_left in zip(counts, left)]
                gains.append(parent - (w * entropy(left) + (n - w) * entropy(right)) / n)
            scores[mutation] = max(0.0, fsum(gains))
        return scores

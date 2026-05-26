from __future__ import annotations

from pathlib import Path
from typing import Iterator

from cam_physgeo.dpo.preference_schema import validate_pair
from cam_physgeo.utils.io import read_jsonl


class AnchoredPreferenceDataset:
    """Lightweight JSONL preference dataset for anchored DPO.

    The heavy video decoding/model loss is delegated to LingBot adapters. This
    class enforces schema and filtering so Stage2 never trains on malformed or
    freeze-hacked preference pairs.
    """

    def __init__(
        self,
        pair_jsonl: str | Path,
        *,
        min_margin: float = 0.05,
        min_winner_reward: float = 0.0,
        max_winner_freeze_penalty: float = 0.6,
    ) -> None:
        self.pair_jsonl = str(pair_jsonl)
        self.min_margin = float(min_margin)
        self.min_winner_reward = float(min_winner_reward)
        self.max_winner_freeze_penalty = float(max_winner_freeze_penalty)
        self._rows = [row for row in read_jsonl(self.pair_jsonl) if self._keep(row)]

    def _keep(self, row: dict) -> bool:
        if validate_pair(row):
            return False
        if float(row.get("margin") or 0.0) < self.min_margin:
            return False
        reward = row.get("winner", {}).get("reward", {})
        if float(reward.get("reward_total") or 0.0) < self.min_winner_reward:
            return False
        freeze = reward.get("components", {}).get("freeze", {}).get("penalty", 0.0)
        return float(freeze or 0.0) <= self.max_winner_freeze_penalty

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[dict]:
        return iter(self._rows)

    def __getitem__(self, index: int) -> dict:
        return self._rows[index]

from __future__ import annotations
import math
from typing import Iterable

def clamp01(v: float) -> float: return max(0.0, min(1.0, 0.0 if math.isnan(float(v)) else float(v)))
def score_from_error(error: float, scale: float=1.0) -> float: return clamp01(math.exp(-float(error)/max(scale,1e-8)))
def mean(values: Iterable[float], default: float=0.0) -> float:
    vals=[float(v) for v in values if v is not None]
    return sum(vals)/len(vals) if vals else default

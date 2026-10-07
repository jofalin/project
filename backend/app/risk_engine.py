from dataclasses import dataclass
from enum import Enum
from typing import Sequence

class HazardState(str, Enum):
    NOMINAL = "NOMINAL"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True, slots=True)
class RiskWeights:
    density: float = 0.40
    density_rate: float = 0.25
    bottleneck: float = 0.20
    weather: float = 0.15

    def normalized(self) -> "RiskWeights":
        total = self.density + self.density_rate + self.bottleneck + self.weather
        if total <= 0:
            raise ValueError("At least one risk weight must be positive")
        return RiskWeights(
            self.density / total, self.density_rate / total,
            self.bottleneck / total, self.weather / total
        )

@dataclass(frozen=True, slots=True)
class RiskInput:
    zone_id: str
    occupancy: float
    max_capacity: float
    density_change_per_minute: float
    inflow_rate: float
    outflow_rate: float
    warning_threshold: float = 0.75
    critical_threshold: float = 0.90
    weather_severity: float = 0.0

@dataclass(frozen=True, slots=True)
class RiskResult:
    zone_id: str
    score: float
    hazard_state: HazardState
    early_warning: bool
    density_ratio: float
    normalized_density_rate: float
    bottleneck_factor: float
    weather_severity: float

def calculate_risk(item: RiskInput, weights: RiskWeights = RiskWeights()) -> RiskResult:
    w = weights.normalized()
    density_ratio = min(1.0, max(0.0, item.occupancy / max(item.max_capacity, 1.0)))
    normalized_rate = min(1.0, max(0.0, abs(item.density_change_per_minute)))
    pressure_ratio = item.inflow_rate / max(item.outflow_rate, 1.0)
    bottleneck = min(1.0, max(0.0, (pressure_ratio - 0.5) / 1.5))
    weather = min(1.0, max(0.0, item.weather_severity))
    score = min(1.0, max(0.0,
        w.density * density_ratio
        + w.density_rate * normalized_rate
        + w.bottleneck * bottleneck
        + w.weather * weather
    ))
    early_warning = score >= max(0.65, item.warning_threshold * 0.90) or density_ratio >= item.warning_threshold
    hazard = (
        HazardState.CRITICAL if score >= 0.80 or density_ratio >= item.critical_threshold
        else HazardState.ELEVATED if early_warning else HazardState.NOMINAL
    )
    return RiskResult(item.zone_id, round(score, 6), hazard, early_warning,
                      round(density_ratio, 6), round(normalized_rate, 6),
                      round(bottleneck, 6), round(weather, 6))

def calculate_risk_matrix(items: Sequence[RiskInput], weights: RiskWeights = RiskWeights()) -> list[RiskResult]:
    return [calculate_risk(item, weights) for item in items]

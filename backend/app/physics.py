from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True, slots=True)
class WeatherImpact:
    severity: float = 0.0
    exit_velocity_multiplier: float = 1.0

def weather_impact(rain_mm: float = 0.0, severity: float | None = None) -> WeatherImpact:
    sev = max(0.0, min(1.0, float(severity if severity is not None else min(rain_mm / 10.0, 1.0))))
    if rain_mm >= 5.0 or sev >= 0.75:
        multiplier = 0.75
    elif rain_mm >= 2.0 or sev >= 0.45:
        multiplier = 0.85
    elif rain_mm > 0 or sev > 0:
        multiplier = 0.93
    else:
        multiplier = 1.0
    return WeatherImpact(severity=sev, exit_velocity_multiplier=multiplier)

def time_to_capacity(max_capacity: float, current_occupancy: float, inflow_rate: float, outflow_rate: float) -> float | None:
    headroom = max(0.0, max_capacity - current_occupancy)
    net_inflow = inflow_rate - outflow_rate
    if headroom <= 0:
        return 0.0
    if net_inflow <= 0:
        return None
    return headroom / net_inflow

@dataclass(frozen=True, slots=True)
class ZoneFlowState:
    zone_id: str
    occupancy: float
    max_capacity: float
    inflow_rate: float
    outflow_rate: float
    base_travel_seconds: float = 30.0
    warning_threshold: float = 0.75

    @property
    def density_ratio(self) -> float:
        return min(1.0, max(0.0, self.occupancy / max(self.max_capacity, 1.0)))

def propagation_delay(source: ZoneFlowState, target: ZoneFlowState, weather: WeatherImpact) -> dict:
    adjusted_outflow = target.outflow_rate * weather.exit_velocity_multiplier
    downstream_net = max(0.0, source.inflow_rate - adjusted_outflow)
    target_queue = max(0.0, target.occupancy - target.max_capacity * target.warning_threshold)
    queue_delay = target_queue / downstream_net if downstream_net > 0 else 0.0
    travel_delay = source.base_travel_seconds / max(weather.exit_velocity_multiplier, 0.25)
    return {
        "propagation_delay_seconds": round(travel_delay + queue_delay, 3),
        "queue_delay_seconds": round(queue_delay, 3),
        "travel_delay_seconds": round(travel_delay, 3),
        "target_time_to_capacity_seconds": time_to_capacity(target.max_capacity, target.occupancy, source.inflow_rate, adjusted_outflow),
        "effective_outflow_rate": round(adjusted_outflow, 3),
        "weather_exit_velocity_multiplier": weather.exit_velocity_multiplier,
    }

def propagate_network(zones: Sequence[ZoneFlowState], edges: Sequence[tuple[str, str]], weather: WeatherImpact) -> list[dict]:
    by_id = {zone.zone_id: zone for zone in zones}
    return [
        {
            **propagation_delay(by_id[src], by_id[dst], weather),
            "source_zone_id": src,
            "target_zone_id": dst,
        }
        for src, dst in edges
    ]

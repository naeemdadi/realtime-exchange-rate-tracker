from app.models import Freshness


def classify(age_seconds: float, thresholds: tuple[float, float]) -> Freshness:
    fresh_until, stale_until = thresholds
    if age_seconds <= fresh_until:
        return "fresh"
    if age_seconds <= stale_until:
        return "stale"
    return "very_stale"

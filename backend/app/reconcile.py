import logging

logger = logging.getLogger(__name__)


def reconcile(
    rates: dict[str, float], reference: dict[str, float], max_deviation: float
) -> dict[str, float]:
    """Replaces any rate that strays more than max_deviation from the daily reference."""
    reconciled = dict(rates)
    for code, value in rates.items():
        expected = reference.get(code)
        if expected and abs(value - expected) / expected > max_deviation:
            logger.warning("rate for %s (%s) deviates from reference (%s)", code, value, expected)
            reconciled[code] = expected
    return reconciled

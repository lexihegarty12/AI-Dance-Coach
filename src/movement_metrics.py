"""Camera-dependent geometry metrics for the first plié/tendu baseline.

These measurements are practice proxies, not anatomical assessments. They are
most interpretable when the relevant body plane is visible and the camera stays
fixed.
"""

from __future__ import annotations

import math


def _vector(start: object, end: object) -> tuple[float, float]:
    return end.x - start.x, end.y - start.y


def _angle_between(first: tuple[float, float], second: tuple[float, float]) -> float:
    first_length = math.hypot(*first)
    second_length = math.hypot(*second)
    if first_length == 0 or second_length == 0:
        return float("nan")
    cosine = sum(a * b for a, b in zip(first, second)) / (first_length * second_length)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def knee_flexion_angle(hip: object, knee: object, ankle: object) -> float:
    """Return the hip-knee-ankle angle in degrees.

    This is useful for describing the depth of a plié. It is not the primary
    knee-tracking metric.
    """
    return _angle_between(_vector(knee, hip), _vector(knee, ankle))


def knee_to_toe_alignment_angle(knee: object, toe: object) -> float:
    """Return deviation of the knee-to-toe line from vertical in degrees.

    Zero degrees means the knee and toe are vertically aligned in the image.
    The sign is intentionally omitted because left/right camera orientation
    changes the interpretation; use the magnitude as a screening proxy.
    """
    dx = toe.x - knee.x
    dy = toe.y - knee.y
    if dx == 0 and dy == 0:
        return float("nan")
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def knee_to_toe_offset(knee: object, toe: object, hip_width: float) -> float:
    """Return horizontal knee-to-toe offset normalized by hip width."""
    return abs(knee.x - toe.x) / max(abs(hip_width), 1e-6)


def foot_to_lower_leg_angle(knee: object, ankle: object, heel: object, toe: object) -> float:
    """Return the angle between the lower-leg and foot lines in degrees.

    A large change can indicate a foot-shape or sickling issue, but this metric
    is highly dependent on camera angle and should be interpreted with a visible
    foot and a fixed view.
    """
    lower_leg = _vector(knee, ankle)
    foot = _vector(heel, toe)
    return _angle_between(lower_leg, foot)

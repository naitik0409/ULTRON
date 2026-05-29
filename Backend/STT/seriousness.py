import numpy as np


def analyze(audio: np.ndarray, sr: int = 16000, pitch_info: dict | None = None, features: dict | None = None) -> dict:
    if audio is None or len(audio) < sr // 10:
        return {"seriousness": 0.5, "urgency": 0.5, "confidence": 0.0}

    features = features or {}
    pitch_info = pitch_info or {}

    rms = features.get("rms", 0.01)
    energy_var = features.get("energy_variance", 0)
    voice_ratio = features.get("voice_ratio", 0.5)
    zcr = features.get("zero_crossing_rate", 0)

    f0_mean = pitch_info.get("f0_mean", 150)
    f0_std = pitch_info.get("f0_std", 30)
    f0_range = pitch_info.get("f0_range", 50)

    if voice_ratio < 0.1:
        return {"seriousness": 0.5, "urgency": 0.3, "confidence": 0.0}

    volume_factor = min(1.0, rms * 25)
    stability = max(0.0, 1.0 - min(1.0, f0_std / 80))
    energy_consistency = max(0.0, 1.0 - min(1.0, energy_var * 5))

    low_pitch_factor = max(0.0, 1.0 - (f0_mean - 60) / 200)
    narrow_range_factor = max(0.0, 1.0 - f0_range / 150)

    seriousness = (
        stability * 0.30 +
        energy_consistency * 0.20 +
        volume_factor * 0.20 +
        low_pitch_factor * 0.15 +
        narrow_range_factor * 0.15
    )

    urgency = (
        volume_factor * 0.30 +
        (1 - stability) * 0.25 +
        min(1.0, zcr * 40) * 0.25 +
        min(1.0, energy_var * 6) * 0.20
    )

    seriousness = min(1.0, max(0.0, seriousness))
    urgency = min(1.0, max(0.0, urgency))

    return {
        "seriousness": round(seriousness, 2),
        "urgency": round(urgency, 2),
        "volume_factor": round(volume_factor, 2),
        "stability": round(stability, 2),
        "energy_consistency": round(energy_consistency, 2),
        "confidence": round(min(1.0, voice_ratio), 2),
    }


def describe(seriousness_info: dict) -> str:
    seriousness = seriousness_info.get("seriousness", 0.5)
    urgency = seriousness_info.get("urgency", 0.5)
    conf = seriousness_info.get("confidence", 0)

    if conf < 0.2:
        return "unable to determine seriousness"

    parts = []

    if seriousness > 0.7:
        parts.append("sounding very serious")
    elif seriousness > 0.5:
        parts.append("moderately serious")
    elif seriousness < 0.3:
        parts.append("not sounding serious")

    if urgency > 0.7:
        parts.append("with high urgency")
    elif urgency > 0.5:
        parts.append("some urgency detected")

    return ", ".join(parts) if parts else "neutral seriousness level"

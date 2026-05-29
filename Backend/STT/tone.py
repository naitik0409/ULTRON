import numpy as np


def analyze(audio: np.ndarray, sr: int = 16000, pitch_info: dict | None = None, features: dict | None = None) -> dict:
    if audio is None or len(audio) < sr // 10:
        return {"tone": "neutral", "tone_score": 0.5, "confidence": 0.0}

    features = features or {}
    pitch_info = pitch_info or {}

    duration = features.get("duration", len(audio) / sr)
    rms = features.get("rms", 0.01)
    energy_var = features.get("energy_variance", 0)
    zcr = features.get("zero_crossing_rate", 0)
    voice_ratio = features.get("voice_ratio", 0.5)

    f0_mean = pitch_info.get("f0_mean", 150)
    f0_std = pitch_info.get("f0_std", 30)
    f0_range = pitch_info.get("f0_range", 50)

    if rms < 0.005 or voice_ratio < 0.1:
        return {"tone": "quiet", "tone_score": 0.2, "confidence": 0.6}

    assertiveness = min(1.0, rms * 20)
    stability = max(0.0, 1.0 - min(1.0, f0_std / 100))
    energy = min(1.0, energy_var * 5)
    pitch_level = min(1.0, max(0.0, (f0_mean - 80) / 300))

    if assertiveness > 0.7 and pitch_level > 0.5 and energy > 0.6:
        tone = "assertive"
        score = 0.8
    elif assertiveness < 0.3 and pitch_level < 0.4:
        tone = "subdued"
        score = 0.3
    elif stability > 0.7 and assertiveness > 0.4:
        tone = "calm"
        score = 0.7
    elif pitch_level > 0.7 and energy > 0.5:
        tone = "enthusiastic"
        score = 0.85
    elif pitch_level < 0.3 and energy < 0.3:
        tone = "tired"
        score = 0.25
    else:
        tone = "neutral"
        score = 0.5

    return {
        "tone": tone,
        "tone_score": round(score, 2),
        "assertiveness": round(assertiveness, 2),
        "stability": round(stability, 2),
        "energy_level": round(energy, 2),
        "confidence": round(min(1.0, voice_ratio), 2),
    }


def describe(tone_info: dict) -> str:
    tone = tone_info.get("tone", "neutral")
    conf = tone_info.get("confidence", 0)

    if conf < 0.3:
        return "unable to determine tone"

    descriptions = {
        "assertive": "speaking assertively",
        "subdued": "speaking quietly and subdued",
        "calm": "speaking in a calm tone",
        "enthusiastic": "sounding enthusiastic",
        "tired": "sounding tired or low energy",
        "neutral": "speaking in a neutral tone",
        "quiet": "speaking very quietly",
    }

    return descriptions.get(tone, f"speaking in a {tone} tone")

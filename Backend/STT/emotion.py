import numpy as np


def classify(audio: np.ndarray, sr: int = 16000, pitch_info: dict | None = None, features: dict | None = None) -> dict:
    if audio is None or len(audio) < sr // 5:
        return {"emotion": "neutral", "emotion_score": 0.5, "confidence": 0.0}

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

    if voice_ratio < 0.1 or rms < 0.003:
        return {"emotion": "unknown", "emotion_score": 0.0, "confidence": 0.0}

    pitch_excitement = min(1.0, max(0.0, (f0_mean - 100) / 250))
    pitch_variability = min(1.0, f0_std / 80)
    volume = min(1.0, rms * 30)
    volume_var = min(1.0, energy_var * 8)
    rate_indicator = min(1.0, zcr * 50)

    anger_score = volume * 0.3 + pitch_excitement * 0.25 + volume_var * 0.25 + pitch_variability * 0.2
    happiness_score = pitch_excitement * 0.3 + pitch_variability * 0.2 + volume * 0.25 + rate_indicator * 0.25
    sadness_score = (1 - pitch_excitement) * 0.35 + (1 - volume) * 0.35 + (1 - rate_indicator) * 0.3
    anxiety_score = pitch_variability * 0.35 + volume_var * 0.3 + rate_indicator * 0.2 + (1 - volume) * 0.15
    calm_score = (1 - pitch_variability) * 0.3 + (1 - volume_var) * 0.3 + (1 - rate_indicator) * 0.2 + volume * 0.2

    emotions = {
        "angry": anger_score,
        "happy": happiness_score,
        "sad": sadness_score,
        "anxious": anxiety_score,
        "calm": calm_score,
        "neutral": 0.4,
    }

    if voice_ratio < 0.3:
        emotions["sad"] *= 1.3
        emotions["calm"] *= 1.2

    if rms < 0.01 and energy_var < 0.001:
        emotions["calm"] *= 1.5
        emotions["neutral"] *= 1.3

    dominant = max(emotions, key=emotions.get)
    score = emotions[dominant]
    confidence = min(1.0, (score - 0.3) / 0.5) if score > 0.3 else 0.0

    return {
        "emotion": dominant,
        "emotion_score": round(score, 2),
        "scores": {k: round(v, 2) for k, v in sorted(emotions.items(), key=lambda x: x[1], reverse=True)},
        "confidence": round(max(0.0, confidence), 2),
    }


def describe(emotion_info: dict) -> str:
    emotion = emotion_info.get("emotion", "neutral")
    conf = emotion_info.get("confidence", 0)

    if conf < 0.2:
        return "unable to detect emotion clearly"

    descriptions = {
        "angry": "sounding frustrated or angry",
        "happy": "sounding happy and upbeat",
        "sad": "sounding sad or down",
        "anxious": "sounding anxious or tense",
        "calm": "sounding calm and relaxed",
        "neutral": "sounding neutral",
        "unknown": "voice is unclear",
    }

    return descriptions.get(emotion, f"sounding {emotion}")

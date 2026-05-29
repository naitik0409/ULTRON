import numpy as np


def detect(audio: np.ndarray, sr: int = 16000, features: dict | None = None) -> dict:
    if audio is None or len(audio) < sr // 5:
        return {"laughing": False, "coughing": False, "confidence": 0.0, "details": "audio too short"}

    features = features or {}

    rms = features.get("rms", 0.01)
    energy_var = features.get("energy_variance", 0)
    zcr = features.get("zero_crossing_rate", 0)
    voice_ratio = features.get("voice_ratio", 0.5)
    duration = features.get("duration", len(audio) / sr)

    result = {"laughing": False, "coughing": False, "confidence": 0.0, "details": ""}

    _analyze_segments(audio, sr, result, features)

    return result


def _analyze_segments(audio: np.ndarray, sr: int, result: dict, features: dict):
    n = len(audio)
    segment_duration = 0.3
    seg_samples = int(segment_duration * sr)
    if seg_samples == 0:
        return

    n_segments = max(1, n // seg_samples)
    segments = np.array_split(audio[:n_segments * seg_samples], n_segments)

    seg_energies = []
    seg_zcrs = []
    for seg in segments:
        seg_energies.append(np.sqrt(np.mean(seg ** 2)))
        seg_zcrs.append(np.sum(np.abs(np.diff(np.signbit(seg)))) / len(seg))

    seg_energies = np.array(seg_energies)
    seg_zcrs = np.array(seg_zcrs)

    if len(seg_energies) < 3:
        result["details"] = "too few segments"
        return

    energy_mean = np.mean(seg_energies)
    energy_std = np.std(seg_energies)

    voice_threshold = 0.015
    high_energy_segments = seg_energies > voice_threshold
    n_voice = np.sum(high_energy_segments)

    if n_voice < 2:
        result["details"] = "no significant voice segments"
        return

    burst_pattern = _detect_bursts(seg_energies, energy_mean, energy_std)
    rhythmic = _detect_rhythmic(seg_energies, sr, seg_samples)
    silence_ratio = 1.0 - (n_voice / len(seg_energies))

    rms = features.get("rms", energy_mean)
    energy_var = features.get("energy_variance", np.var(seg_energies) * 100)
    zcr = features.get("zero_crossing_rate", np.mean(seg_zcrs))
    voice_ratio = features.get("voice_ratio", n_voice / len(seg_energies))

    laugh_score = 0.0
    cough_score = 0.0

    if burst_pattern and 0.2 < silence_ratio < 0.6:
        laugh_score += 0.4
    if rhythmic and burst_pattern:
        laugh_score += 0.3
    if zcr > 0.1 and energy_std > energy_mean * 0.8:
        laugh_score += 0.2

    if burst_pattern and not rhythmic and silence_ratio < 0.3:
        cough_score += 0.5
    if burst_pattern and energy_std > energy_mean * 1.2:
        cough_score += 0.3

    if voice_ratio < 0.3:
        cough_score *= 0.5

    if laugh_score > 0.4 or cough_score > 0.4:
        if laugh_score > cough_score:
            result["laughing"] = laugh_score > 0.5
            result["confidence"] = round(min(1.0, laugh_score), 2)
            result["details"] = "burst pattern with rhythmic quality detected"
        else:
            result["coughing"] = cough_score > 0.5
            result["confidence"] = round(min(1.0, cough_score), 2)
            result["details"] = "short burst with low rhythmic quality"
    else:
        result["details"] = "no laughter or cough patterns detected"

    result["_scores"] = {"laugh": round(laugh_score, 2), "cough": round(cough_score, 2)}


def _detect_bursts(energies: np.ndarray, mean: float, std: float) -> bool:
    if std < 0.001:
        return False
    threshold = mean + std * 0.5
    bursts = energies > threshold
    transitions = np.sum(np.diff(bursts.astype(int)) != 0)
    return transitions >= 3


def _detect_rhythmic(energies: np.ndarray, sr: int, seg_samples: int) -> bool:
    if len(energies) < 10:
        return False

    energies_norm = energies - np.mean(energies)
    corr = np.correlate(energies_norm, energies_norm, mode='full')
    corr = corr[len(corr) // 2:]

    if len(corr) < 4:
        return False

    corr[0] = 0
    if len(corr) < 4:
        return False
    peaks = []
    for i in range(2, len(corr) - 2):
        if corr[i] > corr[i-1] and corr[i] > corr[i+1] and corr[i] > 0.3 * np.max(corr[1:]):
            peaks.append(i)

    return len(peaks) >= 2


def describe(laugh_info: dict) -> str:
    if laugh_info.get("laughing") and laugh_info.get("confidence", 0) > 0.4:
        return "user appears to be laughing"
    if laugh_info.get("coughing") and laugh_info.get("confidence", 0) > 0.4:
        return "user appears to be coughing"
    return None

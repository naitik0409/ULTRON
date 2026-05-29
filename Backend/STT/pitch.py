import numpy as np

MIN_F0 = 60
MAX_F0 = 500


def detect(audio: np.ndarray, sr: int = 16000) -> dict:
    if audio is None or len(audio) < sr // 10:
        return {"f0_mean": 0, "f0_std": 0, "f0_min": 0, "f0_max": 0, "f0_range": 0, "pitch_confidence": 0.0}

    f0_contour = _autocorrelation_pitch(audio, sr)
    f0_values = f0_contour[f0_contour > 0]

    if len(f0_values) == 0:
        return {"f0_mean": 0, "f0_std": 0, "f0_min": 0, "f0_max": 0, "f0_range": 0, "pitch_confidence": 0.0}

    f0_mean = float(np.mean(f0_values))
    f0_std = float(np.std(f0_values))
    f0_min = float(np.min(f0_values))
    f0_max = float(np.max(f0_values))
    f0_range = f0_max - f0_min
    confidence = min(1.0, len(f0_values) / (len(f0_contour) * 0.3))

    return {
        "f0_mean": round(f0_mean, 1),
        "f0_std": round(f0_std, 1),
        "f0_min": round(f0_min, 1),
        "f0_max": round(f0_max, 1),
        "f0_range": round(f0_range, 1),
        "pitch_confidence": round(confidence, 2),
    }


def _autocorrelation_pitch(audio: np.ndarray, sr: int) -> np.ndarray:
    frame_length = int(0.03 * sr)
    hop_length = int(0.01 * sr)
    n_frames = max(1, (len(audio) - frame_length) // hop_length)

    f0_contour = np.zeros(n_frames)

    min_lag = sr // MAX_F0
    max_lag = sr // MIN_F0

    for i in range(n_frames):
        start = i * hop_length
        if start + frame_length > len(audio):
            break
        frame = audio[start:start + frame_length]

        rms = np.sqrt(np.mean(frame ** 2))
        if rms < 0.02:
            continue

        frame = frame - np.mean(frame)
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr) // 2:]

        if len(corr) <= max_lag + 1:
            continue

        corr[:min_lag] = 0
        peak_idx = np.argmax(corr[min_lag:max_lag]) + min_lag

        if peak_idx >= min_lag and corr[peak_idx] > 0.3 * corr[0]:
            f0 = sr / peak_idx
            if MIN_F0 <= f0 <= MAX_F0:
                f0_contour[i] = f0

    return f0_contour


def describe(pitch_info: dict) -> str:
    f0_mean = pitch_info.get("f0_mean", 0)
    f0_range = pitch_info.get("f0_range", 0)
    conf = pitch_info.get("pitch_confidence", 0)

    if conf < 0.2 or f0_mean == 0:
        return "unable to detect voice pitch"

    if f0_mean < 100:
        pitch_desc = "low"
    elif f0_mean < 160:
        pitch_desc = "moderate"
    elif f0_mean < 250:
        pitch_desc = "high"
    else:
        pitch_desc = "very high"

    if f0_range < 30:
        variation = "monotone"
    elif f0_range < 80:
        variation = "moderate variation"
    else:
        variation = "highly varied"

    return f"{pitch_desc} pitched voice with {variation}"

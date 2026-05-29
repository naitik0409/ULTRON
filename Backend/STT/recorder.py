import os
import numpy as np
from datetime import datetime

SAMPLE_RATE = 16000
RECORD_SECONDS = 5
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")

_recorder_available = True
try:
    import sounddevice as sd
except ImportError:
    sd = None
    _recorder_available = False


def is_available() -> bool:
    return _recorder_available and sd is not None


def record_audio(duration: int = RECORD_SECONDS, sr: int = SAMPLE_RATE) -> np.ndarray | None:
    if not is_available():
        return None
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float64')
        sd.wait()
        audio = recording.flatten()
        return audio
    except Exception as e:
        print(f"Recording error: {e}")
        return None


def save_audio(audio: np.ndarray, sr: int = SAMPLE_RATE) -> str | None:
    try:
        import scipy.io.wavfile as wav
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join(DATA_DIR, filename)
        audio_int16 = (audio * 32767).astype(np.int16)
        wav.write(filepath, sr, audio_int16)
        return filepath
    except Exception:
        return None


def get_audio_features(audio: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    if audio is None or len(audio) == 0:
        return {}

    n = len(audio)
    if n == 0:
        return {}

    duration = n / sr
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    energy = np.sum(audio ** 2) / n if n > 0 else 0

    silence_threshold = 0.02
    voice_samples = audio[np.abs(audio) > silence_threshold]
    voice_ratio = len(voice_samples) / n if n > 0 else 0

    zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio)))) / n if n > 0 else 0

    segments = np.array_split(audio, max(10, int(duration * 2)))
    segment_energies = [np.sqrt(np.mean(np.abs(s) ** 2)) for s in segments]
    energy_variance = float(np.var(segment_energies)) if segment_energies else 0

    return {
        "duration": duration,
        "rms": float(rms) if not np.isnan(rms) else 0.0,
        "peak": float(peak) if not np.isnan(peak) else 0.0,
        "energy": float(energy) if not np.isnan(energy) else 0.0,
        "voice_ratio": float(voice_ratio) if not np.isnan(voice_ratio) else 0.0,
        "zero_crossing_rate": float(zero_crossings) if not np.isnan(zero_crossings) else 0.0,
        "energy_variance": energy_variance,
        "sample_rate": sr,
        "samples": n,
    }

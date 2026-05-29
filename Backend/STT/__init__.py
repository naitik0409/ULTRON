import threading
import numpy as np
from .SpeechToText import SpeechRecognition
from . import recorder
from . import pitch as pitch_module
from . import tone as tone_module
from . import emotion as emotion_module
from . import seriousness as seriousness_module
from . import laugh_caugh as laugh_module


class VoiceAnalysis:
    def __init__(self):
        self._last_audio: np.ndarray | None = None
        self._last_features: dict = {}
        self._last_pitch: dict = {}
        self._last_tone: dict = {}
        self._last_emotion: dict = {}
        self._last_seriousness: dict = {}
        self._last_laugh: dict = {}
        self._recording = False
        self._lock = threading.Lock()

    @property
    def has_audio(self) -> bool:
        return self._last_audio is not None

    @property
    def last_pitch(self) -> dict:
        return self._last_pitch

    @property
    def last_tone(self) -> dict:
        return self._last_tone

    @property
    def last_emotion(self) -> dict:
        return self._last_emotion

    @property
    def last_seriousness(self) -> dict:
        return self._last_seriousness

    @property
    def last_laugh(self) -> dict:
        return self._last_laugh

    def analyze(self, audio: np.ndarray | None = None) -> dict:
        if audio is not None:
            self._last_audio = audio

        if self._last_audio is None:
            return {"available": False}

        with self._lock:
            audio = self._last_audio
            features = recorder.get_audio_features(audio)
            pitch_info = pitch_module.detect(audio)
            tone_info = tone_module.analyze(audio, pitch_info=pitch_info, features=features)
            emotion_info = emotion_module.classify(audio, pitch_info=pitch_info, features=features)
            seriousness_info = seriousness_module.analyze(audio, pitch_info=pitch_info, features=features)
            laugh_info = laugh_module.detect(audio, features=features)

            self._last_features = features
            self._last_pitch = pitch_info
            self._last_tone = tone_info
            self._last_emotion = emotion_info
            self._last_seriousness = seriousness_info
            self._last_laugh = laugh_info

        return {
            "available": True,
            "pitch": pitch_info,
            "tone": tone_info,
            "emotion": emotion_info,
            "seriousness": seriousness_info,
            "laugh": laugh_info,
        }

    def analyze_text(self, text: str) -> dict:
        text_lower = text.lower()
        text_features = {}

        excitement_words = {"wow", "amazing", "great", "awesome", "fantastic", "yes", "yeah", "love", "perfect"}
        frustration_words = {"ugh", "damn", "hate", "stupid", "annoying", "frustrating", "seriously"}
        questioning = text.endswith("?")

        text_features["excitement"] = sum(1 for w in text_lower.split() if w in excitement_words)
        text_features["frustration"] = sum(1 for w in text_lower.split() if w in frustration_words)
        text_features["is_question"] = questioning
        text_features["length"] = len(text)

        return text_features

    def get_summary(self) -> str:
        parts = []

        if self._last_emotion.get("emotion") and self._last_emotion.get("confidence", 0) > 0.3:
            parts.append(emotion_module.describe(self._last_emotion))

        if self._last_tone.get("tone") and self._last_tone.get("confidence", 0) > 0.3:
            tone_desc = tone_module.describe(self._last_tone)
            if tone_desc and "unable" not in tone_desc:
                parts.append(tone_desc)

        if self._last_seriousness.get("seriousness", 0.5) > 0.6:
            seriousness_desc = seriousness_module.describe(self._last_seriousness)
            if seriousness_desc and "unable" not in seriousness_desc:
                parts.append(seriousness_desc)

        laugh_desc = laugh_module.describe(self._last_laugh)
        if laugh_desc:
            parts.append(laugh_desc)

        return ". ".join(parts) if parts else ""

    def clear(self):
        with self._lock:
            self._last_audio = None
            self._last_features = {}
            self._last_pitch = {}
            self._last_tone = {}
            self._last_emotion = {}
            self._last_seriousness = {}
            self._last_laugh = {}


voice_analysis = VoiceAnalysis()


def get_voice_analysis() -> VoiceAnalysis:
    return voice_analysis


__all__ = [
    "SpeechRecognition",
    "VoiceAnalysis",
    "voice_analysis",
    "get_voice_analysis",
]

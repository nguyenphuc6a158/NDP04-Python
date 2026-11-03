from threading import Lock

import numpy as np
from faster_whisper import WhisperModel

from app.conversation.domain.errors import EmptyUtterance
from app.conversation.domain.value_objects import AudioClip, Utterance


class WhisperRecognizer:
    def __init__(self, model_size: str) -> None:
        self._model_size = model_size
        self._model: WhisperModel | None = None
        self._lock = Lock()

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            try:
                self._model = WhisperModel(
                    self._model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=8,
                )
            except (OSError, RuntimeError) as exc:
                raise RuntimeError(
                    "Không thể tải model Whisper; kiểm tra kết nối và cấu hình model."
                ) from exc
        return self._model

    def warm_up(self) -> None:
        with self._lock:
            self._ensure_model()

    def transcribe(self, audio: AudioClip) -> Utterance:
        samples = np.frombuffer(audio.pcm, dtype=np.int16).astype(np.float32)
        samples /= 32768.0

        with self._lock:
            model = self._ensure_model()

            try:
                segments, _ = model.transcribe(
                    samples,
                    language="vi",
                    vad_filter=True,
                    beam_size=1,
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
            except (OSError, RuntimeError) as exc:
                raise RuntimeError("Whisper không thể nhận dạng đoạn âm thanh.") from exc

        if not text:
            raise EmptyUtterance()
        return Utterance(text)
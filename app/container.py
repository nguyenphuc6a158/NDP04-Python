import os
from dataclasses import dataclass
from pathlib import Path

from app.conversation.application.handle_voice_input import HandleVoiceInput
from app.conversation.infrastructure.gemini_reply_generator import GeminiReplyGenerator
from app.conversation.infrastructure.piper_synthesizer import PiperSynthesizer
from app.conversation.infrastructure.whisper_recognizer import WhisperRecognizer


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    piper_model_path: Path
    piper_executable: str
    whisper_model: str
    device_api_token: str

    @classmethod
    def from_environment(cls) -> "Settings":
        required = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
            "PIPER_MODEL_PATH": os.getenv("PIPER_MODEL_PATH"),
            "DEVICE_API_TOKEN": os.getenv("DEVICE_API_TOKEN"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Thiếu cấu hình môi trường: " + ", ".join(missing)
            )

        model_path = Path(required["PIPER_MODEL_PATH"] or "").expanduser()
        if not model_path.is_file():
            raise RuntimeError(f"Không tìm thấy model Piper: {model_path}")

        return cls(
            gemini_api_key=required["GEMINI_API_KEY"] or "",
            gemini_model=required["GEMINI_MODEL"] or "",
            piper_model_path=model_path,
            piper_executable=os.getenv("PIPER_EXECUTABLE", "piper"),
            whisper_model=os.getenv("WHISPER_MODEL", "small"),
            device_api_token=required["DEVICE_API_TOKEN"] or "",
        )


def build_voice_handler(settings: Settings) -> HandleVoiceInput:
    return HandleVoiceInput(
        recognizer=WhisperRecognizer(model_size=settings.whisper_model),
        reply_generator=GeminiReplyGenerator(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        ),
        synthesizer=PiperSynthesizer(
            model_path=settings.piper_model_path,
            executable=settings.piper_executable,
        ),
    )

from dataclasses import dataclass
from enum import Enum
from app.conversation.domain.errors import EmptyUtterance

@dataclass(frozen=True)
class ConversationId:
    value: str


@dataclass(frozen=True)
class DeviceId:
    value: str


class Speaker(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Utterance:
    text: str

    def __post_init__(self):
        cleaned = self.text.strip()
        if not cleaned:
            raise EmptyUtterance()
        object.__setattr__(self, "text", cleaned)


@dataclass(frozen=True)
class AudioClip:
    pcm: bytes
    sample_rate: int = 16000

    def __post_init__(self):
        if self.sample_rate <= 0:
            raise ValueError("sample_rate phải > 0")

    @property
    def duration_seconds(self) -> float:
        return len(self.pcm) / 2 / self.sample_rate   # 16-bit mono
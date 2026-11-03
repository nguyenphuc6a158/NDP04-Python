from typing import Protocol

from app.conversation.domain.value_objects import AudioClip, Utterance


class AudioRecognizer(Protocol):
    def transcribe(self, audio: AudioClip) -> Utterance: ...


class ReplyGenerator(Protocol):
    def generate_reply(self, utterance: Utterance) -> Utterance: ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, utterance: Utterance) -> bytes: ...
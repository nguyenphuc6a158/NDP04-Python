from app.conversation.domain.ports import (
    AudioRecognizer,
    ReplyGenerator,
    SpeechSynthesizer,
)
from app.conversation.domain.value_objects import AudioClip


class HandleVoiceInput:
    def __init__(
        self,
        recognizer: AudioRecognizer,
        reply_generator: ReplyGenerator,
        synthesizer: SpeechSynthesizer,
    ) -> None:
        self._recognizer = recognizer
        self._reply_generator = reply_generator
        self._synthesizer = synthesizer

    def handle(self, audio: AudioClip) -> bytes:
        utterance = self._recognizer.transcribe(audio)
        reply = self._reply_generator.generate_reply(utterance)
        return self._synthesizer.synthesize(reply)
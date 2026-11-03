from app.conversation.domain.ports import (
    AudioRecognizer,
    ReplyGenerator,
    SpeechSynthesizer,
)
from app.conversation.domain.value_objects import AudioClip, Utterance


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

    def warm_up(self) -> None:
        warm_up = getattr(self._recognizer, "warm_up", None)
        if warm_up is not None:
            warm_up()

    def handle(self, audio: AudioClip) -> bytes:
        return self.synthesize(self.reply(self.recognize(audio)))

    def recognize(self, audio: AudioClip) -> Utterance:
        return self._recognizer.transcribe(audio)

    def reply(self, utterance: Utterance) -> Utterance:
        return self._reply_generator.generate_reply(utterance)

    def synthesize(self, reply: Utterance) -> bytes:
        return self._synthesizer.synthesize(reply)
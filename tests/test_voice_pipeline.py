import unittest
import wave
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.conversation.application.handle_voice_input import HandleVoiceInput
from app.conversation.domain.value_objects import AudioClip, Utterance
from app.interfaces.ws.device_socket import decode_wav, router as device_router


def make_wav(sample_rate: int = 16_000) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


class VoicePipelineTests(unittest.TestCase):
    def test_decodes_supported_wav_to_pcm(self) -> None:
        clip = decode_wav(make_wav())

        self.assertEqual(clip, AudioClip(pcm=b"\x00\x00" * 160, sample_rate=16_000))

    def test_rejects_wav_with_unsupported_sample_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "sample rate 16000 Hz"):
            decode_wav(make_wav(sample_rate=8_000))

    def test_pipeline_runs_recognition_reply_and_synthesis_in_order(self) -> None:
        calls: list[str] = []

        class Recognizer:
            def transcribe(self, audio: AudioClip) -> Utterance:
                if audio.sample_rate != 16_000:
                    raise AssertionError("Unexpected sample rate")
                calls.append("recognize")
                return Utterance("xin chào")

        class ReplyGenerator:
            def generate_reply(self, utterance: Utterance) -> Utterance:
                calls.append(f"reply:{utterance.text}")
                return Utterance("chào bạn")

        class Synthesizer:
            def synthesize(self, utterance: Utterance) -> bytes:
                calls.append(f"synthesize:{utterance.text}")
                return b"wav-response"

        handler = HandleVoiceInput(
            Recognizer(),
            ReplyGenerator(),
            Synthesizer(),
        )

        result = handler.handle(AudioClip(pcm=b"\x00\x00" * 10))

        self.assertEqual(result, b"wav-response")
        self.assertEqual(
            calls,
            ["recognize", "reply:xin chào", "synthesize:chào bạn"],
        )

    def test_websocket_returns_synthesized_audio(self) -> None:
        calls: list[str] = []

        class Recognizer:
            def transcribe(self, audio: AudioClip) -> Utterance:
                calls.append(f"recognize:{audio.sample_rate}")
                return Utterance("xin chào")

        class ReplyGenerator:
            def generate_reply(self, utterance: Utterance) -> Utterance:
                calls.append(f"reply:{utterance.text}")
                return Utterance("chào bạn")

        class Synthesizer:
            def synthesize(self, utterance: Utterance) -> bytes:
                calls.append(f"synthesize:{utterance.text}")
                return b"reply-wav"

        application = FastAPI()
        application.state.voice_handler = HandleVoiceInput(
            Recognizer(),
            ReplyGenerator(),
            Synthesizer(),
        )
        application.state.device_api_token = "test-token"
        application.include_router(device_router)

        with TestClient(application) as client:
            with client.websocket_connect(
                "/ws/device",
                headers={"Authorization": "Bearer test-token"},
            ) as websocket:
                websocket.send_bytes(make_wav())
                self.assertEqual(websocket.receive_bytes(), b"reply-wav")

        self.assertEqual(
            calls,
            ["recognize:16000", "reply:xin chào", "synthesize:chào bạn"],
        )


if __name__ == "__main__":
    unittest.main()

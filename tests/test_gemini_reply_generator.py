import unittest
from types import SimpleNamespace
from unittest.mock import patch

from google.genai import errors

from app.conversation.domain.value_objects import Utterance
from app.conversation.infrastructure.gemini_reply_generator import (
    SYSTEM_INSTRUCTION,
    GeminiReplyGenerator,
)


class GeminiReplyGeneratorTests(unittest.TestCase):
    @patch("app.conversation.infrastructure.gemini_reply_generator.genai.Client")
    def test_sends_utterance_to_generate_content(self, gemini_client: object) -> None:
        client = gemini_client.return_value
        client.models.generate_content.return_value = SimpleNamespace(text=" Chào bạn! ")
        generator = GeminiReplyGenerator(api_key="test-key", model="test-model")

        reply = generator.generate_reply(Utterance("Xin chào"))

        self.assertEqual(reply, Utterance("Chào bạn!"))
        gemini_client.assert_called_once()
        self.assertEqual(gemini_client.call_args.kwargs["api_key"], "test-key")
        retry = gemini_client.call_args.kwargs["http_options"].retry_options
        self.assertIn(503, retry.http_status_codes)
        call = client.models.generate_content.call_args
        self.assertEqual(call.kwargs["model"], "test-model")
        self.assertEqual(call.kwargs["contents"], "Xin chào")
        self.assertEqual(
            call.kwargs["config"].system_instruction, SYSTEM_INSTRUCTION
        )

    @patch("app.conversation.infrastructure.gemini_reply_generator.genai.Client")
    def test_wraps_api_error_keeping_original_cause(self, gemini_client: object) -> None:
        api_error = errors.APIError(429, {"error": {"message": "quota exceeded"}})
        gemini_client.return_value.models.generate_content.side_effect = api_error
        generator = GeminiReplyGenerator(api_key="test-key", model="test-model")

        with self.assertRaises(RuntimeError) as context:
            generator.generate_reply(Utterance("Xin chào"))

        self.assertIs(context.exception.__cause__, api_error)

    @patch("app.conversation.infrastructure.gemini_reply_generator.genai.Client")
    def test_rejects_empty_response(self, gemini_client: object) -> None:
        gemini_client.return_value.models.generate_content.return_value = SimpleNamespace(
            text=None
        )
        generator = GeminiReplyGenerator(api_key="test-key", model="test-model")

        with self.assertRaisesRegex(RuntimeError, "không trả về nội dung"):
            generator.generate_reply(Utterance("Xin chào"))


if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.conversation.domain.value_objects import Utterance
from app.conversation.infrastructure.openai_reply_generator import OpenAIReplyGenerator


class OpenAIReplyGeneratorTests(unittest.TestCase):
    @patch("app.conversation.infrastructure.openai_reply_generator.OpenAI")
    def test_sends_utterance_to_responses_api(self, openai_client: object) -> None:
        client = openai_client.return_value
        client.responses.create.return_value = SimpleNamespace(
            output_text="Chào bạn!"
        )
        generator = OpenAIReplyGenerator(api_key="test-key", model="test-model")

        reply = generator.generate_reply(Utterance("Xin chào"))

        self.assertEqual(reply, Utterance("Chào bạn!"))
        openai_client.assert_called_once_with(api_key="test-key")
        client.responses.create.assert_called_once_with(
            model="test-model",
            instructions=(
                "Bạn là trợ lý giọng nói. Hãy trả lời bằng tiếng Việt, "
                "ngắn gọn và tự nhiên."
            ),
            input="Xin chào",
        )


if __name__ == "__main__":
    unittest.main()

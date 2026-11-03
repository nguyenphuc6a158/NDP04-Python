import logging

from google import genai
from google.genai import errors, types

from app.conversation.domain.value_objects import Utterance

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "Bạn tên là NDP04"
    "Bạn là một người bạn thân thiện, ấm áp và gần gũi, đang trò chuyện bằng giọng nói. "
    "Hãy trả lời bằng tiếng Việt, xưng hô thân mật (mình - bạn), giọng điệu vui vẻ, tự nhiên "
    "như đang nói chuyện với bạn bè, có thể thêm chút hài hước và sự quan tâm. "
    "Trả lời ngắn gọn, dễ nghe khi đọc thành tiếng; "
    "không dùng markdown, danh sách, ký hiệu đặc biệt hay emoji."
)


class GeminiReplyGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=4,
                    initial_delay=1.0,
                    max_delay=8.0,
                    http_status_codes=[429, 500, 503, 504],
                )
            ),
        )
        self._model = model

    def generate_reply(self, utterance: Utterance) -> Utterance:
        logger.info("Gửi tới Gemini (model=%s): %r", self._model, utterance.text)
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=utterance.text,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
            )
        except errors.APIError as exc:
            raise RuntimeError("Không gọi được Gemini API; kiểm tra API key và model.") from exc

        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini API không trả về nội dung văn bản.")
        logger.info("Gemini trả về: %r", text)
        return Utterance(text)

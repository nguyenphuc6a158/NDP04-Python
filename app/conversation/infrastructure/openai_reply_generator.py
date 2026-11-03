from openai import OpenAI, OpenAIError

from app.conversation.domain.value_objects import Utterance


class OpenAIReplyGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_reply(self, utterance: Utterance) -> Utterance:
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions="Bạn là trợ lý giọng nói. Hãy trả lời bằng tiếng Việt, ngắn gọn và tự nhiên.",
                input=utterance.text,
            )
        except OpenAIError as exc:
            raise RuntimeError("Không gọi được OpenAI API; kiểm tra API key và model.") from exc

        text = response.output_text.strip()
        if not text:
            raise RuntimeError("OpenAI API không trả về nội dung văn bản.")
        return Utterance(text)
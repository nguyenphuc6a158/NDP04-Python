import hmac
import logging
import subprocess
import wave
from io import BytesIO

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.conversation.application.handle_voice_input import HandleVoiceInput
from app.conversation.domain.errors import DomainError
from app.conversation.domain.value_objects import AudioClip


logger = logging.getLogger(__name__)
router = APIRouter()
MAX_AUDIO_BYTES = 8 * 1024 * 1024
SAMPLE_RATE = 16_000


def decode_wav(payload: bytes) -> AudioClip:
    if not payload:
        raise ValueError("Gói âm thanh rỗng.")
    if len(payload) > MAX_AUDIO_BYTES:
        raise ValueError("File WAV vượt quá giới hạn 8 MB.")

    try:
        with wave.open(BytesIO(payload), "rb") as wav_file:
            if (
                wav_file.getnchannels() != 1
                or wav_file.getsampwidth() != 2
                or wav_file.getframerate() != SAMPLE_RATE
                or wav_file.getcomptype() != "NONE"
            ):
                raise ValueError(
                    "WAV phải là PCM mono 16-bit, sample rate 16000 Hz."
                )
            pcm = wav_file.readframes(wav_file.getnframes())
    except (EOFError, OSError, wave.Error) as exc:
        raise ValueError("Dữ liệu gửi lên không phải file WAV hợp lệ.") from exc

    if not pcm:
        raise ValueError("File WAV không có dữ liệu âm thanh.")
    return AudioClip(pcm=pcm, sample_rate=SAMPLE_RATE)


def describe_error(exc: BaseException) -> list[str]:
    details: list[str] = []
    current: BaseException | None = exc
    while current is not None:
        line = f"{type(current).__name__}: {current}"
        if isinstance(current, subprocess.CalledProcessError) and current.stderr:
            line += f" | stderr: {str(current.stderr).strip()[-1500:]}"
        details.append(line)
        current = current.__cause__
    return details


@router.websocket("/ws/device")
async def device_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    expected_token: str = websocket.app.state.device_api_token
    authorization = websocket.headers.get("authorization", "")
    supplied_token = (
        authorization.removeprefix("Bearer ").strip()
        if authorization.startswith("Bearer ")
        else ""
    )
    if not hmac.compare_digest(supplied_token, expected_token):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    handler: HandleVoiceInput = websocket.app.state.voice_handler
    while True:
        try:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return

            payload = message.get("bytes")
            if payload is None:
                await websocket.send_json(
                    {"type": "error", "message": "Hãy gửi một file WAV dưới dạng binary."}
                )
                continue

            try:
                audio = decode_wav(payload)
                utterance = await run_in_threadpool(handler.recognize, audio)
                await websocket.send_json(
                    {"type": "transcript", "text": utterance.text}
                )
                reply = await run_in_threadpool(handler.reply, utterance)
                await websocket.send_json({"type": "reply", "text": reply.text})
                response_audio = await run_in_threadpool(handler.synthesize, reply)
            except (DomainError, ValueError) as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                continue
            except Exception as exc:
                logger.exception("Xử lý lượt thoại thất bại")
                await websocket.send_json(
                    {"type": "error", "message": " <- ".join(describe_error(exc))}
                )
                continue

            await websocket.send_bytes(response_audio)
        except WebSocketDisconnect:
            return
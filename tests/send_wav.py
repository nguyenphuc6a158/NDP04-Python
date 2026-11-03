import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed


async def send_wav(url: str, token: str, wav_path: Path, output_path: Path, timeout: float) -> int:
    payload = wav_path.read_bytes()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with connect(
            url,
            additional_headers=headers,
            max_size=16 * 1024 * 1024,
        ) as websocket:
            await websocket.send(payload)
            print(f"Đã gửi {len(payload)} byte, đang chờ phản hồi...")
            while True:
                reply = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                if isinstance(reply, bytes):
                    break
                message = json.loads(reply)
                if message.get("type") == "transcript":
                    print(f"Nội dung nhận dạng: {message['text']}")
                    continue
                if message.get("type") == "reply":
                    print(f"Gemini trả lời: {message['text']}")
                    continue
                print(f"Máy chủ báo lỗi: {reply}", file=sys.stderr)
                return 1
    except ConnectionClosed as exc:
        print(f"Máy chủ đóng kết nối: {exc}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"Quá {timeout:.0f} giây mà chưa có phản hồi.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Không kết nối được tới {url}: {exc}", file=sys.stderr)
        return 1

    if isinstance(reply, str):
        print(f"Máy chủ báo lỗi: {reply}", file=sys.stderr)
        return 1

    output_path.write_bytes(reply)
    print(f"Đã lưu {len(reply)} byte vào {output_path}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Gửi file WAV (PCM mono 16-bit 16 kHz) tới /ws/device và lưu WAV phản hồi."
    )
    parser.add_argument("wav", type=Path, help="File WAV cần gửi")
    parser.add_argument("-o", "--output", type=Path, default=Path("reply.wav"))
    parser.add_argument("--url", default="ws://127.0.0.1:8000/ws/device")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    token = os.getenv("DEVICE_API_TOKEN")
    if not token:
        print("Thiếu DEVICE_API_TOKEN trong .env.", file=sys.stderr)
        return 1
    if not args.wav.is_file():
        print(f"Không tìm thấy file: {args.wav}", file=sys.stderr)
        return 1

    return asyncio.run(send_wav(args.url, token, args.wav, args.output, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())

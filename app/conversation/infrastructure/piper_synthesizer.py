import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from app.conversation.domain.value_objects import Utterance


class PiperSynthesizer:
    def __init__(self, model_path: Path, executable: str = "piper") -> None:
        self._model_path = model_path
        self._executable = executable

    def synthesize(self, utterance: Utterance) -> bytes:
        with TemporaryDirectory(prefix="ndp04-piper-") as directory:
            output_path = Path(directory) / "reply.wav"
            try:
                subprocess.run(
                    [
                        self._executable,
                        "--model",
                        str(self._model_path),
                        "--output_file",
                        str(output_path),
                    ],
                    input=utterance.text,
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=45,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "Không tìm thấy chương trình Piper; kiểm tra PIPER_EXECUTABLE."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Piper tổng hợp giọng nói quá thời gian.") from exc
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    "Piper không thể tạo âm thanh; kiểm tra model giọng nói."
                ) from exc

            if not output_path.is_file():
                raise RuntimeError("Piper kết thúc nhưng không tạo file âm thanh.")
            return output_path.read_bytes()
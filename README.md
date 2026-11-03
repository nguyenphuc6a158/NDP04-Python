# NDP04 voice server

Luồng thoại hiện tại:

1. Thiết bị kết nối `WebSocket /ws/device` và gửi một file WAV dạng binary.
2. Máy chủ dùng Whisper chạy cục bộ để nhận dạng tiếng Việt.
3. Văn bản được gửi tới OpenAI bằng API key chỉ lưu trên máy chủ.
4. Piper chạy cục bộ để tạo WAV và máy chủ gửi WAV đó về thiết bị.

## Cấu hình trên Windows

Yêu cầu Python 3.10 trở lên.

1. Tạo môi trường và cài dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Sao chép `.env.example` thành `.env`, sau đó điền `OPENAI_API_KEY`,
   `OPENAI_MODEL`, `DEVICE_API_TOKEN` và đường dẫn model Piper `.onnx`.
   Không gửi API key cho thiết bị và không đưa file `.env` lên Git.
3. Cài/tải model giọng Piper tiếng Việt tương thích với bản `piper-tts` đã cài.
   Model ONNX và file cấu hình `.onnx.json` tương ứng cần nằm cạnh nhau.
4. Chạy máy chủ từ thư mục gốc của dự án:

   ```powershell
   fastapi dev app/main.py
   ```

Khi cần cho thiết bị khác trong mạng kết nối, chạy:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Whisper tải model theo giá trị `WHISPER_MODEL` ở lần sử dụng đầu tiên; máy chủ
cần Internet trong lần đó. Có thể đổi thành `tiny` để thử nhanh hoặc `small`
để ưu tiên chất lượng, tùy tài nguyên máy.

## Giao thức thiết bị

- Kết nối `ws://<địa-chỉ-máy-chủ>:8000/ws/device`.
- Gửi header `Authorization: Bearer <DEVICE_API_TOKEN>`.
- Mỗi lượt gửi đúng một WAV: PCM không nén, mono, signed 16-bit, 16 kHz.
- Máy chủ trả một message binary là WAV do Piper tạo. Thiết bị nên đọc sample
  rate từ header WAV vì sample rate đầu ra phụ thuộc model Piper.
- Nếu có lỗi, máy chủ trả message JSON dạng
  `{"type":"error","message":"..."}` thay vì binary.

Kiểm tra tình trạng máy chủ tại `GET /get/health`. Test nhanh phần giải mã WAV
và luồng xử lý:

```powershell
python -m unittest discover -s tests
```

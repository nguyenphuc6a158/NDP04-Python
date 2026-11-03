# NDP04 voice server

Luồng thoại hiện tại:

1. Thiết bị kết nối `WebSocket /ws/device` và gửi một file WAV dạng binary.
2. Máy chủ dùng Whisper chạy cục bộ để nhận dạng tiếng Việt.
3. Văn bản được gửi tới Gemini bằng API key chỉ lưu trên máy chủ.
4. Piper chạy cục bộ để tạo WAV và máy chủ gửi WAV đó về thiết bị.

## Cấu hình trên Windows

Yêu cầu Python 3.10 trở lên.

1. Tạo môi trường và cài dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Sao chép `.env.example` thành `.env`, sau đó điền `GEMINI_API_KEY`,
   `GEMINI_MODEL` và `DEVICE_API_TOKEN`. Lấy API key miễn phí tại
   https://aistudio.google.com/api-keys. Gói miễn phí chỉ áp dụng cho một số
   model (ví dụ `gemini-3.8-flash`) và có giới hạn số request. Không gửi API
   key cho thiết bị và không đưa file `.env` lên Git.
3. Đặt model Piper tiếng Việt và file cấu hình `.onnx.json` tương ứng cạnh
   nhau trong `app/models_piper`. Mặc định `PIPER_MODEL_PATH` trỏ tới
   `app/models_piper/vi_VN-vais1000-medium.onnx`; nếu dùng model khác, cập nhật
   biến này trong `.env`.
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
- Máy chủ gửi thêm message JSON `{"type":"reply","text":"..."}` chứa câu trả lời
  của Gemini, trước khi Piper tạo âm thanh.
- Máy chủ trả một message binary là WAV do Piper tạo. Thiết bị nên đọc sample
  rate từ header WAV vì sample rate đầu ra phụ thuộc model Piper.
- Ngay sau khi nhận dạng xong, trước khi gọi Gemini, máy chủ gửi một message
  JSON `{"type":"transcript","text":"..."}` chứa nội dung nhận dạng được.
  Thiết bị cần đọc message này rồi chờ tiếp message binary.
- Nếu có lỗi, máy chủ trả message JSON dạng
  `{"type":"error","message":"..."}` thay vì binary. Với lỗi xử lý âm thanh,
  `message` là lỗi gốc của từng tầng (nối bằng ` <- `), kèm stderr của Piper
  nếu có. Chi tiết này phục vụ debug nên không nên mở máy chủ ra Internet.

Kiểm tra tình trạng máy chủ tại `GET /get/health`. Test nhanh phần giải mã WAV
và luồng xử lý:

```powershell
python -m unittest discover -s tests
```

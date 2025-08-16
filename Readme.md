# Prompt Paster

Ứng dụng hỗ trợ paste prompt tự động cho Midjourney/ChatGPT và các công cụ AI khác.

## Yêu cầu hệ thống
- Python 3.8 trở lên
- Windows 7/10/11

## Cài đặt

1. Tạo môi trường ảo:
```bash
python -m venv .venv
```

2. Kích hoạt môi trường ảo:
```bash
# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. Cài đặt các thư viện cần thiết:
```bash
python install_requirements.py
```

## Chạy ứng dụng

```bash
python main.py
```

## Tính năng chính

- Quản lý danh sách prompt theo thư mục
- Paste tự động với hotkey (mặc định Ctrl+B)
- Theo dõi và di chuyển file ảnh tự động
- Dashboard thống kê hoạt động
- Hỗ trợ import/export CSV

## Ghi chú

- Ứng dụng sẽ tạo thư mục dữ liệu mặc định tại `~/PromptPaster_Data`
- Có thể thay đổi đường dẫn trong phần Cài đặt
- Hỗ trợ theo dõi tự động thư mục Downloads
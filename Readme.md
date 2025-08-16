# Prompt Paster v1.0

![Prompt Paster Logo](docs/images/logo.png)

Ứng dụng hỗ trợ paste prompt tự động cho Midjourney/ChatGPT và các công cụ AI khác, giúp tối ưu hóa quy trình làm việc với AI.

## Tải về và Cài đặt

### Phiên bản thực thi (Khuyến nghị)

1. Tải file cài đặt từ [Releases](https://github.com/tech-tnitechsolve/Prompt_Paster/releases) mới nhất
2. Chạy file PromptPaster_Setup.exe
3. Làm theo hướng dẫn cài đặt

### Cài đặt từ mã nguồn (Cho nhà phát triển)

#### Yêu cầu hệ thống
- Python 3.8 trở lên
- Windows 7/10/11

1. Clone repository:
```bash
git clone https://github.com/tech-tnitechsolve/Prompt_Paster.git
cd Prompt_Paster
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Cài đặt các thư viện cần thiết:
```bash
python install_requirements.py
```

4. Chạy ứng dụng:
```bash
python main.py
```

## Tính năng chính

### 1. Quản lý Prompt
- Tổ chức prompt theo thư mục và danh sách
- Hỗ trợ import/export CSV
- Tự động lưu tiến trình paste

### 2. Paste Tự động
- Hotkey tùy chỉnh (mặc định Ctrl+B)
- Hỗ trợ paste nhanh với shortcut
- Tự động chuyển prompt tiếp theo

### 3. Quản lý File Ảnh
- Theo dõi thư mục Downloads
- Tự động di chuyển ảnh đến thư mục lưu trữ
- Phân loại và tổ chức file

### 4. Thống kê và Báo cáo
- Dashboard theo dõi hoạt động
- Thống kê số lượng prompt đã sử dụng
- Lịch sử hoạt động chi tiết

## Cấu hình và Tùy chỉnh

### Thư mục dữ liệu
- Mặc định: `~/PromptPaster_Data`
- Có thể thay đổi trong phần Cài đặt

### Hotkey
- Mặc định: `Ctrl+B`
- Tùy chỉnh trong phần Cài đặt
- Hỗ trợ các tổ hợp phím phổ biến

### Tự động hóa
- Theo dõi thư mục Downloads
- Tự động di chuyển file ảnh
- Cấu hình qua giao diện

## Đóng góp

Chúng tôi luôn chào đón mọi đóng góp! Nếu bạn muốn cải thiện Prompt Paster:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## Giấy phép

Dự án này được phát hành dưới giấy phép MIT. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## Hỗ trợ

Nếu bạn gặp vấn đề hoặc có câu hỏi:
- Tạo issue trên [GitHub](https://github.com/tech-tnitechsolve/Prompt_Paster/issues)
- Email: support@tnitechsolve.com

## Tác giả

**TNI Tech Solutions** - [GitHub](https://github.com/tech-tnitechsolve)

## Ghi nhận đóng góp

Cảm ơn tất cả các contributor đã giúp phát triển dự án này!
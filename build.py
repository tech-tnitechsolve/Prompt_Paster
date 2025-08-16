# -*- coding: utf-8 -*-
# build.py

import subprocess
import sys
import os

# --- Cấu hình ---
APP_NAME = "Prompt Paster"
MAIN_SCRIPT = "main.py"
LOGO_DIR = "logos"
ICON_FILE = os.path.join(LOGO_DIR, "logo.ico")
# -----------------

def build_executable():
    """
    Chạy PyInstaller để đóng gói ứng dụng.
    Yêu cầu: PyInstaller và các thư viện khác phải được cài đặt sẵn trong môi trường ảo.
    """
    if not os.path.exists(MAIN_SCRIPT):
        print(f"!!! Lỗi: Không tìm thấy file chính '{MAIN_SCRIPT}'. !!!")
        sys.exit(1)
        
    if not os.path.exists(ICON_FILE):
        print(f"--- Cảnh báo: Không tìm thấy file logo tại '{ICON_FILE}'. Bỏ qua icon. ---")

    print(f">>> Bắt đầu quá trình đóng gói '{APP_NAME}'...")

    # Sử dụng sys.executable để đảm bảo PyInstaller được chạy từ môi trường ảo hiện tại
    command = [
        sys.executable,
        '-m', 'PyInstaller',
        '--name', APP_NAME,
        '--onefile',
        '--windowed',
        '--hidden-import', 'pynput',
        '--hidden-import', 'six',
        '--clean',
        MAIN_SCRIPT
    ]
    
    # Chỉ thêm icon vào lệnh nếu file tồn tại
    if os.path.exists(ICON_FILE):
        command.extend(['--icon', ICON_FILE])

    print(f"--- Đang chạy lệnh: {' '.join(command)} ---")

    try:
        subprocess.check_call(command)
        print("\n>>> HOÀN TẤT! <<<")
        print(f"--- File '{APP_NAME}.exe' đã được tạo trong thư mục 'dist'. ---")
    except subprocess.CalledProcessError as e:
        print(f"\n!!! Lỗi trong quá trình đóng gói: {e} !!!")
    except FileNotFoundError:
        print("\n!!! Lỗi: Không tìm thấy PyInstaller. Vui lòng chạy 'pip install pyinstaller' trong môi trường ảo của bạn. !!!")


if __name__ == "__main__":
    build_executable()

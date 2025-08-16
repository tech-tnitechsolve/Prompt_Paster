# -*- coding: utf-8 -*-
# install_requirements.py

import subprocess
import sys

def install_packages(packages):
    """
    Sử dụng pip để cài đặt một danh sách các thư viện Python.

    Args:
        packages (list): Danh sách các tên thư viện cần cài đặt.
    """
    python_executable = sys.executable
    
    for package in packages:
        try:
            print(f"--- Đang cài đặt {package}... ---")
            subprocess.check_call([python_executable, "-m", "pip", "install", package])
            print(f"--- Cài đặt thành công {package} ---\n")
        except subprocess.CalledProcessError as e:
            print(f"!!! Lỗi khi cài đặt {package}: {e} !!!")
            print("Vui lòng thử cài đặt thủ công bằng lệnh:")
            print(f'"{python_executable}" -m pip install {package}')
            sys.exit(1)

def main():
    """
    Hàm chính để xác định và cài đặt các thư viện cần thiết.
    """
    required_packages = []
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            for line in f:
                pkg = line.strip()
                if pkg and not pkg.startswith("#"):
                    required_packages.append(pkg)
    except FileNotFoundError:
        # Danh sách dự phòng nếu không có file requirements.txt
        required_packages = [
            "PyQt6",
            "pynput",
            "watchdog"  # Thêm thư viện để theo dõi file
        ]

    if not required_packages:
        print("Không tìm thấy thư viện nào để cài đặt.")
        return

    print(">>> Bắt đầu quá trình cài đặt các thư viện cần thiết cho dự án...")
    install_packages(required_packages)
    print(">>> Hoàn tất! Tất cả các thư viện đã được cài đặt thành công.")

if __name__ == "__main__":
    main()

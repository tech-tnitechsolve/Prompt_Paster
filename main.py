# -*- coding: utf-8 -*-
# main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import các lớp từ các file khác
from core import CoreLogic
from ui import MainWindow

def main():
    """
    Điểm khởi đầu của ứng dụng.
    Khởi tạo Core, UI và liên kết chúng với nhau.
    """
    app = QApplication(sys.argv)

    # 1. Khởi tạo Core Logic
    core = CoreLogic()

    # 2. Khởi tạo Main Window và truyền core vào
    window = MainWindow(core)

    # 3. Tải dữ liệu ban đầu và khôi phục trạng thái
    core.load_all_lists()
    last_path = core.load_state()
    
    # TỐI ƯU HÓA: Sử dụng hàm tiện ích trong MainWindow để chọn lại item cuối cùng.
    # Logic này giờ đây gọn gàng và được đóng gói trong lớp UI.
    if last_path:
        window.select_item_by_path(last_path)


    # 4. Hiển thị cửa sổ và chạy ứng dụng
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

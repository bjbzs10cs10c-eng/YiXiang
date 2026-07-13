"""易象 - 周易六爻占卜桌面应用"""

import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.database import init_db


def main():
    # 初始化数据库
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("易象")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

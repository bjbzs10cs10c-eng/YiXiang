"""主窗口 - 左侧导航 + 右侧内容区"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QPushButton, QStackedWidget,
                                QLabel, QButtonGroup)
from PySide6.QtCore import Qt
from ui.styles import STYLE_SHEET
from ui.home_page import HomePage
from ui.divination_page import DivinationPage
from ui.library_page import LibraryPage
from ui.history_page import HistoryPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("易象 - 周易六爻占卜")
        self.resize(900, 650)
        self.setStyleSheet(STYLE_SHEET)

        # 中央部件
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setFixedWidth(160)
        nav_widget.setStyleSheet("background-color: #ebe5d8; border-right: 1px solid #d5cdb8;")
        self.nav_layout = QVBoxLayout(nav_widget)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)
        self.nav_layout.setSpacing(8)

        title = QLabel("易象")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c2c2c; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_layout.addWidget(title)

        subtitle = QLabel("周易六爻占卜")
        subtitle.setStyleSheet("font-size: 12px; color: #888; padding-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_layout.addWidget(subtitle)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        # 右侧内容区
        self.pages = QStackedWidget()

        # 首页
        self.home_page = HomePage()
        self.home_page.start_divination_clicked.connect(self.go_to_divination)
        self.add_nav_button("开始占卜", 0)
        self.pages.addWidget(self.home_page)

        # 占卜页
        self.divination_page = DivinationPage()
        self.divination_page.divination_done.connect(self.on_divination_done)
        self.add_nav_button("起卦", 1)
        self.pages.addWidget(self.divination_page)

        # 卦库
        self.library_page = LibraryPage()
        self.add_nav_button("周易查询", 2)
        self.pages.addWidget(self.library_page)

        # 历史
        self.history_page = HistoryPage()
        self.add_nav_button("历史记录", 3)
        self.pages.addWidget(self.history_page)

        self.nav_layout.addStretch()

        layout.addWidget(nav_widget)
        layout.addWidget(self.pages)

        self.setCentralWidget(central)

        # 默认选中首页
        self.nav_group.button(0).setChecked(True)

    def add_nav_button(self, text, index):
        """添加导航按钮"""
        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nav_group.addButton(btn, index)
        btn.clicked.connect(lambda: self.pages.setCurrentIndex(index))
        self.nav_layout.addWidget(btn)

    def go_to_divination(self):
        """从首页跳转到占卜页"""
        self.nav_group.button(1).setChecked(True)
        self.pages.setCurrentIndex(1)
        self.divination_page.start()

    def on_divination_done(self, result):
        """占卜完成后跳转到结果页"""
        self.divination_page.show_result(result)

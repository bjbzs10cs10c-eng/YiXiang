"""首页 - 欢迎页面"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, Qt


class HomePage(QWidget):
    start_divination_clicked = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        layout.addSpacerItem(QSpacerItem(0, 80, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        title = QLabel("易 象")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #2c2c2c; letter-spacing: 20px;")
        layout.addWidget(title)

        subtitle = QLabel("周易六爻占卜 · 三枚铜钱法")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(subtitle)

        layout.addSpacing(40)

        btn = QPushButton("开始占卜")
        btn.setFixedSize(160, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.start_divination_clicked)
        # 居中按钮
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        layout.addSpacerItem(QSpacerItem(0, 80, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

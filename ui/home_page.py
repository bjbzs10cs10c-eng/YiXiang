"""首页 - 欢迎页面

布局（UIDesign.md 第六节）：
- Logo 区：☰☰ + 易象 + YiXiang
- 副标题：天行健，君子以自强不息
- 主按钮：开始一次占卜
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, Qt
from ui.styles import COLOR_INK, COLOR_SLATE, COLOR_CINNABAR, COLOR_PAPER


class HomePage(QWidget):
    start_divination_clicked = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        layout.addSpacerItem(QSpacerItem(0, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Logo 符号
        logo = QLabel("☰☰")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 56px; color: {}; letter-spacing: 12px;".format(COLOR_INK))
        layout.addWidget(logo)

        # 主标题
        title = QLabel("易 象")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 56px; font-weight: bold; color: {}; font-family: SimSun, 宋体, serif; letter-spacing: 24px; padding: 10px 0 0 24px;".format(COLOR_INK)
        )
        layout.addWidget(title)

        # 英文副标题
        en_subtitle = QLabel("YiXiang")
        en_subtitle.setObjectName("subtitleLabel")
        en_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        en_subtitle.setStyleSheet("font-size: 13px; color: {}; letter-spacing: 4px; padding-top: 4px;".format(COLOR_SLATE))
        layout.addWidget(en_subtitle)

        # 诗句副标题
        poem = QLabel("天行健，君子以自强不息")
        poem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poem.setStyleSheet(
            "font-size: 16px; color: {}; font-family: SimSun, 宋体, serif; padding: 8px 0;".format(COLOR_SLATE)
        )
        layout.addWidget(poem)

        layout.addSpacing(40)

        # 主按钮
        btn = QPushButton("开始一次占卜")
        btn.setFixedSize(200, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.start_divination_clicked)
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        layout.addSpacerItem(QSpacerItem(0, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

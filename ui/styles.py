"""全局样式 - 新中式极简（古籍感）

配色规范（UIDesign.md）：
- 宣纸白 #F7F3EA  背景
- 墨黑   #2B2B2B  正文
- 朱砂红 #B83A2E  强调（动爻、按钮）
- 青灰   #718096  辅助
- 金色   #C9A227  特殊提示（少量）
"""

# 色彩常量（供代码内引用）
COLOR_PAPER = "#F7F3EA"      # 宣纸白
COLOR_INK = "#2B2B2B"        # 墨黑
COLOR_CINNABAR = "#B83A2E"   # 朱砂红
COLOR_SLATE = "#718096"      # 青灰
COLOR_GOLD = "#C9A227"       # 金色
COLOR_CARD_BG = "#FFFBF2"    # 卡片背景（略浅于主背景）
COLOR_BORDER = "#E5DCC8"     # 边框色
COLOR_NAV_BG = "#EFE8D8"     # 导航栏背景（浅米色）

# 字体（系统字体，无需打包）
FONT_TITLE = '"SimSun", "宋体", "Noto Serif CJK SC", serif'
FONT_BODY = '"SimHei", "黑体", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif'


STYLE_SHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_PAPER};
    font-family: {FONT_BODY};
    color: {COLOR_INK};
}}

QLabel {{
    color: {COLOR_INK};
    font-family: {FONT_BODY};
}}

QLabel#titleLabel {{
    font-size: 48px;
    font-weight: bold;
    color: {COLOR_INK};
    font-family: {FONT_TITLE};
    letter-spacing: 8px;
    padding: 10px;
}}

QLabel#subtitleLabel {{
    font-size: 14px;
    color: {COLOR_SLATE};
    font-family: {FONT_BODY};
}}

QLabel#hexagramNameLabel {{
    font-size: 24px;
    font-weight: bold;
    color: {COLOR_INK};
    font-family: {FONT_TITLE};
}}

QLabel#sectionLabel {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_INK};
    font-family: {FONT_TITLE};
    border-bottom: 2px solid {COLOR_CINNABAR};
    padding-bottom: 6px;
    margin-bottom: 4px;
}}

QLabel#readingLabel {{
    font-size: 16px;
    color: {COLOR_INK};
    padding: 12px;
    background-color: {COLOR_CARD_BG};
    border-left: 4px solid {COLOR_CINNABAR};
    border-radius: 4px;
}}

QPushButton {{
    background-color: {COLOR_CINNABAR};
    color: {COLOR_PAPER};
    border: none;
    padding: 10px 24px;
    font-size: 15px;
    border-radius: 8px;
    font-family: {FONT_BODY};
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: #A02B22;
}}

QPushButton:pressed {{
    background-color: #8B2319;
}}

QPushButton:disabled {{
    background-color: {COLOR_SLATE};
    color: #D5D5D5;
}}

QPushButton#navButton {{
    background-color: transparent;
    color: {COLOR_INK};
    border: none;
    border-left: 3px solid transparent;
    font-size: 15px;
    padding: 12px 20px;
    text-align: left;
    border-radius: 0;
    font-family: {FONT_BODY};
}}

QPushButton#navButton:hover {{
    background-color: rgba(184, 58, 46, 0.08);
    border-left: 3px solid {COLOR_GOLD};
}}

QPushButton#navButton:checked {{
    background-color: rgba(184, 58, 46, 0.12);
    color: {COLOR_CINNABAR};
    border-left: 3px solid {COLOR_CINNABAR};
    font-weight: bold;
}}

QTextEdit, QTextBrowser {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 10px;
    font-family: {FONT_BODY};
    font-size: 14px;
    color: {COLOR_INK};
    selection-background-color: rgba(184, 58, 46, 0.2);
}}

QLineEdit {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 14px;
    font-family: {FONT_BODY};
    color: {COLOR_INK};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_CINNABAR};
}}

QComboBox {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 14px;
    font-family: {FONT_BODY};
    color: {COLOR_INK};
    min-height: 20px;
}}

QComboBox:hover {{
    border: 1px solid {COLOR_CINNABAR};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: rgba(184, 58, 46, 0.15);
    selection-color: {COLOR_CINNABAR};
    color: {COLOR_INK};
}}

QListWidget {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    font-size: 14px;
    font-family: {FONT_BODY};
    padding: 4px;
    color: {COLOR_INK};
}}

QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QListWidget::item:hover {{
    background-color: rgba(184, 58, 46, 0.06);
}}

QListWidget::item:selected {{
    background-color: rgba(184, 58, 46, 0.12);
    color: {COLOR_CINNABAR};
    border-left: 3px solid {COLOR_CINNABAR};
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QFrame#cardFrame {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
}}

QSplitter::handle {{
    background-color: {COLOR_BORDER};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_SLATE};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    border-radius: 5px;
    min-width: 30px;
}}
"""

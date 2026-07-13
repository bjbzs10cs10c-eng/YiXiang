"""全局样式 - 古籍简洁禅意风格"""

STYLE_SHEET = """
QMainWindow {
    background-color: #f5f0e8;
}

QLabel {
    color: #333333;
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
}

QLabel#titleLabel {
    font-size: 28px;
    font-weight: bold;
    color: #2c2c2c;
    padding: 10px;
}

QLabel#subtitleLabel {
    font-size: 14px;
    color: #666666;
}

QLabel#hexagramNameLabel {
    font-size: 24px;
    font-weight: bold;
    color: #1a1a1a;
}

QLabel#sectionLabel {
    font-size: 16px;
    font-weight: bold;
    color: #2c2c2c;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4px;
}

QLabel#coinLabel {
    font-size: 36px;
}

QLabel#readingLabel {
    font-size: 18px;
    color: #4a4a4a;
    padding: 8px;
    background-color: #faf8f4;
    border: 1px solid #e0d8c8;
    border-radius: 4px;
}

QPushButton {
    background-color: #4a4a4a;
    color: #f5f0e8;
    border: none;
    padding: 10px 24px;
    font-size: 15px;
    border-radius: 4px;
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QPushButton:pressed {
    background-color: #3a3a3a;
}

QPushButton#navButton {
    background-color: transparent;
    color: #4a4a4a;
    border: 1px solid #ccc;
    font-size: 14px;
    padding: 8px 16px;
}

QPushButton#navButton:hover {
    background-color: #e8e0d0;
    border-color: #aaa;
}

QPushButton#navButton:checked {
    background-color: #4a4a4a;
    color: #f5f0e8;
    border-color: #4a4a4a;
}

QTextEdit {
    background-color: #faf8f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px;
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 14px;
    color: #333;
}

QTextBrowser {
    background-color: #faf8f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 8px;
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 14px;
    color: #333;
}

QLineEdit {
    background-color: #faf8f4;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #888;
}

QListWidget {
    background-color: #faf8f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    padding: 4px;
}

QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #eee;
}

QListWidget::item:selected {
    background-color: #e8e0d0;
    color: #2c2c2c;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QFrame#cardFrame {
    background-color: #faf8f4;
    border: 1px solid #e0d8c8;
    border-radius: 6px;
}
"""

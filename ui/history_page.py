"""历史记录页 - 占卜历史"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                                QListWidgetItem, QTextBrowser, QLabel,
                                QPushButton, QSplitter, QMessageBox)
from PySide6.QtCore import Qt
from services.history_service import get_records, get_record_detail, delete_record
from services.interpretation_service import get_hexagram_by_id, get_yao_lines, get_interpretations


class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("历史记录")
        title.setObjectName("sectionLabel")
        left_layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)
        left_layout.addWidget(self.list_widget)

        self.delete_btn = QPushButton("删除选中记录")
        self.delete_btn.clicked.connect(self.delete_selected)
        left_layout.addWidget(self.delete_btn)

        splitter.addWidget(left)

        # 右侧详情
        self.detail = QTextBrowser()
        splitter.addWidget(self.detail)

        splitter.setSizes([300, 500])
        layout.addWidget(splitter)

        self.records = []
        self.refresh()

    def refresh(self):
        """刷新列表"""
        self.records = get_records(100)
        self.list_widget.clear()
        for r in self.records:
            text = f"{r['create_time'][:16]} | {r['question'][:15]}... | {r['original_name']}"
            self.list_widget.addItem(QListWidgetItem(text))
        if self.records:
            self.list_widget.setCurrentRow(0)
        else:
            self.detail.setHtml("<p style='color:#888; text-align:center;'>暂无历史记录</p>")

    def on_select(self, row):
        if row < 0 or row >= len(self.records):
            return
        record = self.records[row]
        detail = get_record_detail(record['id'])
        if not detail:
            return

        # 查询本卦信息
        orig_hex = get_hexagram_by_id(detail['original_hexagram'])
        orig_yaos = get_yao_lines(detail['original_hexagram'])
        orig_interps = get_interpretations('hexagram', detail['original_hexagram'])

        changed_hex = None
        if detail.get('changed_hexagram'):
            changed_hex = get_hexagram_by_id(detail['changed_hexagram'])

        html = self._build_html(detail, orig_hex, orig_yaos, orig_interps, changed_hex)
        self.detail.setHtml(html)

    def _build_html(self, record, orig_hex, orig_yaos, orig_interps, changed_hex):
        html = "<div style='font-family: Microsoft YaHei; line-height: 1.8;'>"
        html += f"<p style='color:#888;'>占问：<b style='color:#333;'>{record['question']}</b></p>"
        html += f"<p style='color:#888; font-size:13px;'>{record['create_time']}</p>"
        html += "<hr/>"

        html += f"<h2 style='color:#2c2c2c;'>本卦：{orig_hex['name']}</h2>"
        html += f"<p style='font-size:15px;'>卦辞：{orig_hex['gua_ci']}</p>"

        moving = record.get('moving_lines', [])
        if moving:
            moving_str = "、".join([f"第{m['position']}爻" for m in moving])
            html += f"<p style='color:#b8860b;'>动爻：{moving_str}</p>"

        if changed_hex:
            html += f"<h2 style='color:#2c2c2c; margin-top:16px;'>变卦：{changed_hex['name']}</h2>"
            html += f"<p style='font-size:15px;'>卦辞：{changed_hex['gua_ci']}</p>"

        # 爻辞
        html += "<hr/><h3 style='color:#4a4a4a;'>爻辞</h3>"
        moving_positions = {m['position'] for m in moving}
        for yl in orig_yaos:
            if yl['position'] <= 6:
                mark = " ← 动爻" if yl['position'] in moving_positions else ""
                color = "#b8860b" if mark else "#333"
                html += f"<p style='color:{color};'><b>{yl['yao_name']}</b>：{yl['original_text']}{mark}</p>"

        # 解释
        if orig_interps:
            html += "<hr/><h3 style='color:#4a4a4a;'>解释</h3>"
            for interp in orig_interps:
                html += f"<p><b style='color:#555;'>[{interp['source']}] {interp['title']}</b></p>"
                html += f"<p style='color:#555; line-height:1.8;'>{interp['content']}</p>"

        html += "</div>"
        return html

    def delete_selected(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.records):
            return
        record_id = self.records[row]['id']
        reply = QMessageBox.question(self, "确认", "确定删除这条记录？")
        if reply == QMessageBox.StandardButton.Yes:
            delete_record(record_id)
            self.refresh()

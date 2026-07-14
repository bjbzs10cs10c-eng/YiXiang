"""卦库查询页 - 浏览六十四卦"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                                QListWidgetItem, QTextBrowser, QLineEdit,
                                QSplitter)
from PySide6.QtCore import Qt
from services.interpretation_service import (get_all_hexagrams,
                                              get_hexagram_by_id,
                                              get_yao_lines,
                                              get_interpretations)
from ui.hexagram_renderer import render_hexagram_block


class LibraryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：搜索 + 列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索卦名...")
        self.search_input.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left)

        # 右侧：详情
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(False)
        splitter.addWidget(self.detail)

        splitter.setSizes([250, 550])
        layout.addWidget(splitter)

        self.load_hexagrams()

    def load_hexagrams(self):
        """加载64卦列表"""
        self.hexagrams = get_all_hexagrams()
        self.list_widget.clear()
        for h in self.hexagrams:
            item = QListWidgetItem(f"{h['sequence']}. {h['name']}")
            self.list_widget.addItem(item)
        if self.hexagrams:
            self.list_widget.setCurrentRow(0)

    def filter_list(self, text):
        """过滤列表"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text())

    def on_select(self, row):
        """选中卦象，显示详情"""
        if row < 0 or row >= len(self.hexagrams):
            return

        h = self.hexagrams[row]
        detail = get_hexagram_by_id(h['id'])
        yaos = get_yao_lines(h['id'])
        interps = get_interpretations('hexagram', h['id'])

        html = self._build_html(detail, yaos, interps)
        self.detail.setHtml(html)

    def _build_html(self, hexagram, yaos, interps):
        """构建详情HTML"""
        html = f"""
        <div style='font-family: Microsoft YaHei;'>
        {render_hexagram_block(hexagram['name'], hexagram['binary_code'])}
        <p style='color:#888;'>上卦：{hexagram['upper_trigram']} | 下卦：{hexagram['lower_trigram']}</p>
        <hr/>
        <h3 style='color:#4a4a4a;'>卦辞</h3>
        <p style='font-size:15px; line-height:1.8;'>{hexagram['gua_ci']}</p>
        <h3 style='color:#4a4a4a;'>彖辞</h3>
        <p style='font-size:14px; color:#555; line-height:1.8;'>{hexagram['tuan_ci']}</p>
        <h3 style='color:#4a4a4a;'>象辞</h3>
        <p style='font-size:14px; color:#555; line-height:1.8;'>{hexagram['xiang_ci']}</p>
        <hr/>
        <h3 style='color:#4a4a4a;'>爻辞</h3>
        """
        for y in yaos:
            html += f"<p><b style='color:#333;'>{y['yao_name']}</b>：{y['original_text']}</p>"
            if y.get('translation'):
                html += f"<p style='color:#777; font-size:13px; margin-left:20px;'>{y['translation']}</p>"

        if interps:
            html += "<hr/><h3 style='color:#4a4a4a;'>解释</h3>"
            for interp in interps:
                html += f"<p><b style='color:#555;'>[{interp['source']}] {interp['title']}</b></p>"
                html += f"<p style='color:#555; line-height:1.8;'>{interp['content']}</p>"

        html += "</div>"
        return html

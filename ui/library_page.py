"""卦库查询页 - 浏览六十四卦"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                                QListWidgetItem, QTextBrowser, QLineEdit,
                                QSplitter, QPushButton, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from services.interpretation_service import (get_all_hexagrams,
                                              get_hexagram_by_id,
                                              get_yao_lines,
                                              get_interpretations)
from services.ai_service import interpret_hexagram, AIError
from services.settings_service import is_ai_configured
from ui.hexagram_renderer import render_hexagram_block


class LibraryAIWorker(QThread):
    """后台线程：卦库页调用AI解读单卦"""
    finished_signal = Signal(str, str, int)  # (content, model, hexagram_id)
    error_signal = Signal(str, int)  # (error_message, hexagram_id)

    def __init__(self, hexagram, yao_lines, hexagram_id):
        super().__init__()
        self.hexagram = hexagram
        self.yao_lines = yao_lines
        self.hexagram_id = hexagram_id

    def run(self):
        from services.settings_service import get_ai_config
        try:
            content = interpret_hexagram(self.hexagram, self.yao_lines)
            config = get_ai_config()
            model = config.get("model", "未知")
            self.finished_signal.emit(content, model, self.hexagram_id)
        except AIError as e:
            self.error_signal.emit(e.message, self.hexagram_id)
        except Exception as e:
            self.error_signal.emit(f"AI解读失败：{e}", self.hexagram_id)


class LibraryPage(QWidget):
    def __init__(self):
        super().__init__()
        self._ai_worker = None
        self._current_hexagram = None
        self._current_yaos = []
        self._current_interps = []
        self._current_hexagram_id = None

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

        # AI 解读按钮
        self.ai_btn = QPushButton("AI 解读")
        self.ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_btn.clicked.connect(self.on_ai_interpret)
        self.ai_btn.setVisible(False)
        left_layout.addWidget(self.ai_btn)

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

        self._current_hexagram = detail
        self._current_yaos = yaos
        self._current_interps = interps
        self._current_hexagram_id = h['id']

        html = self._build_html(detail, yaos, interps)
        self.detail.setHtml(html)

        # 显示AI按钮
        self.ai_btn.setVisible(True)
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI 解读")

    def on_ai_interpret(self):
        """触发AI解读"""
        if not self._current_hexagram:
            return

        if not is_ai_configured():
            QMessageBox.warning(self, "未配置AI",
                                "AI 尚未配置，请先到「设置」页面配置AI服务商、模型和API Key")
            return

        # 禁用按钮，显示加载中
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("AI 解读中...")
        self._append_loading()

        # 后台线程调用
        self._ai_worker = LibraryAIWorker(
            self._current_hexagram, self._current_yaos, self._current_hexagram_id
        )
        self._ai_worker.finished_signal.connect(self.on_ai_finished)
        self._ai_worker.error_signal.connect(self.on_ai_error)
        self._ai_worker.start()

    def on_ai_finished(self, content, model, hexagram_id):
        """AI解读完成回调"""
        if hexagram_id != self._current_hexagram_id:
            return  # 用户已切换到其他卦象，丢弃旧结果

        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("重新AI解读")
        self._refresh_detail_with_ai(content, model)

    def on_ai_error(self, error_msg, hexagram_id):
        """AI解读失败回调"""
        if hexagram_id != self._current_hexagram_id:
            return
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI 解读")
        self._refresh_detail_with_error(error_msg)

    def _append_loading(self):
        """追加加载中提示"""
        html = self.detail.toHtml()
        html += "<hr/><p style='color:#888; font-size:14px;'>AI 解读中，请稍候...</p>"
        self.detail.setHtml(html)
        self.detail.verticalScrollBar().setValue(
            self.detail.verticalScrollBar().maximum()
        )

    def _refresh_detail_with_ai(self, content, model):
        """刷新详情并追加AI解读结果"""
        if not self._current_hexagram:
            return
        base_html = self._build_html(self._current_hexagram, self._current_yaos, self._current_interps)
        ai_html = self._build_ai_html(content, model)
        self.detail.setHtml(base_html + ai_html)
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _refresh_detail_with_error(self, error_msg):
        """刷新详情并追加错误提示"""
        if not self._current_hexagram:
            return
        base_html = self._build_html(self._current_hexagram, self._current_yaos, self._current_interps)
        error_html = (
            "<hr/>"
            "<div style='background-color:#fdf2f2; padding:12px; border:1px solid #f5c6cb; border-radius:4px;'>"
            f"<p style='color:#c0392b; font-weight:bold;'>AI 解读失败</p>"
            f"<p style='color:#721c24; font-size:14px;'>{error_msg}</p>"
            "</div>"
        )
        self.detail.setHtml(base_html + error_html)

    def _build_ai_html(self, content, model):
        """构建AI解读HTML"""
        safe_content = (content
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br/>"))
        return (
            "<hr/>"
            "<div style='background-color:#f0f7ff; padding:14px; border:1px solid #c8e0f4; border-radius:4px; margin-top:10px;'>"
            f"<p style='color:#1a73e8; font-weight:bold; font-size:16px;'>AI 解读（{model}）</p>"
            "<hr style='border:none; border-top:1px dashed #c8e0f4; margin:8px 0;'/>"
            f"<div style='color:#333; line-height:1.9; font-size:14px;'>{safe_content}</div>"
            "</div>"
        )

    def _scroll_to_bottom(self):
        """滚动到详情底部"""
        self.detail.verticalScrollBar().setValue(
            self.detail.verticalScrollBar().maximum()
        )

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

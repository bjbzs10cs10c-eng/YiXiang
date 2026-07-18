"""历史记录页 - 占卜历史"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                                QListWidgetItem, QTextBrowser, QLabel,
                                QPushButton, QSplitter, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from services.history_service import (get_records, get_record_detail, delete_record,
                                       save_ai_interpretation, get_ai_interpretation)
from services.interpretation_service import get_hexagram_by_id, get_yao_lines, get_interpretations
from services.ai_service import interpret_divination, AIError
from services.settings_service import is_ai_configured
from ui.hexagram_renderer import render_hexagram_block, render_dual_hexagram_block


class HistoryAIWorker(QThread):
    """后台线程：历史页调用AI解读"""
    finished_signal = Signal(str, str, int)  # (content, model, record_id)
    error_signal = Signal(str, int)  # (error_message, record_id)

    def __init__(self, result, record_id):
        super().__init__()
        self.result = result
        self.record_id = record_id

    def run(self):
        from services.settings_service import get_ai_config
        try:
            content = interpret_divination(self.result)
            config = get_ai_config()
            model = config.get("model", "未知")
            self.finished_signal.emit(content, model, self.record_id)
        except AIError as e:
            self.error_signal.emit(e.message, self.record_id)
        except Exception as e:
            self.error_signal.emit(f"AI解读失败：{e}", self.record_id)


class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self._ai_worker = None
        self._current_detail = None
        self._current_record_id = None

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

        # AI 解读按钮
        self.ai_btn = QPushButton("AI 解读")
        self.ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_btn.clicked.connect(self.on_ai_interpret)
        self.ai_btn.setVisible(False)
        left_layout.addWidget(self.ai_btn)

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
            self.ai_btn.setVisible(False)

    def on_select(self, row):
        if row < 0 or row >= len(self.records):
            return
        record = self.records[row]
        detail = get_record_detail(record['id'])
        if not detail:
            return

        self._current_detail = detail
        self._current_record_id = detail['id']

        # 查询本卦信息
        orig_hex = get_hexagram_by_id(detail['original_hexagram'])
        orig_yaos = get_yao_lines(detail['original_hexagram'])
        orig_interps = get_interpretations('hexagram', detail['original_hexagram'])

        changed_hex = None
        if detail.get('changed_hexagram'):
            changed_hex = get_hexagram_by_id(detail['changed_hexagram'])

        html = self._build_html(detail, orig_hex, orig_yaos, orig_interps, changed_hex)

        # 如果已有保存的AI解读，追加展示
        saved_ai = get_ai_interpretation(detail['id'])
        if saved_ai:
            html += self._build_ai_html(saved_ai['content'], saved_ai['model'])
            self.ai_btn.setText("重新AI解读")
        else:
            self.ai_btn.setText("AI 解读")

        self.detail.setHtml(html)

        # 显示AI按钮
        self.ai_btn.setVisible(True)
        self.ai_btn.setEnabled(True)

    def on_ai_interpret(self):
        """触发AI解读"""
        if not self._current_detail:
            return

        # 检查是否已配置AI
        if not is_ai_configured():
            QMessageBox.warning(self, "未配置AI",
                                "AI 尚未配置，请先到「设置」页面配置AI服务商、模型和API Key")
            return

        # 从详情构建result（interpret_divination需要完整result格式）
        result = self._build_result_from_detail(self._current_detail)
        if not result:
            QMessageBox.warning(self, "错误", "无法构建占卜结果数据")
            return

        # 禁用按钮，显示加载中
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("AI 解读中...")
        self._append_loading()

        # 后台线程调用
        self._ai_worker = HistoryAIWorker(result, self._current_record_id)
        self._ai_worker.finished_signal.connect(self.on_ai_finished)
        self._ai_worker.error_signal.connect(self.on_ai_error)
        self._ai_worker.start()

    def _build_result_from_detail(self, detail):
        """从历史记录详情构建AI解读所需的result格式"""
        try:
            orig_hex = get_hexagram_by_id(detail['original_hexagram'])
            orig_yaos = get_yao_lines(detail['original_hexagram'])
            orig_interps = get_interpretations('hexagram', detail['original_hexagram'])

            changed_hex = None
            if detail.get('changed_hexagram'):
                changed_hex = get_hexagram_by_id(detail['changed_hexagram'])

            moving = detail.get('moving_lines', [])
            moving_count = len(moving) if moving else 0

            # 构建断卦文本（简化的）
            reading_source = "静卦" if moving_count == 0 else "动爻断"
            if moving_count == 0:
                reading_text = f"以{orig_hex['name']}卦卦辞断之"
            elif moving_count == 6:
                reading_text = f"以变卦{changed_hex['name'] if changed_hex else ''}卦辞断之"
            else:
                reading_text = f"以{orig_hex['name']}卦动爻爻辞断之"

            return {
                "question": detail.get('question', ''),
                "time": detail.get('create_time', ''),
                "original_hexagram": orig_hex,
                "changed_hexagram": changed_hex,
                "moving_lines": moving,
                "moving_count": moving_count,
                "reading_source": reading_source,
                "reading_text": reading_text,
                "original_yao_lines": orig_yaos,
                "original_interpretations": orig_interps,
                "tosses": detail.get('yao_values', []),
            }
        except Exception as e:
            print(f"构建result失败: {e}")
            return None

    def on_ai_finished(self, content, model, record_id):
        """AI解读完成回调"""
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("重新AI解读")

        # 重新构建详情HTML并追加AI结果
        self._refresh_detail_with_ai(content, model)

        # 保存到数据库
        if record_id == self._current_record_id:
            save_ai_interpretation(record_id, content, model)

    def on_ai_error(self, error_msg, record_id):
        """AI解读失败回调"""
        if record_id != self._current_record_id:
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
        if not self._current_detail:
            return
        detail = self._current_detail
        orig_hex = get_hexagram_by_id(detail['original_hexagram'])
        orig_yaos = get_yao_lines(detail['original_hexagram'])
        orig_interps = get_interpretations('hexagram', detail['original_hexagram'])
        changed_hex = None
        if detail.get('changed_hexagram'):
            changed_hex = get_hexagram_by_id(detail['changed_hexagram'])

        base_html = self._build_html(detail, orig_hex, orig_yaos, orig_interps, changed_hex)
        ai_html = self._build_ai_html(content, model)
        self.detail.setHtml(base_html + ai_html)
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _refresh_detail_with_error(self, error_msg):
        """刷新详情并追加错误提示"""
        if not self._current_detail:
            return
        detail = self._current_detail
        orig_hex = get_hexagram_by_id(detail['original_hexagram'])
        orig_yaos = get_yao_lines(detail['original_hexagram'])
        orig_interps = get_interpretations('hexagram', detail['original_hexagram'])
        changed_hex = None
        if detail.get('changed_hexagram'):
            changed_hex = get_hexagram_by_id(detail['changed_hexagram'])

        base_html = self._build_html(detail, orig_hex, orig_yaos, orig_interps, changed_hex)
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

    def _build_html(self, record, orig_hex, orig_yaos, orig_interps, changed_hex):
        html = "<div style='font-family: Microsoft YaHei; line-height: 1.8;'>"
        html += f"<p style='color:#888;'>占问：<b style='color:#333;'>{record['question']}</b></p>"
        html += f"<p style='color:#888; font-size:13px;'>{record['create_time']}</p>"
        html += "<hr/>"

        moving = record.get('moving_lines', [])
        moving_positions = {m['position'] for m in moving}

        if changed_hex:
            html += render_dual_hexagram_block(
                orig_hex['name'], orig_hex['binary_code'],
                changed_hex['name'], changed_hex['binary_code'],
                moving_positions
            )
        else:
            html += render_hexagram_block(orig_hex['name'], orig_hex['binary_code'], moving_positions)

        html += f"<p style='font-size:15px;'>卦辞：{orig_hex['gua_ci']}</p>"

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

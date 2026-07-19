"""占卜页 - 输入问题 + 铜钱投掷 + 结果展示"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QLineEdit, QTextBrowser,
                                QFrame, QScrollArea, QGridLayout, QGraphicsView,
                                QGraphicsScene, QGraphicsPixmapItem, QGraphicsRotation)
from PySide6.QtCore import (Signal, Qt, QTimer, QThread, QPropertyAnimation,
                              QEasingCurve, QPointF)
from PySide6.QtGui import QPixmap, QPainter, QVector3D

from core.coin import toss_three_coins
from controllers.divination_controller import DivinationController
from config import COIN_FRONT_IMG, COIN_BACK_IMG
from ui.hexagram_renderer import render_hexagram_block, render_dual_hexagram_block
from ui.styles import (COLOR_INK, COLOR_CINNABAR, COLOR_SLATE, COLOR_GOLD,
                        COLOR_PAPER, COLOR_CARD_BG, COLOR_BORDER, FONT_BODY, FONT_TITLE)
from services.ai_service import interpret_divination, AIError
from services.settings_service import is_ai_configured
from services.history_service import save_ai_interpretation, get_ai_interpretation


class AIInterpretWorker(QThread):
    """后台线程：调用AI解读，避免界面卡死"""
    finished_signal = Signal(str, str)  # (content, model)
    error_signal = Signal(str)  # error_message

    def __init__(self, result):
        super().__init__()
        self.result = result

    def run(self):
        from services.settings_service import get_ai_config
        try:
            content = interpret_divination(self.result)
            config = get_ai_config()
            model = config.get("model", "未知")
            self.finished_signal.emit(content, model)
        except AIError as e:
            self.error_signal.emit(e.message)
        except Exception as e:
            self.error_signal.emit(f"AI解读失败：{e}")


class CoinWidget(QGraphicsView):
    """单个铜钱控件，用 QGraphicsRotation 实现真正的旋转动画

    通过 QPropertyAnimation 动画 angle 属性（0°→360°），
    旋转过程中在 90° 时切换正反面图片，模拟硬币翻转。
    """

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedSize(90, 90)
        self.setStyleSheet("background: transparent; border: none;")

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # 铜钱图片（正反面）
        front_pm = QPixmap(COIN_FRONT_IMG).scaled(
            80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        back_pm = QPixmap(COIN_BACK_IMG).scaled(
            80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self._front_item = QGraphicsPixmapItem(front_pm)
        self._back_item = QGraphicsPixmapItem(back_pm)
        self._front_item.setOffset(5, 5)
        self._back_item.setOffset(5, 5)
        self._back_item.setVisible(False)

        # 旋转 transform（绕 Y 轴，原点为铜钱中心）
        self._rotation = QGraphicsRotation()
        self._rotation.setAxis(Qt.Axis.YAxis)
        self._rotation.setOrigin(QVector3D(45, 45, 0))

        for item in (self._front_item, self._back_item):
            item.setTransformations([self._rotation])
            self._scene.addItem(item)

        self._showing_front = True
        self._switched = False
        self._final_is_front = True
        self._on_finished = None
        self._anim = None

    def flip(self, final_is_front, on_finished):
        """旋转动画：绕 Y 轴旋转一周，中途切换正反面

        Args:
            final_is_front: True=停在正面, False=停在反面
            on_finished: 动画完成回调
        """
        self._final_is_front = final_is_front
        self._on_finished = on_finished
        self._switched = False
        # 起始面根据当前显示决定
        self._showing_front = True
        self._front_item.setVisible(True)
        self._back_item.setVisible(False)
        self._rotation.setAngle(0)

        # 动画 0 → 360，耗时约 700ms
        self._anim = QPropertyAnimation(self._rotation, b"angle")
        self._anim.setDuration(700)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.valueChanged.connect(self._on_angle_changed)
        self._anim.finished.connect(self._on_anim_finished)
        self._anim.start()

    def _on_angle_changed(self, angle):
        """旋转到 90°/270° 时切换正反面（仅切换一次，到终点再根据 final 决定）"""
        # 在 90°~270° 之间显示背面，其余显示正面
        if 90 < angle < 270:
            if not self._switched:
                self._front_item.setVisible(False)
                self._back_item.setVisible(True)
                self._switched = True
        else:
            if self._switched:
                self._front_item.setVisible(True)
                self._back_item.setVisible(False)
                self._switched = False

    def _on_anim_finished(self):
        """动画结束，停在最终面"""
        if self._final_is_front:
            self._front_item.setVisible(True)
            self._back_item.setVisible(False)
        else:
            self._front_item.setVisible(False)
            self._back_item.setVisible(True)
        self._rotation.setAngle(0)
        if self._on_finished:
            cb = self._on_finished
            self._on_finished = None
            cb()


class DivinationPage(QWidget):
    """占卜页面"""
    divination_done = Signal(dict)

    def __init__(self):
        super().__init__()
        self.controller = DivinationController()
        self.tosses = []
        self.current_toss = 0
        self.is_tossing = False
        self._ai_worker = None
        self._current_result = None
        self._current_record_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # 阶段1：输入问题
        self.input_frame = QFrame()
        input_layout = QVBoxLayout(self.input_frame)
        input_layout.setSpacing(12)

        label = QLabel("请输入您要占问的事项：")
        label.setObjectName("sectionLabel")
        input_layout.addWidget(label)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("例如：事业发展如何？")
        self.question_input.returnPressed.connect(self.start)
        input_layout.addWidget(self.question_input)

        # 铜钱区域
        self.coin_area = QWidget()
        coin_layout = QHBoxLayout(self.coin_area)
        coin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coin_layout.setSpacing(30)

        self.coins = [CoinWidget() for _ in range(3)]
        for coin in self.coins:
            coin_layout.addWidget(coin)

        input_layout.addWidget(self.coin_area)

        # 投掷进度
        self.progress_label = QLabel("点击下方按钮开始投掷铜钱（共六次）")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; color: {};".format(COLOR_SLATE))
        input_layout.addWidget(self.progress_label)

        # 六次投掷结果预览
        self.toss_labels = []
        toss_widget = QWidget()
        toss_grid = QGridLayout(toss_widget)
        toss_grid.setSpacing(4)
        for i in range(6):
            lbl = QLabel(f"第{6 - i}爻：待投掷")
            lbl.setStyleSheet("font-size: 13px; color: {}; padding: 4px;".format(COLOR_SLATE))
            self.toss_labels.append(lbl)
            toss_grid.addWidget(lbl, i, 0)
        input_layout.addWidget(toss_widget)

        # 开始按钮
        self.toss_btn = QPushButton("开始投掷")
        self.toss_btn.setFixedHeight(40)
        self.toss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toss_btn.clicked.connect(self.do_toss)
        input_layout.addWidget(self.toss_btn)

        layout.addWidget(self.input_frame)

        # 阶段2：结果展示
        self.result_scroll = QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_content = QTextBrowser()
        self.result_scroll.setWidget(self.result_content)
        self.result_scroll.setVisible(False)
        layout.addWidget(self.result_scroll)

        # 重新占卜按钮
        self.reset_btn = QPushButton("重新占卜")
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)
        self.reset_btn.setVisible(False)
        layout.addWidget(self.reset_btn)

        # AI 解读按钮
        self.ai_btn = QPushButton("AI 解读")
        self.ai_btn.setFixedHeight(40)
        self.ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_btn.clicked.connect(self.on_ai_interpret)
        self.ai_btn.setVisible(False)
        layout.addWidget(self.ai_btn)

    def start(self):
        """开始占卜流程"""
        question = self.question_input.text().strip()
        if not question:
            self.progress_label.setText("请先输入占问事项")
            return

        self.tosses = []
        self.current_toss = 0
        self.is_tossing = False

        for i, lbl in enumerate(self.toss_labels):
            lbl.setText(f"第{6 - i}爻：待投掷")
            lbl.setStyleSheet("font-size: 13px; color: {}; padding: 4px;".format(COLOR_SLATE))

        self.progress_label.setText("点击按钮投掷铜钱（第1次/共6次）")
        self.toss_btn.setEnabled(True)
        self.toss_btn.setText("投掷铜钱")

    def do_toss(self):
        """执行一次投掷"""
        if self.is_tossing or self.current_toss >= 6:
            return

        question = self.question_input.text().strip()
        if not question:
            self.progress_label.setText("请先输入占问事项")
            return

        self.is_tossing = True
        self.toss_btn.setEnabled(False)

        # 执行投掷
        result = toss_three_coins()
        self.tosses.append(result)

        # 铜钱动画 - 依次旋转
        flip_count = [0]

        def on_coin_flipped():
            flip_count[0] += 1
            if flip_count[0] >= 3:
                self.show_toss_result(result, self.current_toss)
                self.current_toss += 1
                self.is_tossing = False

                if self.current_toss >= 6:
                    self.progress_label.setText("六次投掷完成，正在解析卦象...")
                    QTimer.singleShot(500, self.finish_divination)
                else:
                    self.toss_btn.setEnabled(True)
                    self.toss_btn.setText(f"投掷铜钱（第{self.current_toss + 1}次/共6次）")
                    self.progress_label.setText(f"第{self.current_toss}次完成，继续投掷")

        # 依次旋转三个铜钱，每枚根据投掷结果显示最终正反面
        for i, coin in enumerate(self.coins):
            is_front = result["coins"][i] == 3
            QTimer.singleShot(i * 200, lambda c=coin, f=is_front, cb=on_coin_flipped: c.flip(f, cb))

    def show_toss_result(self, result, index):
        """显示单次投掷结果"""
        pos = index + 1
        coins_str = " ".join(["正" if c == 3 else "反" for c in result["coins"]])
        yao_name = result["name"]
        value = result["value"]

        is_moving = result["value"] in (6, 9)
        color = COLOR_CINNABAR if is_moving else COLOR_INK
        bold = "bold" if is_moving else "normal"
        # 从上到下显示：第6爻在上，第1爻在下
        lbl = self.toss_labels[5 - index]
        lbl.setText(f"第{pos}爻：{coins_str} = {value} {yao_name}")
        lbl.setStyleSheet(f"font-size: 13px; color: {color}; padding: 4px; font-weight: {bold};")

    def finish_divination(self):
        """完成占卜，生成结果"""
        question = self.question_input.text().strip()
        try:
            result = self.controller.perform_divination(question, self.tosses)
            record_id = self.controller.save_result(result)
            self._current_result = result
            self._current_record_id = record_id
            self.divination_done.emit(result)
            self.show_result(result)
        except Exception as e:
            self.progress_label.setText(f"占卜出错: {e}")
            self.toss_btn.setEnabled(True)

    def show_result(self, result):
        """显示完整结果"""
        self.input_frame.setVisible(False)
        self.result_scroll.setVisible(True)
        self.reset_btn.setVisible(True)

        # 显示AI解读按钮（无论是否配置，都显示；未配置时点击会提示）
        self.ai_btn.setVisible(True)
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI 解读")

        html = self._build_result_html(result)
        self.result_content.setHtml(html)

        # 如果已有保存的AI解读，直接展示
        if self._current_record_id:
            saved = get_ai_interpretation(self._current_record_id)
            if saved:
                self._append_ai_result(saved["content"], saved["model"])
                self.ai_btn.setText("重新AI解读")
                self.ai_btn.setEnabled(True)

    def on_ai_interpret(self):
        """触发AI解读"""
        if not self._current_result:
            return

        # 检查是否已配置AI
        if not is_ai_configured():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "未配置AI",
                                "AI 尚未配置，请先到「设置」页面配置AI服务商、模型和API Key")
            return

        # 禁用按钮，显示加载中
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("AI 解读中...")
        self._append_loading()

        # 后台线程调用
        self._ai_worker = AIInterpretWorker(self._current_result)
        self._ai_worker.finished_signal.connect(self.on_ai_finished)
        self._ai_worker.error_signal.connect(self.on_ai_error)
        self._ai_worker.start()

    def on_ai_finished(self, content, model):
        """AI解读完成回调"""
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("重新AI解读")
        self._append_ai_result(content, model)

        # 保存到数据库
        if self._current_record_id:
            save_ai_interpretation(self._current_record_id, content, model)

    def on_ai_error(self, error_msg):
        """AI解读失败回调"""
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI 解读")
        self._append_ai_error(error_msg)

    def _append_loading(self):
        """追加加载中提示"""
        html = self.result_content.toHtml()
        html += f"<hr/><p id='ai_loading' style='color:{COLOR_SLATE}; font-size:14px;'>AI 解读中，请稍候...</p>"
        self.result_content.setHtml(html)
        # 滚动到底部
        self.result_content.verticalScrollBar().setValue(
            self.result_content.verticalScrollBar().maximum()
        )

    def _append_ai_result(self, content, model):
        """追加AI解读结果到结果页"""
        # 重新构建HTML，避免累加重复
        base_html = self._build_result_html(self._current_result)
        ai_html = self._build_ai_html(content, model)
        self.result_content.setHtml(base_html + ai_html)
        # 滚动到底部
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _append_ai_error(self, error_msg):
        """追加AI解读错误提示"""
        base_html = self._build_result_html(self._current_result)
        error_html = (
            f"<hr/>"
            f"<div style='background-color:#FDF2F2; padding:14px; border:1px solid #F5C6CB; border-radius:8px;'>"
            f"<p style='color:#B83A2E; font-weight:bold; font-size:16px;'>AI 解读失败</p>"
            f"<p style='color:#721C24; font-size:14px;'>{error_msg}</p>"
            f"</div>"
        )
        self.result_content.setHtml(base_html + error_html)

    def _build_ai_html(self, content, model):
        """构建AI解读HTML"""
        # 将换行符转为 <br/>，简单转义
        safe_content = (content
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br/>"))
        return (
            f"<hr/>"
            f"<div style='background-color:#F0F7FF; padding:16px; border:1px solid #C8E0F4; border-radius:8px; margin-top:12px;'>"
            f"<p style='color:#1A73E8; font-weight:bold; font-size:16px;'>AI 解读（{model}）</p>"
            f"<hr style='border:none; border-top:1px dashed #C8E0F4; margin:8px 0;'/>"
            f"<div style='color:#2B2B2B; line-height:1.9; font-size:14px;'>{safe_content}</div>"
            f"</div>"
        )

    def _scroll_to_bottom(self):
        """滚动到结果底部"""
        self.result_content.verticalScrollBar().setValue(
            self.result_content.verticalScrollBar().maximum()
        )

    def _build_result_html(self, result):
        """构建结果HTML"""
        orig = result["original_hexagram"]
        moving = result["moving_lines"]
        moving_count = result["moving_count"]
        changed = result["changed_hexagram"]

        html = f"<div style='font-family: {FONT_BODY}; line-height: 1.8; color: {COLOR_INK};'>"

        html += f"<p style='color:{COLOR_SLATE};'>占问：<b style='color:{COLOR_INK};'>{result['question']}</b></p>"
        html += f"<p style='color:{COLOR_SLATE}; font-size:13px;'>{result['time']}</p>"
        html += f"<hr style='border:none; border-top:1px solid {COLOR_BORDER};'/>"

        moving_positions = {m["position"] for m in moving}

        if changed:
            html += render_dual_hexagram_block(
                orig['name'], orig['binary_code'],
                changed['name'], changed['binary_code'],
                moving_positions
            )
        else:
            html += render_hexagram_block(orig['name'], orig['binary_code'], moving_positions)

        html += f"<p style='color:{COLOR_SLATE}; font-size:13px;'>上卦：{orig['upper_trigram']} | 下卦：{orig['lower_trigram']}</p>"
        html += f"<p style='font-size:15px;'>卦辞：{orig['gua_ci']}</p>"
        html += f"<p style='color:{COLOR_SLATE}; font-size:14px;'>象辞：{orig['xiang_ci']}</p>"

        if moving_count > 0:
            moving_str = "、".join([f"第{m['position']}爻({m['name']})" for m in moving])
            html += f"<p style='color:{COLOR_CINNABAR}; font-weight:bold;'>动爻：{moving_str}（共{moving_count}个）</p>"
        else:
            html += f"<p style='color:{COLOR_SLATE};'>静卦（无动爻）</p>"

        if changed:
            html += f"<h3 style='color:{COLOR_INK}; margin-top:20px; font-family:{FONT_TITLE};'>变卦：{changed['name']}</h3>"
            html += f"<p style='color:{COLOR_SLATE}; font-size:13px;'>上卦：{changed['upper_trigram']} | 下卦：{changed['lower_trigram']}</p>"
            html += f"<p style='font-size:15px;'>卦辞：{changed['gua_ci']}</p>"

        html += f"<hr style='border:none; border-top:1px solid {COLOR_BORDER};'/>"
        html += f"<p style='font-size:16px; color:{COLOR_INK}; background-color:{COLOR_CARD_BG}; padding:12px; border-left:4px solid {COLOR_CINNABAR}; border-radius:4px;'>"
        html += f"<b>断卦（{result['reading_source']}）：</b>{result['reading_text']}</p>"

        html += f"<hr/><h3 style='color:{COLOR_INK}; font-family:{FONT_TITLE};'>本卦爻辞</h3>"
        for yl in result["original_yao_lines"]:
            if yl["position"] <= 6:
                moving_mark = " ← 动爻" if yl["position"] in moving_positions else ""
                color = COLOR_CINNABAR if moving_mark else COLOR_INK
                html += f"<p style='color:{color};'><b>{yl['yao_name']}</b>：{yl['original_text']}{moving_mark}</p>"
                if yl.get("translation"):
                    html += f"<p style='color:{COLOR_SLATE}; font-size:13px; margin-left:20px;'>{yl['translation']}</p>"

        interps = result["original_interpretations"]
        if interps:
            html += f"<hr/><h3 style='color:{COLOR_INK}; font-family:{FONT_TITLE};'>卦象解释</h3>"
            for interp in interps:
                html += f"<p><b style='color:{COLOR_SLATE};'>[{interp['source']}] {interp['title']}</b></p>"
                html += f"<p style='color:{COLOR_SLATE}; line-height:1.8;'>{interp['content']}</p>"

        html += "</div>"
        return html

    def reset(self):
        """重置为初始状态"""
        self.input_frame.setVisible(True)
        self.result_scroll.setVisible(False)
        self.reset_btn.setVisible(False)
        self.ai_btn.setVisible(False)
        self.question_input.clear()
        self.tosses = []
        self.current_toss = 0
        self._current_result = None
        self._current_record_id = None
        for i, lbl in enumerate(self.toss_labels):
            lbl.setText(f"第{6 - i}爻：待投掷")
            lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_SLATE}; padding: 4px;")
        self.progress_label.setText("点击下方按钮开始投掷铜钱（共六次）")
        self.toss_btn.setText("开始投掷")
        self.toss_btn.setEnabled(True)

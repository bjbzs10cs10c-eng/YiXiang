"""占卜页 - 输入问题 + 铜钱投掷 + 结果展示"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QLineEdit, QTextBrowser,
                                QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Signal, Qt, QTimer

from core.coin import toss_three_coins
from controllers.divination_controller import DivinationController


class CoinWidget(QLabel):
    """单个铜钱控件，用QTimer切换 ●/○ 模拟翻转"""

    def __init__(self):
        super().__init__("●")
        self.setObjectName("coinLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(60, 60)
        self.setStyleSheet("""
            QLabel {
                font-size: 36px;
                color: #b8860b;
                background-color: #faf8f4;
                border: 2px solid #d4a843;
                border-radius: 30px;
            }
        """)
        self._timer = None
        self._flip_count = 0
        self._max_flips = 6
        self._on_finished = None

    def flip(self, on_finished):
        """翻转动画：用QTimer切换 ● 和 ○ 模拟翻转"""
        self._on_finished = on_finished
        self._flip_count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._do_flip)
        self._timer.start(100)

    def _do_flip(self):
        """执行一次切换"""
        if self.text() == "●":
            self.setText("○")
        else:
            self.setText("●")

        self._flip_count += 1
        if self._flip_count >= self._max_flips:
            self._timer.stop()
            self.setText("●")
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
        coin_layout.setSpacing(20)

        self.coins = [CoinWidget() for _ in range(3)]
        for coin in self.coins:
            coin_layout.addWidget(coin)

        input_layout.addWidget(self.coin_area)

        # 投掷进度
        self.progress_label = QLabel("点击下方按钮开始投掷铜钱（共六次）")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; color: #888;")
        input_layout.addWidget(self.progress_label)

        # 六次投掷结果预览
        self.toss_labels = []
        toss_widget = QWidget()
        toss_grid = QGridLayout(toss_widget)
        toss_grid.setSpacing(4)
        for i in range(6):
            lbl = QLabel(f"第{i+1}爻：待投掷")
            lbl.setStyleSheet("font-size: 13px; color: #999; padding: 4px;")
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

    def start(self):
        """开始占卜流程"""
        question = self.question_input.text().strip()
        if not question:
            self.progress_label.setText("请先输入占问事项")
            return

        self.tosses = []
        self.current_toss = 0
        self.is_tossing = False

        for lbl in self.toss_labels:
            lbl.setText("待投掷")
            lbl.setStyleSheet("font-size: 13px; color: #999; padding: 4px;")

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

        # 铜钱动画 - 依次翻转
        flip_count = [0]

        def on_coin_flipped():
            flip_count[0] += 1
            if flip_count[0] >= 3:
                # 所有铜钱翻转完成
                self.show_toss_result(result, self.current_toss)
                self.current_toss += 1
                self.is_tossing = False

                if self.current_toss >= 6:
                    # 六次完成
                    self.progress_label.setText("六次投掷完成，正在解析卦象...")
                    QTimer.singleShot(500, self.finish_divination)
                else:
                    self.toss_btn.setEnabled(True)
                    self.toss_btn.setText(f"投掷铜钱（第{self.current_toss + 1}次/共6次）")
                    self.progress_label.setText(f"第{self.current_toss}次完成，继续投掷")

        # 依次翻转三个铜钱
        for i, coin in enumerate(self.coins):
            QTimer.singleShot(i * 150, lambda c=coin, cb=on_coin_flipped: c.flip(cb))

    def show_toss_result(self, result, index):
        """显示单次投掷结果"""
        pos = index + 1
        coins_str = " ".join(["正" if c == 3 else "反" for c in result["coins"]])
        yao_name = result["name"]
        value = result["value"]

        color = "#b8860b" if result["value"] in (6, 9) else "#555"
        # 从上到下显示：第6爻在上，第1爻在下
        lbl = self.toss_labels[5 - index]
        lbl.setText(f"第{pos}爻：{coins_str} = {value} {yao_name}")
        bold = "bold" if result["value"] in (6, 9) else "normal"
        lbl.setStyleSheet(f"font-size: 13px; color: {color}; padding: 4px; font-weight: {bold};")

    def finish_divination(self):
        """完成占卜，生成结果"""
        question = self.question_input.text().strip()
        try:
            result = self.controller.perform_divination(question)
            self.controller.save_result(result)
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

        html = self._build_result_html(result)
        self.result_content.setHtml(html)

    def _build_result_html(self, result):
        """构建结果HTML"""
        orig = result["original_hexagram"]
        moving = result["moving_lines"]
        moving_count = result["moving_count"]
        changed = result["changed_hexagram"]

        html = "<div style='font-family: Microsoft YaHei; line-height: 1.8;'>"

        # 问题
        html += f"<p style='color:#888;'>占问：<b style='color:#333;'>{result['question']}</b></p>"
        html += f"<p style='color:#888; font-size:13px;'>{result['time']}</p>"
        html += "<hr/>"

        # 本卦
        html += f"<h2 style='color:#2c2c2c;'>本卦：{orig['name']}</h2>"
        html += f"<p style='color:#888; font-size:13px;'>上卦：{orig['upper_trigram']} | 下卦：{orig['lower_trigram']}</p>"
        html += f"<p style='font-size:15px;'>卦辞：{orig['gua_ci']}</p>"
        html += f"<p style='color:#555; font-size:14px;'>象辞：{orig['xiang_ci']}</p>"

        # 动爻
        if moving_count > 0:
            moving_str = "、".join([f"第{m['position']}爻({m['name']})" for m in moving])
            html += f"<p style='color:#b8860b; font-weight:bold;'>动爻：{moving_str}（共{moving_count}个）</p>"
        else:
            html += "<p style='color:#555;'>静卦（无动爻）</p>"

        # 变卦
        if changed:
            html += f"<h2 style='color:#2c2c2c; margin-top:20px;'>变卦：{changed['name']}</h2>"
            html += f"<p style='color:#888; font-size:13px;'>上卦：{changed['upper_trigram']} | 下卦：{changed['lower_trigram']}</p>"
            html += f"<p style='font-size:15px;'>卦辞：{changed['gua_ci']}</p>"

        # 断卦
        html += "<hr/>"
        html += "<p style='font-size:16px; color:#4a4a4a; background-color:#faf8f4; padding:10px; border:1px solid #e0d8c8; border-radius:4px;'>"
        html += f"<b>断卦（{result['reading_source']}）：</b>{result['reading_text']}</p>"

        # 爻辞
        html += "<hr/><h3 style='color:#4a4a4a;'>本卦爻辞</h3>"
        moving_positions = {m["position"] for m in moving}
        for yl in result["original_yao_lines"]:
            if yl["position"] <= 6:
                moving_mark = " ← 动爻" if yl["position"] in moving_positions else ""
                color = "#b8860b" if moving_mark else "#333"
                html += f"<p style='color:{color};'><b>{yl['yao_name']}</b>：{yl['original_text']}{moving_mark}</p>"
                if yl.get("translation"):
                    html += f"<p style='color:#888; font-size:13px; margin-left:20px;'>{yl['translation']}</p>"

        # 解释
        interps = result["original_interpretations"]
        if interps:
            html += "<hr/><h3 style='color:#4a4a4a;'>卦象解释</h3>"
            for interp in interps:
                html += f"<p><b style='color:#555;'>[{interp['source']}] {interp['title']}</b></p>"
                html += f"<p style='color:#555; line-height:1.8;'>{interp['content']}</p>"

        html += "</div>"
        return html

    def reset(self):
        """重置为初始状态"""
        self.input_frame.setVisible(True)
        self.result_scroll.setVisible(False)
        self.reset_btn.setVisible(False)
        self.question_input.clear()
        self.tosses = []
        self.current_toss = 0
        for lbl in self.toss_labels:
            lbl.setText("待投掷")
            lbl.setStyleSheet("font-size: 13px; color: #999; padding: 4px;")
        self.progress_label.setText("点击下方按钮开始投掷铜钱（共六次）")
        self.toss_btn.setText("开始投掷")
        self.toss_btn.setEnabled(True)

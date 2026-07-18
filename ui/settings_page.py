"""设置页 - AI 服务商配置"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox,
                                QLineEdit, QPushButton, QLabel, QFrame,
                                QMessageBox)
from PySide6.QtCore import Signal, Qt, QThread

from config import AI_PROVIDERS, AI_PROVIDER_MODELS, AI_DEFAULT_PROVIDER
from services.settings_service import (get_ai_config, save_ai_config,
                                        get_endpoint_by_provider)
from services.ai_service import test_connection


class TestConnectionWorker(QThread):
    """后台线程：测试API连接，避免界面卡死"""
    finished_signal = Signal(bool, str)  # (success, message)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        from services.ai_service import _call_api
        try:
            success, msg = test_connection(self.config)
            self.finished_signal.emit(success, msg)
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class SettingsPage(QWidget):
    """设置页面 - 配置AI服务商"""

    def __init__(self):
        super().__init__()
        self._worker = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # 标题
        title = QLabel("AI 解读设置")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        desc = QLabel("配置AI服务商后，可在占卜结果页和卦库页使用AI解读功能")
        desc.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(desc)

        # 表单卡片
        form_frame = QFrame()
        form_frame.setObjectName("cardFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        # 服务商下拉
        self.provider_combo = QComboBox()
        for name in AI_PROVIDERS.keys():
            self.provider_combo.addItem(name)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("服务商：", self.provider_combo)

        # API端点
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("API端点地址，如 https://api.deepseek.com")
        form_layout.addRow("API端点：", self.endpoint_input)

        # 模型名
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("模型名，如 deepseek-v4-flash")
        form_layout.addRow("模型名：", self.model_input)

        # API Key（密码模式）
        self.apikey_input = QLineEdit()
        self.apikey_input.setPlaceholderText("API Key")
        self.apikey_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key：", self.apikey_input)

        # 显示/隐藏Key按钮
        self.toggle_key_btn = QPushButton("显示")
        self.toggle_key_btn.setFixedWidth(60)
        self.toggle_key_btn.clicked.connect(self.toggle_key_visibility)
        form_layout.addRow("", self.toggle_key_btn)

        layout.addWidget(form_frame)

        # 按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.setFixedHeight(40)
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.clicked.connect(self.on_test_connection)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # 状态提示
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; color: #888;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 加载已保存的配置
        self._load_config()

    def _load_config(self):
        """加载已保存的配置到表单，无保存配置时使用默认服务商"""
        config = get_ai_config()

        if config["provider"]:
            # 有保存的配置，加载它
            idx = self.provider_combo.findText(config["provider"])
            if idx >= 0:
                self.provider_combo.blockSignals(True)
                self.provider_combo.setCurrentIndex(idx)
                self.provider_combo.blockSignals(False)
            self.endpoint_input.setText(config["endpoint"])
            self.model_input.setText(config["model"])
            self.apikey_input.setText(config["api_key"])
            self._update_model_placeholder(config["provider"])
        else:
            # 无保存配置，使用默认服务商 DeepSeek
            idx = self.provider_combo.findText(AI_DEFAULT_PROVIDER)
            if idx >= 0:
                self.provider_combo.blockSignals(True)
                self.provider_combo.setCurrentIndex(idx)
                self.provider_combo.blockSignals(False)
            # 自动填充默认端点
            default_endpoint = get_endpoint_by_provider(AI_DEFAULT_PROVIDER)
            self.endpoint_input.setText(default_endpoint)
            self._update_model_placeholder(AI_DEFAULT_PROVIDER)

        if config["configured"]:
            self.status_label.setText("当前已配置AI服务")
            self.status_label.setStyleSheet("font-size: 13px; color: #2a8c2a;")
        else:
            self.status_label.setText("尚未配置AI服务")
            self.status_label.setStyleSheet("font-size: 13px; color: #888;")

    def _update_model_placeholder(self, provider_name):
        """根据服务商更新模型名输入框的提示"""
        models = AI_PROVIDER_MODELS.get(provider_name, "")
        if models:
            self.model_input.setPlaceholderText(f"推荐：{models}")
        else:
            self.model_input.setPlaceholderText("模型名")

    def on_provider_changed(self, provider_name):
        """服务商切换时自动填充端点和模型提示"""
        endpoint = get_endpoint_by_provider(provider_name)
        if endpoint:  # 预设服务商，自动填充（自定义/Claude则不动）
            self.endpoint_input.setText(endpoint)
        self._update_model_placeholder(provider_name)

    def toggle_key_visibility(self):
        """切换API Key显示/隐藏"""
        if self.apikey_input.echoMode() == QLineEdit.EchoMode.Password:
            self.apikey_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("隐藏")
        else:
            self.apikey_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("显示")

    def _get_form_config(self) -> dict:
        """从表单获取配置字典"""
        endpoint = self.endpoint_input.text().strip()
        model = self.model_input.text().strip()
        api_key = self.apikey_input.text().strip()
        return {
            "provider": self.provider_combo.currentText(),
            "endpoint": endpoint,
            "model": model,
            "api_key": api_key,
            "configured": bool(endpoint and model and api_key),
        }

    def on_test_connection(self):
        """测试连接"""
        config = self._get_form_config()

        if not config["endpoint"] or not config["api_key"] or not config["model"]:
            QMessageBox.warning(self, "提示", "请先填写端点、模型名和API Key")
            return

        # 禁用按钮，显示测试中
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.status_label.setText("正在连接API...")
        self.status_label.setStyleSheet("font-size: 13px; color: #888;")

        # 后台线程测试
        self._worker = TestConnectionWorker(config)
        self._worker.finished_signal.connect(self.on_test_finished)
        self._worker.start()

    def on_test_finished(self, success, message):
        """测试连接完成回调"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")

        if success:
            self.status_label.setText("连接成功！")
            self.status_label.setStyleSheet("font-size: 13px; color: #2a8c2a;")
            QMessageBox.information(self, "连接成功", f"AI服务连接正常。\n\nAI回复：{message}")
        else:
            self.status_label.setText("连接失败")
            self.status_label.setStyleSheet("font-size: 13px; color: #c0392b;")
            QMessageBox.warning(self, "连接失败", message)

    def on_save(self):
        """保存配置"""
        config = self._get_form_config()

        if not config["endpoint"]:
            QMessageBox.warning(self, "提示", "请填写API端点")
            return
        if not config["model"]:
            QMessageBox.warning(self, "提示", "请填写模型名")
            return
        if not config["api_key"]:
            QMessageBox.warning(self, "提示", "请填写API Key")
            return

        save_ai_config(
            config["provider"],
            config["endpoint"],
            config["model"],
            config["api_key"],
        )

        self.status_label.setText("配置已保存")
        self.status_label.setStyleSheet("font-size: 13px; color: #2a8c2a;")
        QMessageBox.information(self, "保存成功", "AI配置已保存，现在可以使用AI解读功能了")

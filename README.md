# 易象（YiXiang）

本地周易六爻占卜助手

此项目含有未经科学证实的内容，请仔细甄别

此项目目前还有较多bugs，未来一段时间会进行修复。
未来会加入的功能：结果导出。（makedown、txt、pdf）
可能会开发安卓手机端和微信小程序版本
（这个readme其实也会再改改）

## 简介

《易象》是一款基于传统「三枚铜钱法」的数字化周易工具，支持离线运行与可选的 AI 辅助解读。

核心功能：
- 三枚铜钱模拟六爻起卦
- 自动计算本卦、动爻、变卦
- 周易原文与白话解释
- 占卜历史记录
- 六十四卦查询
- **AI 辅助解读**（v2.0.0 新增）
- **全新 UI 设计**（v2.1.0 新增）

## v2.1.0 更新内容：UI 全面升级

### 新增与改进

- **新中式极简设计**：宣纸白 + 墨黑 + 朱砂红 + 青灰配色，典雅古朴
- **卦象渲染重写**：QPainter 直接绘制 PNG 图片，完美兼容 QTextBrowser，显示效果精确可控
  - 阳爻整线、阴爻两段，每爻独立有间距，标准卦象结构
  - 老阳动爻右侧 ○ 标记（朱砂红）
  - 老阴动爻右侧 × 标记（朱砂红）
  - 本卦变卦左右并排双卡片布局，中间箭头指示变化方向
- **铜钱动画升级**：3D 旋转动画，更具仪式感
- **应用图标**：铜钱图案图标
- **字体优化**：系统宋体 + 黑体替代思源字体，开箱即用
- **窗口尺寸调整**：更符合桌面应用使用习惯
- **设置页优化**：显示/隐藏按钮尺寸修正，布局更合理
- **首页优化**：精简布局，移除冗余视觉元素

## v2.0.0 更新内容：AI 辅助解释功能

### 新增功能

- **多服务商支持**：内置 8 家 OpenAI 兼容格式的 AI 服务商
  - DeepSeek（默认）
  - 通义千问
  - Kimi（月之暗面）
  - 智谱GLM
  - OpenAI
  - Gemini
  - Claude（需第三方代理）
  - 自定义端点
- **AI 解读三处集成**：
  - 占卜结果页：对本卦、变卦、动爻综合解读
  - 历史记录页：对历史占卜记录重新解读
  - 卦库查询页：对单卦进行独立解读
- **配置管理**：
  - 设置页可配置服务商、API 端点、模型名、API Key
  - API Key 使用 XOR + base64 简单加密存储
  - 服务商切换时自动填充端点与推荐模型名
  - 支持连接测试
- **数据持久化**：AI 解读结果保存到数据库，下次查看时自动展示
- **后台线程调用**：QThread 异步请求，UI 不卡顿
- **优雅的错误处理**：超时、连接失败、认证失败、额度不足等 7 类异常友好提示
- **数据库迁移**：旧版 v1.0.x 数据库自动升级，不丢失历史记录

### 安全说明

- AI 调用需用户自行配置 API Key，**不会上传到任何第三方服务器**（仅发送至用户选择的服务商）
- API Key 在本地数据库中以 XOR + base64 简单加密存储，防止肉眼直接读取
- **未配置 AI 时，所有核心占卜功能完全离线可用**，AI 解读为可选增强功能

## 技术栈

- Python 3.13
- PySide6（GUI）
- SQLite（数据存储，原生 sqlite3）
- requests（AI API 调用）
- PyInstaller（打包）


## 项目结构

```
YiXiang/
├── main.py                 # 程序入口
├── config.py               # 应用配置（含 AI 服务商列表）
├── requirements.txt        # 依赖清单
├── YiXiang.spec            # PyInstaller 打包配置
├── ui/                     # PySide6 界面
│   ├── main_window.py      # 主窗口
│   ├── home_page.py        # 首页
│   ├── divination_page.py  # 起卦页（含 AI 解读）
│   ├── library_page.py     # 卦库页（含 AI 解读）
│   ├── history_page.py     # 历史页（含 AI 解读）
│   ├── settings_page.py    # 设置页（AI 配置）
│   ├── hexagram_renderer.py
│   └── styles.py
├── controllers/            # 控制器
├── services/               # 服务层
│   ├── ai_service.py       # AI 调用（OpenAI 兼容格式）
│   ├── settings_service.py # AI 配置读写与 Key 加解密
│   ├── divination_service.py
│   ├── interpretation_service.py
│   └── history_service.py  # 含 AI 解读存储
├── core/                   # 核心算法（铜钱、六爻、卦象）
├── models/                 # 数据模型
├── database/               # 数据库（schema + 迁移）
├── data/                   # JSON 初始数据
├── resources/              # 图标/图片资源
└── scripts/                # 工具与测试脚本
    ├── run_all_tests.py    # 全量测试入口
    ├── test_ai_service.py
    ├── test_settings_service.py
    ├── test_settings_page.py
    ├── test_divination_ai.py
    ├── test_history_ai.py
    ├── test_library_ai.py
    ├── test_db_extension.py
    ├── test_version.py
    └── ...
```

## 快速开始

### 开发环境运行

```bash
pip install -r requirements.txt
python main.py
```

### 运行测试

```bash
python scripts\run_all_tests.py
```

包含 9 个测试套件，覆盖核心算法、AI 服务层、设置服务、数据库扩展、三个页面的 AI 集成、版本号与打包配置。

### 打包为 exe

```bash
pyinstaller YiXiang.spec --noconfirm
```

生成的 exe 位于 `dist/易象.exe`（约 48 MB，单文件）。

## AI 配置指南

1. 启动程序，进入「设置」页
2. 选择服务商（默认 DeepSeek）
3. 端点会自动填充，如需自定义可手动修改
4. 填写模型名（如 `deepseek-v4-flash`）
5. 填写 API Key（可点击「显示」切换明文/密文）
6. 点击「测试连接」验证配置
7. 点击「保存配置」

配置完成后，在占卜结果页、历史记录页、卦库查询页均可点击「AI 解读」按钮获取 AI 辅助解读。

## 版本历史

- **v2.1.0**：UI 全面升级（新中式设计、卦象渲染重写、铜钱动画、应用图标）
- **v2.0.0**：新增 AI 辅助解释功能（多服务商、三处集成、数据持久化）
- **v1.0.2**：优化硬币与卦象图像
- **v1.0.1**：基础版本
- **v1.0.0**：周易六爻占卜桌面应用初始版本

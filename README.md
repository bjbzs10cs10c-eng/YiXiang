# 易象（YiXiang）

本地周易六爻占卜助手

## 简介

《易象》是一款基于传统「三枚铜钱法」的数字化周易工具，完全离线运行。

核心功能：
- 三枚铜钱模拟六爻起卦
- 自动计算本卦、动爻、变卦
- 周易原文与白话解释
- 占卜历史记录
- 六十四卦查询

## 技术栈

- Python 3.12
- PySide6（GUI）
- SQLite + SQLAlchemy（数据存储）
- PyInstaller（打包）

## 环境搭建

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 项目结构

```
YiXiang/
├── main.py                 # 程序入口
├── config.py               # 应用配置
├── requirements.txt        # 依赖清单
├── ui/                     # PySide6 界面
├── controllers/            # 控制器
├── services/               # 服务层
├── core/                   # 核心算法
├── models/                 # 数据模型
├── database/               # 数据库
├── data/                   # JSON 初始数据
├── resources/              # 图标/图片资源
├── scripts/                # 工具脚本
└── tests/                  # 测试
```

## 六爻规则

三枚铜钱法（文王六爻法）：

| 和值 | 名称 | 阴阳 | 动爻 |
|------|------|------|------|
| 6    | 老阴 | 阴   | 变阳 |
| 7    | 少阳 | 阳   | 不变 |
| 8    | 少阴 | 阴   | 不变 |
| 9    | 老阳 | 阳   | 变阴 |

## 许可

个人使用，小而美。

"""卦象图形渲染 - QPainter绘制图片方案，显示效果完全可控

用QPainter绘制卦象到QPixmap，转成base64 PNG嵌入HTML，
完全不依赖QTextBrowser的HTML/CSS渲染能力，显示效果100%可控。
"""

import base64
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QBuffer, QByteArray

COLOR_INK = "#2B2B2B"
COLOR_CINNABAR = "#B83A2E"
COLOR_CARD_BG = "#FFFBF2"
COLOR_BORDER = "#E5DCC8"
COLOR_SLATE = "#718096"


def _draw_hexagram(painter, x, y, width, binary_code, moving_positions=None):
    """在指定位置绘制六爻卦象

    Args:
        painter: QPainter对象
        x, y: 左上角坐标
        width: 卦象总宽度
        binary_code: 6位二进制字符串（第0位=上爻）
        moving_positions: 动爻位置集合
    """
    if moving_positions is None:
        moving_positions = set()

    yao_height = 8
    yao_gap = 12
    mark_offset = 10

    for i in range(6):
        pos = 6 - i
        ch = binary_code[i]
        is_yang = ch == "1"
        is_moving = pos in moving_positions

        color = QColor(COLOR_CINNABAR) if is_moving else QColor(COLOR_INK)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        y_yao = y + i * (yao_height + yao_gap)

        if is_yang:
            painter.drawRect(QRectF(x, y_yao, width, yao_height))
        else:
            seg_width = (width - yao_gap) / 2
            painter.drawRect(QRectF(x, y_yao, seg_width, yao_height))
            painter.drawRect(QRectF(x + seg_width + yao_gap, y_yao, seg_width, yao_height))

        if is_moving:
            painter.setPen(QColor(COLOR_CINNABAR))
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            mark_char = "○" if is_yang else "×"
            mark_x = x + width + mark_offset
            painter.drawText(QRectF(mark_x, y_yao - 1, 16, yao_height + 2),
                             Qt.AlignVCenter | Qt.AlignLeft, mark_char)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

    return


def _draw_hexagram_block(pixmap, x, y, width, height, title, name, binary_code, moving_positions=None):
    """绘制一个卦象卡片（标题+卦名+卦象）"""
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # 卡片背景和边框
    painter.setBrush(QColor(COLOR_CARD_BG))
    painter.setPen(QColor(COLOR_BORDER))
    painter.drawRoundedRect(QRectF(x, y, width, height), 8, 8)

    # 标题（本卦/变卦）
    painter.setPen(QColor(COLOR_SLATE))
    font = QFont()
    font.setPointSize(10)
    painter.setFont(font)
    painter.drawText(QRectF(x, y + 8, width, 20), Qt.AlignCenter, title)

    # 卦名
    painter.setPen(QColor(COLOR_INK))
    font = QFont("SimSun", 16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(QRectF(x, y + 30, width, 28), Qt.AlignCenter, name)

    # 卦象
    yao_width = 100
    yao_x = x + (width - yao_width) / 2 - 10
    yao_y = y + 70
    _draw_hexagram(painter, yao_x, yao_y, yao_width, binary_code, moving_positions)

    painter.end()


def render_hexagram_image_base64(binary_code, moving_positions=None, width=180, height=260):
    """生成卦象图片的base64编码"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    yao_width = 100
    x = (width - yao_width) / 2 - 10
    y = (height - (8 * 6 + 12 * 5)) / 2
    _draw_hexagram(painter, x, y, yao_width, binary_code, moving_positions)
    painter.end()

    buffer = QBuffer()
    buffer.open(QBuffer.ReadWrite)
    pixmap.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return base64.b64encode(data).decode("ascii")


def render_dual_hexagram_image_base64(orig_name, orig_binary, changed_name, changed_binary,
                                       moving_positions=None, width=620, height=280):
    """生成本卦+变卦双卡片图片的base64编码"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    arrow_width = 60
    card_width = (width - arrow_width - 20) / 2
    card_height = height - 20
    card_y = 10

    # 本卦卡片
    _draw_hexagram_block(pixmap, 10, card_y, card_width, card_height,
                         "本卦", orig_name, orig_binary, moving_positions)

    # 箭头
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QColor(COLOR_CINNABAR))
    font = QFont()
    font.setPointSize(28)
    painter.setFont(font)
    arrow_x = 10 + card_width
    painter.drawText(QRectF(arrow_x, card_y, arrow_width, card_height), Qt.AlignCenter, "→")
    painter.end()

    # 变卦卡片
    _draw_hexagram_block(pixmap, width - card_width - 10, card_y, card_width, card_height,
                         "变卦", changed_name, changed_binary)

    buffer = QBuffer()
    buffer.open(QBuffer.ReadWrite)
    pixmap.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return base64.b64encode(data).decode("ascii")


def render_dual_hexagram_block(orig_name, orig_binary, changed_name, changed_binary, moving_positions=None):
    """生成本卦+变卦左右并排双卡片HTML（用图片渲染，显示效果完全可控）"""
    img_b64 = render_dual_hexagram_image_base64(
        orig_name, orig_binary, changed_name, changed_binary, moving_positions
    )
    return '<div align="center"><img src="data:image/png;base64,{}"/></div>'.format(img_b64)


def render_hexagram_block(name, binary_code, moving_positions=None):
    """生成卦象名称+六爻图形的HTML块（用图片渲染）"""
    img_b64 = render_hexagram_image_base64(binary_code, moving_positions, width=200, height=240)
    return (
        '<div align="center" style="padding:8px 0;">'
        '<div style="font-size:22px; font-weight:bold; color:#2B2B2B; '
        'font-family:SimSun,宋体,serif; margin-bottom:8px;">{}</div>'
        '<img src="data:image/png;base64,{}"/>'
        '</div>'
    ).format(name, img_b64)


def render_hexagram_lines(binary_code, moving_positions=None):
    """生成六爻卦象HTML（用图片渲染）"""
    img_b64 = render_hexagram_image_base64(binary_code, moving_positions, width=140, height=180)
    return '<div align="center"><img src="data:image/png;base64,{}"/></div>'.format(img_b64)

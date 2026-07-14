"""卦象图形渲染 - 阳爻实线、阴爻两段，CSS纯色块方案"""


def _yao_line_html(is_yang, color="#333"):
    if is_yang:
        return '<div style="width:120px; height:8px; background:{}; margin:4px auto; border-radius:2px;"></div>'.format(color)
    else:
        return (
            '<div style="display:flex; justify-content:center; gap:16px; margin:4px 0;">'
            '<div style="width:48px; height:8px; background:{}; border-radius:2px;"></div>'
            '<div style="width:48px; height:8px; background:{}; border-radius:2px;"></div>'
            '</div>'
        ).format(color, color)


def render_hexagram_lines(binary_code, moving_positions=None):
    """生成六爻卦象HTML，从上到下（上爻→初爻）

    Args:
        binary_code: 6位二进制字符串，第0位=上爻
        moving_positions: 动爻位置集合（1=初爻, 6=上爻），可选

    Returns:
        HTML字符串
    """
    if moving_positions is None:
        moving_positions = set()

    lines = []
    for i, ch in enumerate(binary_code):
        pos = 6 - i
        is_yang = ch == "1"
        is_moving = pos in moving_positions
        color = "#b8860b" if is_moving else "#333"
        lines.append(_yao_line_html(is_yang, color))
    return '<div style="padding:8px 0;">' + "".join(lines) + "</div>"


def render_hexagram_block(name, binary_code, moving_positions=None):
    """生成卦象名称+六爻图形的HTML块

    Args:
        name: 卦名
        binary_code: 6位二进制字符串
        moving_positions: 动爻位置集合，可选

    Returns:
        HTML字符串
    """
    lines_html = render_hexagram_lines(binary_code, moving_positions)
    return (
        '<div style="text-align:center; padding:12px 0;">'
        '<div style="font-size:18px; font-weight:bold; color:#2c2c2c;">{}</div>'
        '{}'
        '</div>'
    ).format(name, lines_html)


def render_dual_hexagram_block(orig_name, orig_binary, changed_name, changed_binary, moving_positions=None):
    """生成本卦+变卦双卦对比HTML块

    Args:
        orig_name: 本卦卦名
        orig_binary: 本卦二进制编码
        changed_name: 变卦卦名
        changed_binary: 变卦二进制编码
        moving_positions: 动爻位置集合，可选

    Returns:
        HTML字符串
    """
    orig_block = render_hexagram_block(orig_name, orig_binary, moving_positions)
    arrow = '<div style="text-align:center; font-size:28px; color:#b8860b; padding:8px 0;">↓</div>'
    changed_block = render_hexagram_block(changed_name, changed_binary)

    return (
        '<div style="display:flex; justify-content:center; align-items:center; gap:40px; padding:16px 0;">'
        '<div>{}</div>'
        '<div>{}</div>'
        '<div>{}</div>'
        '</div>'
    ).format(orig_block, arrow, changed_block)

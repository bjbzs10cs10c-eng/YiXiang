"""变卦模块 - 动爻变化与变卦计算"""

from typing import Optional


def transform_yao(value: int) -> Optional[int]:
    """单爻变化

    Args:
        value: 爻值 6/7/8/9

    Returns:
        变化后的值：6→9(阴变阳), 9→6(阳变阴), 7/8不变返回None
    """
    if value == 6:
        return 9  # 老阴变阳
    elif value == 9:
        return 6  # 老阳变阴
    return None  # 少阳/少阴不变


def get_changing_binary(binary_code: str, moving_positions: list) -> str:
    """根据动爻位置生成变卦二进制编码

    Args:
        binary_code: 本卦二进制编码（上爻→初爻）
        moving_positions: 动爻位置列表（1-6，1=初爻）

    Returns:
        变卦二进制编码
    """
    chars = list(binary_code)
    for pos in moving_positions:
        idx = 6 - pos  # 位置1=初爻→索引5, 位置6=上爻→索引0
        chars[idx] = "1" if chars[idx] == "0" else "0"
    return "".join(chars)

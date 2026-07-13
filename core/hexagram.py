"""卦象模块 - 本卦生成与匹配"""

from typing import Optional

from core.yao import Yao


class Hexagram:
    """卦象

    内部六爻顺序：yaos[0]=初爻, yaos[5]=上爻（从下往上）
    binary_code 顺序：上爻→初爻（从上往下），与数据库编码一致
    """

    def __init__(self, yaos: list):
        """初始化卦象

        Args:
            yaos: 六个 Yao 对象列表，yaos[0]=初爻, yaos[5]=上爻
        """
        self.yaos = yaos

    @property
    def binary_code(self) -> str:
        """生成二进制编码（上爻→初爻）

        阳=1，阴=0，从上爻到初爻排列，与数据库 binary_code 一致
        """
        # yaos[5]=上爻 在前，yaos[0]=初爻 在后
        return "".join(yao.binary for yao in reversed(self.yaos))

    @property
    def upper_trigram_code(self) -> str:
        """上卦三爻编码（上爻、五爻、四爻）"""
        return "".join(self.yaos[i].binary for i in [5, 4, 3])

    @property
    def lower_trigram_code(self) -> str:
        """下卦三爻编码（三爻、二爻、初爻）"""
        return "".join(self.yaos[i].binary for i in [2, 1, 0])

    def get_moving_lines(self) -> list:
        """获取所有动爻位置

        Returns:
            动爻位置列表，位置从1到6（1=初爻, 6=上爻）
        """
        return [yao.position for yao in self.yaos if yao.changing]

    def get_changing_binary(self) -> Optional[str]:
        """生成变卦二进制编码

        规则：动爻阴阳反转，非动爻保持不变

        Returns:
            变卦二进制编码，无动爻时返回None（静卦）
        """
        moving = self.get_moving_lines()
        if not moving:
            return None

        chars = list(self.binary_code)
        # binary_code 顺序：上爻→初爻
        # 位置1=初爻对应索引5，位置6=上爻对应索引0
        for pos in moving:
            idx = 6 - pos
            chars[idx] = "1" if chars[idx] == "0" else "0"
        return "".join(chars)

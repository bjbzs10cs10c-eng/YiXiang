"""爻模块 - 爻的数据结构与判断规则"""

from dataclasses import dataclass


# 爻值规则映射
YAO_RULES = {
    6: {"name": "老阴", "yin_yang": "阴", "changing": True},
    7: {"name": "少阳", "yin_yang": "阳", "changing": False},
    8: {"name": "少阴", "yin_yang": "阴", "changing": False},
    9: {"name": "老阳", "yin_yang": "阳", "changing": True},
}


@dataclass
class Yao:
    """爻"""
    value: int       # 6/7/8/9
    position: int    # 1-6（初爻到上爻）
    yin_yang: str = ""    # 阴/阳
    changing: bool = False  # 是否动爻
    name: str = ""    # 老阴/少阳/少阴/老阳

    def __post_init__(self):
        rule = YAO_RULES.get(self.value)
        if rule:
            self.yin_yang = rule["yin_yang"]
            self.changing = rule["changing"]
            self.name = rule["name"]

    @property
    def binary(self) -> str:
        """返回二进制表示：阳=1，阴=0"""
        return "1" if self.yin_yang == "阳" else "0"

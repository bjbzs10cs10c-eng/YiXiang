"""铜钱模拟模块 - 三枚铜钱法"""

import random

from core.yao import YAO_RULES


COIN_FRONT = 3  # 正面值
COIN_BACK = 2   # 反面值


def toss_single_coin() -> int:
    """模拟投掷一枚铜钱，返回正面(3)或反面(2)"""
    return random.choice([COIN_FRONT, COIN_BACK])


def toss_three_coins() -> dict:
    """模拟一次投掷三枚铜钱

    返回:
        {"coins": [3,3,2], "value": 8, "name": "少阴"}
    """
    coins = [toss_single_coin() for _ in range(3)]
    value = sum(coins)
    name = YAO_RULES[value]["name"]
    return {"coins": coins, "value": value, "name": name}

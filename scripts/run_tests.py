"""核心算法测试 - 无需pytest，直接运行"""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.coin import toss_single_coin, toss_three_coins, COIN_FRONT, COIN_BACK
from core.yao import Yao, YAO_RULES
from core.hexagram import Hexagram


def make_yaos(values):
    """用爻值列表创建六爻，values[0]=初爻"""
    return [Yao(value=v, position=i + 1) for i, v in enumerate(values)]


passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


print("=" * 50)
print("测试1: 铜钱模拟")
print("=" * 50)

# 单枚铜钱返回值
for _ in range(100):
    r = toss_single_coin()
    assert r in (COIN_FRONT, COIN_BACK), f"单枚铜钱返回值错误: {r}"
check("单枚铜钱返回3或2", True)

# 三枚求和范围
ok = True
for _ in range(100):
    r = toss_three_coins()
    if r["value"] not in (6, 7, 8, 9):
        ok = False
        break
    if len(r["coins"]) != 3:
        ok = False
        break
    if sum(r["coins"]) != r["value"]:
        ok = False
        break
    if r["name"] != YAO_RULES[r["value"]]["name"]:
        ok = False
        break
check("三枚铜钱求和在6-9之间", ok)

# 四种值都能出现
random.seed(42)
values = set()
for _ in range(1000):
    values.add(toss_three_coins()["value"])
check("四种和值6/7/8/9都能出现", values == {6, 7, 8, 9})


print()
print("=" * 50)
print("测试2: 6/7/8/9规则")
print("=" * 50)

# 6=老阴
yao = Yao(value=6, position=1)
check("6=老阴 阴 动爻", yao.yin_yang == "阴" and yao.changing is True and yao.name == "老阴")
check("6 binary=0", yao.binary == "0")

# 7=少阳
yao = Yao(value=7, position=2)
check("7=少阳 阳 不变", yao.yin_yang == "阳" and yao.changing is False and yao.name == "少阳")
check("7 binary=1", yao.binary == "1")

# 8=少阴
yao = Yao(value=8, position=3)
check("8=少阴 阴 不变", yao.yin_yang == "阴" and yao.changing is False and yao.name == "少阴")
check("8 binary=0", yao.binary == "0")

# 9=老阳
yao = Yao(value=9, position=4)
check("9=老阳 阳 动爻", yao.yin_yang == "阳" and yao.changing is True and yao.name == "老阳")
check("9 binary=1", yao.binary == "1")

# 爻位
positions_ok = all(Yao(value=7, position=p).position == p for p in range(1, 7))
check("爻位1-6正确", positions_ok)


print()
print("=" * 50)
print("测试3: 卦象编码")
print("=" * 50)

# 乾卦
h = Hexagram(make_yaos([7, 7, 7, 7, 7, 7]))
check("乾卦 binary=111111", h.binary_code == "111111")

# 坤卦
h = Hexagram(make_yaos([8, 8, 8, 8, 8, 8]))
check("坤卦 binary=000000", h.binary_code == "000000")

# 水雷屯(坎上震下)
# 震(下): 初阳二阴三阴, 坎(上): 四阴五阳上阴
h = Hexagram(make_yaos([7, 8, 8, 8, 7, 8]))
check("水雷屯 binary=010001", h.binary_code == "010001")
check("水雷屯 上卦=010(坎)", h.upper_trigram_code == "010")
check("水雷屯 下卦=001(震)", h.lower_trigram_code == "001")

# 天地否(乾上坤下)
h = Hexagram(make_yaos([8, 8, 8, 7, 7, 7]))
check("天地否 binary=111000", h.binary_code == "111000")
check("天地否 上卦=111(乾)", h.upper_trigram_code == "111")
check("天地否 下卦=000(坤)", h.lower_trigram_code == "000")


print()
print("=" * 50)
print("测试4: 动爻判断")
print("=" * 50)

# 单动爻
h = Hexagram(make_yaos([7, 7, 7, 7, 9, 7]))
check("九五动: moving=[5]", h.get_moving_lines() == [5])

# 多动爻
h = Hexagram(make_yaos([6, 7, 9, 7, 7, 7]))
check("初爻+三爻动: moving=[1,3]", h.get_moving_lines() == [1, 3])

# 静卦
h = Hexagram(make_yaos([7, 8, 7, 8, 7, 8]))
check("静卦: moving=[]", h.get_moving_lines() == [])
check("静卦: 无变卦", h.get_changing_binary() is None)


print()
print("=" * 50)
print("测试5: 变卦计算")
print("=" * 50)

# 乾九五动 → 火天大有
h = Hexagram(make_yaos([7, 7, 7, 7, 9, 7]))
check("乾九五动: 本卦=111111", h.binary_code == "111111")
check("乾九五动: 变卦=101111(火天大有)", h.get_changing_binary() == "101111")

# 六爻全动: 乾→坤
h = Hexagram(make_yaos([9, 9, 9, 9, 9, 9]))
check("乾全动: 变卦=000000(坤)", h.get_changing_binary() == "000000")

# 坤初爻动 → 地雷复
h = Hexagram(make_yaos([6, 8, 8, 8, 8, 8]))
check("坤初爻动: 变卦=000001(地雷复)", h.get_changing_binary() == "000001")

# 混合动爻：初爻老阴(0)+五爻老阳(1)，其余少阴(0)
# binary_code = 上(0)五(1)四(0)三(0)二(0)初(0) = 010000
# 变卦：初爻位置1→索引5翻转0→1，五爻位置5→索引1翻转1→0
# 010000 → 000001
h = Hexagram(make_yaos([6, 8, 8, 8, 9, 8]))
check("混合动(初+五): 本卦=010000", h.binary_code == "010000")
check("混合动(初+五): 变卦=000001", h.get_changing_binary() == "000001")


print()
print("=" * 50)
print(f"结果: {passed} passed, {failed} failed")
print("=" * 50)

sys.exit(1 if failed > 0 else 0)

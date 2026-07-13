"""核心算法测试 - 6/7/8/9规则验证"""

import random

from core.coin import toss_single_coin, toss_three_coins, COIN_FRONT, COIN_BACK
from core.yao import Yao, YAO_RULES
from core.hexagram import Hexagram


class TestCoin:
    """铜钱模拟测试"""

    def test_single_coin_returns_valid_value(self):
        """单枚铜钱只能返回3或2"""
        for _ in range(100):
            result = toss_single_coin()
            assert result in (COIN_FRONT, COIN_BACK)

    def test_three_coins_sum_range(self):
        """三枚铜钱求和结果只能在6-9之间"""
        for _ in range(100):
            result = toss_three_coins()
            assert result["value"] in (6, 7, 8, 9)
            assert len(result["coins"]) == 3
            # 每枚只能是2或3
            for coin in result["coins"]:
                assert coin in (2, 3)
            # 和值正确
            assert sum(result["coins"]) == result["value"]
            # 名称正确
            assert result["name"] == YAO_RULES[result["value"]]["name"]

    def test_three_coins_all_combinations(self):
        """验证四种和值都能出现（随机种子覆盖）"""
        random.seed(42)
        values = set()
        for _ in range(1000):
            values.add(toss_three_coins()["value"])
        assert values == {6, 7, 8, 9}


class TestYaoRules:
    """6/7/8/9规则测试"""

    def test_old_yin_6(self):
        """6=老阴，阴，动爻"""
        yao = Yao(value=6, position=1)
        assert yao.yin_yang == "阴"
        assert yao.changing is True
        assert yao.name == "老阴"
        assert yao.binary == "0"

    def test_young_yang_7(self):
        """7=少阳，阳，不变"""
        yao = Yao(value=7, position=2)
        assert yao.yin_yang == "阳"
        assert yao.changing is False
        assert yao.name == "少阳"
        assert yao.binary == "1"

    def test_young_yin_8(self):
        """8=少阴，阴，不变"""
        yao = Yao(value=8, position=3)
        assert yao.yin_yang == "阴"
        assert yao.changing is False
        assert yao.name == "少阴"
        assert yao.binary == "0"

    def test_old_yang_9(self):
        """9=老阳，阳，动爻"""
        yao = Yao(value=9, position=4)
        assert yao.yin_yang == "阳"
        assert yao.changing is True
        assert yao.name == "老阳"
        assert yao.binary == "1"

    def test_yao_positions(self):
        """爻位1-6"""
        for pos in range(1, 7):
            yao = Yao(value=7, position=pos)
            assert yao.position == pos


class TestHexagram:
    """卦象测试"""

    def _make_yaos(self, values):
        """用爻值列表创建六爻，values[0]=初爻"""
        return [Yao(value=v, position=i + 1) for i, v in enumerate(values)]

    def test_qian_binary_code(self):
        """乾卦（全阳）binary_code = 111111"""
        yaos = self._make_yaos([7, 7, 7, 7, 7, 7])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "111111"

    def test_kun_binary_code(self):
        """坤卦（全阴）binary_code = 000000"""
        yaos = self._make_yaos([8, 8, 8, 8, 8, 8])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "000000"

    def test_tun_binary_code(self):
        """水雷屯（3号卦）：坎上震下
        震(下)：初阳二阴三阴 = 001
        坎(上)：四阴五阳上阴 = 010
        binary_code = 上爻→初爻 = 010001
        """
        # 震=阳阴阴（初/二/三），坎=阴阳阴（四/五/上）
        yaos = self._make_yaos([7, 8, 8, 8, 7, 8])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "010001"
        assert hexagram.upper_trigram_code == "010"  # 坎
        assert hexagram.lower_trigram_code == "001"  # 震

    def test_moving_lines_single(self):
        """单动爻：第五爻动"""
        yaos = self._make_yaos([7, 7, 7, 7, 9, 7])
        hexagram = Hexagram(yaos)
        moving = hexagram.get_moving_lines()
        assert moving == [5]

    def test_moving_lines_multiple(self):
        """多动爻：初爻和三爻动"""
        yaos = self._make_yaos([6, 7, 9, 7, 7, 7])
        hexagram = Hexagram(yaos)
        moving = hexagram.get_moving_lines()
        assert moving == [1, 3]

    def test_no_moving_lines(self):
        """静卦：无动爻"""
        yaos = self._make_yaos([7, 8, 7, 8, 7, 8])
        hexagram = Hexagram(yaos)
        assert hexagram.get_moving_lines() == []
        assert hexagram.get_changing_binary() is None

    def test_changing_binary_single(self):
        """变卦：乾九五动 → 变卦为火天大有（14号卦）
        乾=111111，五爻动(阳变阴)，binary_code索引1翻转
        101111 = 离上乾下 = 火天大有
        """
        yaos = self._make_yaos([7, 7, 7, 7, 9, 7])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "111111"
        assert hexagram.get_changing_binary() == "101111"

    def test_changing_binary_all_moving(self):
        """六爻全动：乾→坤"""
        yaos = self._make_yaos([9, 9, 9, 9, 9, 9])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "111111"
        assert hexagram.get_changing_binary() == "000000"

    def test_changing_binary_old_yin(self):
        """老阴变阳：坤初爻动 → 地雷复"""
        yaos = self._make_yaos([6, 8, 8, 8, 8, 8])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "000000"
        # 初爻动(阴变阳)，索引5翻转
        assert hexagram.get_changing_binary() == "000001"

    def test_changing_binary_mixed(self):
        """混合动爻：初爻老阴(0)+五爻老阳(1)，其余少阴(0)
        binary_code = 上(0)五(1)四(0)三(0)二(0)初(0) = 010000
        初爻位置1→索引5翻转：0→1
        五爻位置5→索引1翻转：1→0
        变卦 = 000001
        """
        yaos = self._make_yaos([6, 8, 8, 8, 9, 8])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "010000"
        # 初爻(位置1):索引5 翻转 0→1
        # 五爻(位置5):索引1 翻转 1→0
        assert hexagram.get_changing_binary() == "000001"

    def test_upper_lower_trigram(self):
        """天地否（12号卦）：乾上坤下
        乾=111，坤=000
        binary_code = 111000
        """
        yaos = self._make_yaos([8, 8, 8, 7, 7, 7])
        hexagram = Hexagram(yaos)
        assert hexagram.binary_code == "111000"
        assert hexagram.upper_trigram_code == "111"  # 乾
        assert hexagram.lower_trigram_code == "000"  # 坤

"""深度数据验证脚本"""

import sqlite3

conn = sqlite3.connect("database/yijing.db")
c = conn.cursor()

trigram_yin_yang = {
    "乾": ["阳","阳","阳"], "坤": ["阴","阴","阴"],
    "震": ["阳","阴","阴"], "巽": ["阴","阳","阳"],
    "坎": ["阴","阳","阴"], "离": ["阳","阴","阳"],
    "艮": ["阴","阴","阳"], "兑": ["阳","阳","阴"],
}
trigram_bin = {"乾":"111","兑":"011","离":"101","震":"001","巽":"110","坎":"010","艮":"100","坤":"000"}

# 1. 爻阴阳与卦结构一致性
yao_errors = 0
for hid in range(1, 65):
    c.execute("SELECT upper_trigram, lower_trigram FROM hexagrams WHERE id=?", (hid,))
    upper, lower = c.fetchone()
    expected = trigram_yin_yang[lower] + trigram_yin_yang[upper]
    c.execute("SELECT position, yao_type FROM yao_lines WHERE hexagram_id=? AND position<=6 ORDER BY position", (hid,))
    for pos, yt in c.fetchall():
        if yt != expected[pos-1]:
            yao_errors += 1
            print(f"  YAO ERROR: hex={hid} pos={pos} expected={expected[pos-1]} got={yt}")
result1 = "PASS" if yao_errors == 0 else f"FAIL({yao_errors})"
print(f"1. 爻阴阳校验: {result1}")

# 2. binary_code 与上下卦组合
bin_errors = 0
c.execute("SELECT id, binary_code, upper_trigram, lower_trigram FROM hexagrams")
for hid, bc, upper, lower in c.fetchall():
    if bc != trigram_bin[upper] + trigram_bin[lower]:
        bin_errors += 1
        print(f"  BIN ERROR: hex={hid} binary={bc} expected={trigram_bin[upper]+trigram_bin[lower]}")
result2 = "PASS" if bin_errors == 0 else f"FAIL({bin_errors})"
print(f"2. binary_code校验: {result2}")

# 3. yao_name 与 yao_type 一致性
name_errors = 0
c.execute("SELECT hexagram_id, position, yao_name, yao_type FROM yao_lines WHERE position<=6")
for hid, pos, yname, ytype in c.fetchall():
    if ytype == "阳" and "六" in yname:
        name_errors += 1
        print(f"  NAME ERROR: hex={hid} pos={pos} {yname} should be 阳 not 阴")
    elif ytype == "阴" and "九" in yname:
        name_errors += 1
        print(f"  NAME ERROR: hex={hid} pos={pos} {yname} should be 阴 not 阳")
result3 = "PASS" if name_errors == 0 else f"FAIL({name_errors})"
print(f"3. yao_name与yao_type校验: {result3}")

# 4. 统计
c.execute("SELECT COUNT(*) FROM hexagrams")
print(f"4. 六十四卦数量: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM yao_lines WHERE position<=6")
print(f"5. 标准爻辞数量: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM yao_lines WHERE position=7")
print(f"6. 用爻数量: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM interpretations")
print(f"7. 解释数量: {c.fetchone()[0]}")
c.execute("SELECT COUNT(DISTINCT target_id) FROM interpretations WHERE target_type='hexagram'")
print(f"8. 解释覆盖卦数: {c.fetchone()[0]}")

conn.close()

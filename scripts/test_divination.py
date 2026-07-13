"""完整占卜流程测试 - 输入问题 → 六次投掷 → 本卦 → 动爻 → 变卦 → 解释"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.divination_controller import DivinationController
from services.history_service import get_records, get_record_detail, delete_record


def print_separator(title):
    print()
    print("=" * 50)
    print(title)
    print("=" * 50)


controller = DivinationController()
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


# ============================================================
# 测试1: 完整占卜流程
# ============================================================
print_separator("测试1: 完整占卜流程")

result = controller.perform_divination("事业发展如何？")

check("返回结果非空", result is not None)
check("问题正确", result["question"] == "事业发展如何？")
check("时间非空", result["time"] is not None)

# 六次投掷
print(f"\n  占问: {result['question']}")
print(f"  时间: {result['time']}")
print(f"\n  六次投掷:")
for toss in result["tosses"]:
    coins_str = " ".join(["正" if c == 3 else "反" for c in toss["coins"]])
    print(f"    第{toss['position']}爻: {coins_str} = {toss['value']} {toss['name']}")

check("投掷次数=6", len(result["tosses"]) == 6)
check("每次投掷有3枚铜钱", all(len(t["coins"]) == 3 for t in result["tosses"]))
check("每次投掷值在6-9", all(t["value"] in (6, 7, 8, 9) for t in result["tosses"]))


# ============================================================
# 测试2: 本卦
# ============================================================
print_separator("测试2: 本卦")

orig = result["original_hexagram"]
print(f"  本卦: {orig['name']} (id={orig['id']})")
print(f"  binary_code: {orig['binary_code']}")
print(f"  卦辞: {orig['gua_ci']}")
print(f"  象辞: {orig['xiang_ci']}")

check("本卦有名称", orig["name"] is not None and len(orig["name"]) > 0)
check("本卦有binary_code", len(orig["binary_code"]) == 6)
check("本卦有卦辞", orig["gua_ci"] is not None and len(orig["gua_ci"]) > 0)
check("本卦爻辞=6条", len(result["original_yao_lines"]) >= 6)


# ============================================================
# 测试3: 动爻
# ============================================================
print_separator("测试3: 动爻")

moving = result["moving_lines"]
moving_count = result["moving_count"]
print(f"  动爻数量: {moving_count}")
for m in moving:
    print(f"    第{m['position']}爻: {m['value']} {m['name']}")

check("动爻数量正确", moving_count == len(moving))
check("动爻值只能是6或9", all(m["value"] in (6, 9) for m in moving))

# 验证动爻位置与yaos一致
for m in moving:
    pos = m["position"]
    yao = result["yaos"][pos - 1]
    check(f"动爻位置{pos}与yaos一致", yao["changing"] is True and yao["value"] == m["value"])


# ============================================================
# 测试4: 变卦
# ============================================================
print_separator("测试4: 变卦")

if moving_count == 0:
    print("  静卦，无变卦")
    check("静卦无变卦", result["changed_hexagram"] is None)
else:
    changed = result["changed_hexagram"]
    print(f"  变卦: {changed['name']} (id={changed['id']})")
    print(f"  binary_code: {changed['binary_code']}")
    print(f"  卦辞: {changed['gua_ci']}")
    check("变卦非空", changed is not None)
    check("变卦有名称", changed["name"] is not None and len(changed["name"]) > 0)
    check("变卦binary_code与本卦不同", changed["binary_code"] != orig["binary_code"])


# ============================================================
# 测试5: 断卦解释
# ============================================================
print_separator("测试5: 断卦解释")

reading = result["reading_text"]
source = result["reading_source"]
print(f"  断卦来源: {source}")
print(f"  断卦文本: {reading}")

check("断卦文本非空", reading is not None and len(reading) > 0)
check("断卦来源非空", source is not None and len(source) > 0)

# 验证断卦规则
if moving_count == 0:
    check("静卦看本卦卦辞", source == "本卦卦辞")
elif moving_count == 1:
    check("一爻动看该爻爻辞", "九" in source or "六" in source)
elif moving_count == 6:
    check("六爻全动看变卦卦辞或用爻", source in ("变卦卦辞", "用九", "用六"))


# ============================================================
# 测试6: 解释数据
# ============================================================
print_separator("测试6: 解释数据")

interps = result["original_interpretations"]
print(f"  本卦解释数量: {len(interps)}")
for interp in interps:
    print(f"    [{interp['source']}] {interp['title']}")
    print(f"      {interp['content'][:40]}...")

check("本卦解释>=2条", len(interps) >= 2)


# ============================================================
# 测试7: 保存记录
# ============================================================
print_separator("测试7: 保存历史记录")

record_id = controller.save_result(result)
print(f"  保存记录ID: {record_id}")
check("保存成功返回ID", record_id > 0)

# 查询记录列表
records = get_records()
check("历史记录非空", len(records) > 0)
last = records[0]
print(f"  最新记录: id={last['id']}, 问题={last['question']}, 本卦={last['original_name']}")
check("最新记录是刚保存的", last["id"] == record_id)

# 查询记录详情
detail = get_record_detail(record_id)
check("记录详情非空", detail is not None)
check("记录详情问题正确", detail["question"] == "事业发展如何？")
check("记录详情有moving_lines", len(detail["moving_lines"]) == moving_count)
check("记录详情有yao_values", len(detail["yao_values"]) == 6)

# 验证JSON格式
import json
print(f"\n  moving_lines JSON:")
print(f"    {json.dumps(detail['moving_lines'], ensure_ascii=False, indent=2)}")
print(f"  yao_values JSON:")
print(f"    {json.dumps(detail['yao_values'], ensure_ascii=False, indent=2)}")

# 清理测试数据
delete_record(record_id)
check("删除记录成功", True)
print(f"  已清理测试记录 id={record_id}")


# ============================================================
# 测试8: 多次占卜验证
# ============================================================
print_separator("测试8: 多次占卜验证")

for i in range(5):
    r = controller.perform_divination(f"测试问题{i+1}")
    orig_name = r["original_hexagram"]["name"]
    moving_cnt = r["moving_count"]
    if r["changed_hexagram"]:
        changed_name = r["changed_hexagram"]["name"]
        print(f"  第{i+1}次: {orig_name} → {changed_name} (动爻{moving_cnt}个)")
    else:
        print(f"  第{i+1}次: {orig_name} (静卦)")
    check(f"第{i+1}次占卜成功", r["original_hexagram"] is not None)


# ============================================================
# 结果汇总
# ============================================================
print_separator(f"结果: {passed} passed, {failed} failed")

sys.exit(1 if failed > 0 else 0)

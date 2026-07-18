"""易象 v2.0.0 全量测试 - 一键运行所有测试脚本

运行方式:
    python scripts\run_all_tests.py

执行顺序:
1. 核心算法测试 (run_tests.py)
2. AI服务层测试 (test_ai_service.py)
3. 设置服务测试 (test_settings_service.py)
4. 数据库扩展测试 (test_db_extension.py)
5. 设置页UI测试 (test_settings_page.py)
6. 占卜页AI测试 (test_divination_ai.py)
7. 历史页AI测试 (test_history_ai.py)
8. 卦库页AI测试 (test_library_ai.py)
9. 版本号与打包配置测试 (test_version.py)
"""

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 测试脚本清单（按顺序执行）
TESTS = [
    ("核心算法测试", "scripts/run_tests.py"),
    ("AI服务层测试", "scripts/test_ai_service.py"),
    ("设置服务测试", "scripts/test_settings_service.py"),
    ("数据库扩展测试", "scripts/test_db_extension.py"),
    ("设置页UI测试", "scripts/test_settings_page.py"),
    ("占卜页AI测试", "scripts/test_divination_ai.py"),
    ("历史页AI测试", "scripts/test_history_ai.py"),
    ("卦库页AI测试", "scripts/test_library_ai.py"),
    ("版本号与打包配置测试", "scripts/test_version.py"),
]


def main():
    print("=" * 70)
    print("易象 v2.0.0 全量测试")
    print("=" * 70)
    print()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable

    total_passed = 0
    total_failed = 0
    failed_tests = []

    for name, script in TESTS:
        script_path = os.path.join(project_root, script)
        print(f"▶ 执行: {name} ({script})")
        print("-" * 70)

        if not os.path.exists(script_path):
            print(f"  ✗ 脚本不存在: {script_path}")
            total_failed += 1
            failed_tests.append(f"{name} (脚本不存在)")
            print()
            continue

        try:
            result = subprocess.run(
                [python, script_path],
                cwd=project_root,
                capture_output=False,
                text=True,
                encoding="utf-8",
            )
            exit_code = result.returncode
            if exit_code == 0:
                total_passed += 1
                print(f"  ✓ {name} 通过")
            else:
                total_failed += 1
                failed_tests.append(name)
                print(f"  ✗ {name} 失败 (exit code: {exit_code})")
        except Exception as e:
            total_failed += 1
            failed_tests.append(f"{name} (异常: {e})")
            print(f"  ✗ {name} 异常: {e}")

        print()

    print("=" * 70)
    print("全量测试总结")
    print("=" * 70)
    print(f"通过测试套件: {total_passed}/{len(TESTS)}")
    print(f"失败测试套件: {total_failed}/{len(TESTS)}")
    if failed_tests:
        print("\n失败列表:")
        for t in failed_tests:
            print(f"  - {t}")
    print("=" * 70)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

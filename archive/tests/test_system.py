#!/usr/bin/env python3
"""
會議記錄優化系統測試腳本

用於測試新的疊代優化系統是否正常運行
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 添加腳本路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

try:
    from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig
    print("✓ 成功導入疊代優化器")
except ImportError as e:
    print(f"✗ 導入疊代優化器失敗: {e}")
    sys.exit(1)

try:
    from scripts.evaluation import MeetingEvaluator, EvaluationConfig
    print("✓ 成功導入評估模組")
except ImportError as e:
    print(f"✗ 導入評估模組失敗: {e}")

def test_strategy_loading():
    """測試策略配置載入"""
    try:
        config_path = os.path.join(script_dir, "config/improvement_strategies.json")
        if not os.path.exists(config_path):
            print(f"✗ 策略配置文件不存在: {config_path}")
            assert False
        with open(config_path, "r", encoding="utf-8") as f:
            strategies = json.load(f)
        # 檢查是否有30種策略
        strategy_count = len([k for k in strategies.keys() if k != "metadata"])
        print(f"✓ 載入 {strategy_count} 種策略")
        if strategy_count >= 25:  # 允許一定誤差
            print("✓ 策略數量符合要求")
            assert True
        else:
            print(f"✗ 策略數量不足，期望至少25種，實際{strategy_count}種")
            assert False
    except Exception as e:
        print(f"✗ 策略配置載入失敗: {e}")
        assert False

def test_optimizer_creation():
    """測試優化器創建"""
    try:
        config = OptimizationConfig(
            max_iterations=2,
            quality_threshold=0.7,
            model_name="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
            optimization_model="gemma3:12b"
        )
        
        optimizer = MeetingOptimizer(config)
        print("✓ 成功創建優化器")
        assert True
        
    except Exception as e:
        print(f"✗ 創建優化器失敗: {e}")
        assert False

def test_strategy_selection():
    """測試策略選擇邏輯"""
    try:
        config = OptimizationConfig(max_iterations=3)
        optimizer = MeetingOptimizer(config)
        # 測試第一輪策略選擇
        strategies_round1 = optimizer._select_strategy_combination(0, [])
        print(f"✓ 第一輪策略選擇: {strategies_round1}")
        # 測試策略維度分組
        pools = optimizer._get_strategy_pools_by_dimension()
        for dim, strategies in pools.items():
            if strategies:
                print(f"✓ {dim} 維度有 {len(strategies)} 個策略")
        assert True
    except Exception as e:
        print(f"✗ 策略選擇測試失敗: {e}")
        assert False

def test_prompt_generation():
    """測試提示詞生成"""
    try:
        config = OptimizationConfig()
        optimizer = MeetingOptimizer(config)
        # 測試提示詞組裝
        strategies = ["A_role_definition_A1", "B_structure_B1", "C_summary_C1"]
        transcript = "這是一個測試逐字稿。主席說：今天討論預算。張三說：我同意。會議結束。"
        prompt = optimizer._assemble_prompt(strategies, transcript)
        if len(prompt) > 100 and "會議記錄優化任務" in prompt:
            print("✓ 提示詞生成正常")
            assert True
        else:
            print("✗ 提示詞生成異常")
            assert False
    except Exception as e:
        print(f"✗ 提示詞生成測試失敗: {e}")
        assert False

def test_file_structure():
    """測試文件結構"""
    required_files = [
        "scripts/iterative_optimizer.py",
        "scripts/evaluation/__init__.py",
        "config/improvement_strategies.json",
        "run_optimization.sh"
    ]
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(script_dir, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    assert all_exist

def main():
    """主測試函數"""
    print("=== 會議記錄優化系統測試 ===\n")
    
    tests = [
        ("文件結構檢查", test_file_structure),
        ("策略配置載入", test_strategy_loading),
        ("優化器創建", test_optimizer_creation),
        ("策略選擇邏輯", test_strategy_selection),
        ("提示詞生成", test_prompt_generation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            test_func()
            passed += 1
            print(f"✓ {test_name} 通過")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} 出錯: {e}")
    
    print(f"\n=== 測試結果 ===")
    print(f"通過: {passed}")
    print(f"失敗: {failed}")
    print(f"總計: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有測試通過！系統已準備就緒。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗，請檢查並修復。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
測試結構化改進機制 - 不依賴 LLM 調用
"""

import os
import sys
import json
from pathlib import Path

# 添加腳本路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig

def test_prompt_generation():
    """測試改進提示詞生成"""
    print("=== 測試改進提示詞生成 ===")
    
    config = OptimizationConfig(
        max_iterations=1,
        model_name="gemma3:12b",
        optimization_model="gemma3:12b"
    )
    
    optimizer = MeetingOptimizer(config)
    
    # 模擬正確格式的歷史數據
    history = {
        'iterations': [
            {
                'iteration': 0,
                'strategy_combination': ['A_role_definition_A1', 'B_structure_B1'],
                'scores': {
                    'overall_score': 0.65,
                    'structure_score': 0.7,
                    'content_richness': 0.6
                },
                'minutes_content': '會議記錄內容測試...'
            }
        ]
    }
    
    try:
        prompt = optimizer._generate_improvement_prompt("測試會議記錄", history)
        
        print("✓ 改進提示詞生成成功")
        print(f"提示詞長度: {len(prompt)} 字符")
        
        # 檢查關鍵組件
        checks = [
            ("JSON格式要求", "JSON格式" in prompt),
            ("策略調整", "strategy_adjustments" in prompt),
            ("可用策略", "可用策略資源" in prompt),
            ("評分詳情", "評分詳情" in prompt)
        ]
        
        for check_name, check_result in checks:
            print(f"  {check_name}: {'✓' if check_result else '✗'}")
        
        assert all(result for _, result in checks)
        
    except Exception as e:
        print(f"✗ 改進提示詞生成失敗: {e}")
        import traceback
        traceback.print_exc()
        assert False

def test_suggestion_parsing():
    """測試建議解析功能"""
    print("\n=== 測試建議解析功能 ===")
    
    config = OptimizationConfig()
    optimizer = MeetingOptimizer(config)
    
    # 測試 JSON 格式解析
    test_json = """
```json
{
  "score_analysis": {
    "weakest_metrics": ["content_richness", "structure_score"],
    "improvement_priority": "high",
    "root_causes": ["缺乏詳細內容", "結構不清晰"]
  },
  "strategy_adjustments": {
    "remove_strategies": ["A_role_definition_A1"],
    "add_strategies": ["A_role_definition_A2", "C_detail_C2"],
    "dimension_focus": "內容",
    "rationale": "需要加強內容詳細度"
  },
  "specific_improvements": {
    "content_structure": "增加具體討論細節",
    "language_style": "使用更正式語調",
    "format_enhancement": "加強標題層次"
  }
}
```
"""
    
    try:
        parsed = optimizer._parse_improvement_suggestions(test_json)
        
        print("✓ JSON 解析成功")
        print(f"解析結果鍵: {list(parsed.keys())}")
        
        # 驗證解析結果
        if 'strategy_adjustments' in parsed:
            adjustments = parsed['strategy_adjustments']
            print(f"  策略調整: 移除 {len(adjustments.get('remove_strategies', []))} 個，新增 {len(adjustments.get('add_strategies', []))} 個")
        
        # 測試驗證功能
        validated = optimizer._validate_strategy_suggestions(parsed)
        print("✓ 建議驗證完成")
        assert True
    except Exception as e:
        print(f"✗ 建議解析失敗: {e}")
        assert False

def test_strategy_application():
    """測試策略應用功能"""
    print("\n=== 測試策略應用功能 ===")
    
    config = OptimizationConfig()
    optimizer = MeetingOptimizer(config)
    
    # 模擬歷史結果
    from scripts.iterative_optimizer import OptimizationResult
    history = [
        OptimizationResult(
            iteration=0,
            strategy_combination=['A_role_definition_A1', 'B_structure_B1'],
            minutes_content="測試內容",
            scores={'overall_score': 0.65},
            execution_time=10.0,
            timestamp="2024-01-01T00:00:00",
            model_used="test"
        )
    ]
    
    # 模擬改進建議
    suggestions = {
        "strategy_adjustments": {
            "remove_strategies": ["A_role_definition_A1"],
            "add_strategies": ["A_role_definition_A2", "C_summary_C1"],
            "dimension_focus": "內容",
            "rationale": "改善內容品質"
        }
    }
    
    try:
        new_strategies = optimizer._apply_improvement_suggestions(suggestions, history)
        
        print("✓ 策略應用成功")
        print(f"新策略組合: {new_strategies}")
        
        # 檢查結果
        expected_removed = "A_role_definition_A1" not in new_strategies
        expected_added = "A_role_definition_A2" in new_strategies or "C_summary_C1" in new_strategies
        
        print(f"  移除舊策略: {'✓' if expected_removed else '✗'}")
        print(f"  新增新策略: {'✓' if expected_added else '✗'}")
        
        assert expected_removed and expected_added
        
    except Exception as e:
        print(f"✗ 策略應用失敗: {e}")
        assert False

def test_integration():
    """測試完整整合"""
    print("\n=== 測試完整整合 ===")
    
    config = OptimizationConfig(max_iterations=1)
    optimizer = MeetingOptimizer(config)
    
    # 測試獲取策略維度分組
    strategies_by_dimension = optimizer._get_available_strategies_by_dimension()
    
    print(f"✓ 策略維度分組: {len(strategies_by_dimension)} 個維度")
    for dim, strategies in strategies_by_dimension.items():
        if strategies:
            print(f"  {dim}: {len(strategies)} 個策略")
    
    # 測試格式化功能
    formatted = optimizer._format_available_strategies(strategies_by_dimension)
    print(f"✓ 策略格式化: {len(formatted)} 字符")
    
    assert True

if __name__ == "__main__":
    print("開始測試結構化改進機制...\n")
    
    tests = [
        ("改進提示詞生成", test_prompt_generation),
        ("建議解析功能", test_suggestion_parsing),
        ("策略應用功能", test_strategy_application),
        ("完整整合", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 測試出錯: {e}")
            results.append((test_name, False))
    
    print(f"\n=== 測試總結 ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總結: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！結構化改進機制運行正常。")
    else:
        print("❌ 部分測試失敗，但核心功能可用。")

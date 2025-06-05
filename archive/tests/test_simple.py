#!/usr/bin/env python3
"""
簡單測試：驗證結構化改進提示詞生成
"""

import os
import sys

# 添加腳本路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig

def test_prompt_generation_only():
    """只測試提示詞生成，不調用LLM"""
    print("=== 測試結構化改進提示詞生成 ===")
    
    try:
        config = OptimizationConfig(
            max_iterations=1,
            model_name="gemma3:12b",
            optimization_model="gemma3:12b"
        )
        
        optimizer = MeetingOptimizer(config)
        print("✓ 優化器創建成功")
        
        # 模擬歷史數據
        history = {
            'iterations': [
                {
                    'score': 0.65,
                    'strategies': ['A_role_definition_A1', 'B_structure_B1'],
                    'feedback': '結構清晰但缺乏細節',
                    'improvements': '需要增加更多具體內容'
                }
            ]
        }
        
        test_meeting = "這是一個測試會議記錄。包含基本的會議信息和討論內容。"
        
        # 測試改進提示詞生成
        print("正在生成改進提示詞...")
        improvement_prompt = optimizer._generate_improvement_prompt(test_meeting, history)
        
        print("✓ 改進提示詞生成成功")
        print(f"提示詞長度: {len(improvement_prompt)} 字符")
        
        # 檢查關鍵詞
        key_terms = [
            "JSON格式",
            "strategy_adjustments", 
            "specific_suggestions",
            "score_analysis",
            "gemma3"
        ]
        
        found_terms = []
        for term in key_terms:
            if term in improvement_prompt:
                found_terms.append(term)
        
        print(f"✓ 包含關鍵詞: {found_terms}")
        
        # 打印部分提示詞內容（前500字符）
        print("\n--- 提示詞前500字符 ---")
        print(improvement_prompt[:500])
        print("...")
        
        # 檢查可用策略獲取
        print("\n=== 測試策略獲取方法 ===")
        available_strategies = optimizer._get_available_strategies_by_dimension()
        print(f"✓ 獲取到 {len(available_strategies)} 個維度的策略")
        
        for dim, strategies in available_strategies.items():
            print(f"  - {dim}: {len(strategies)} 個策略")
        
        # 測試策略格式化
        formatted = optimizer._format_available_strategies(available_strategies)
        print(f"✓ 策略格式化成功，長度: {len(formatted)} 字符")
        assert True
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        assert False

def test_parsing_methods():
    """測試解析方法"""
    print("\n=== 測試解析方法 ===")
    
    try:
        config = OptimizationConfig(max_iterations=1, model_name="gemma3:12b")
        optimizer = MeetingOptimizer(config)
        
        # 測試 JSON 解析
        test_json = '''
        {
            "score_analysis": "當前分數0.65偏低",
            "strategy_adjustments": {
                "role": ["A_role_definition_A2"],
                "structure": ["B_structure_B2", "B_structure_B3"]
            },
            "specific_suggestions": [
                "增加會議主持人資訊",
                "改善會議結構組織"
            ]
        }
        '''
        
        parsed = optimizer._parse_improvement_suggestions(test_json)
        print("✓ JSON 解析成功")
        print(f"解析結果: {parsed}")
        
        # 測試驗證方法
        is_valid = optimizer._validate_strategy_suggestions(parsed.get('strategy_adjustments', {}))
        print(f"✓ 策略驗證結果: {is_valid}")
        assert True
    except Exception as e:
        print(f"✗ 解析測試失敗: {e}")
        import traceback
        traceback.print_exc()
        assert False

if __name__ == "__main__":
    print("開始簡單測試...\n")
    
    test1 = test_prompt_generation_only()
    test2 = test_parsing_methods()
    
    print(f"\n=== 測試結果 ===")
    print(f"提示詞生成: {'✓' if test1 else '✗'}")
    print(f"解析方法: {'✓' if test2 else '✗'}")
    
    if test1 and test2:
        print("\n🎉 基礎功能測試通過！")
    else:
        print("\n❌ 部分功能需要修復。")

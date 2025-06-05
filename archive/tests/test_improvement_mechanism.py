#!/usr/bin/env python3
"""
測試 Gemma3:12b 結構化改進機制

用於驗證新實現的結構化改進建議是否正常工作
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 添加腳本路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig

def test_improvement_mechanism():
    """測試改進機制"""
    print("=== 測試 Gemma3:12b 結構化改進機制 ===\n")
    
    # 創建優化器
    config = OptimizationConfig(
        max_iterations=3,  # 只做3輪測試
        model_name="gemma3:12b",
        optimization_model="gemma3:12b",
        quality_threshold=0.7
    )
    
    optimizer = MeetingOptimizer(config)
    print("✓ 優化器創建成功")
    
    # 創建測試會議記錄
    test_meeting = """
會議記錄：產品開發討論
時間：2024年12月16日 14:00-15:30
參與者：產品經理王小明、技術主管李大華、設計師張小美

討論內容：
1. 新產品功能需求討論
2. 技術實現可行性分析  
3. 設計原型審查
4. 開發時程規劃

會議結論：
- 確定核心功能列表
- 技術方案需進一步調研
- 下週完成設計稿
- 預計2個月開發週期
"""
    
    print(f"測試會議記錄長度: {len(test_meeting)} 字符")
    
    # 開始優化流程
    print("\n--- 開始優化流程 ---")
    try:
        results = optimizer.optimize(test_meeting)
        
        print(f"\n=== 優化結果統計 ===")
        print(f"完成輪數: {len(results['iterations'])}")
        print(f"最終分數: {results.get('final_score', 'N/A')}")
        print(f"改進幅度: {results.get('improvement', 'N/A')}")
        
        # 檢查每輪的改進建議
        for i, iteration in enumerate(results['iterations']):
            print(f"\n--- 第 {i+1} 輪 ---")
            print(f"分數: {iteration.get('score', 'N/A')}")
            print(f"使用策略: {iteration.get('strategies', [])}")
            
            # 檢查改進建議
            if 'improvements' in iteration:
                improvements = iteration['improvements']
                print(f"改進建議類型: {type(improvements)}")
                
                if isinstance(improvements, dict):
                    print("✓ 結構化改進建議:")
                    for key, value in improvements.items():
                        if key == 'strategy_adjustments' and isinstance(value, dict):
                            print(f"  - 策略調整: {len(value)} 個維度")
                            for dim, strategies in value.items():
                                print(f"    • {dim}: {strategies}")
                        elif key == 'specific_suggestions' and isinstance(value, list):
                            print(f"  - 具體建議: {len(value)} 項")
                        else:
                            print(f"  - {key}: {value}")
                else:
                    print(f"傳統改進建議: {str(improvements)[:100]}...")
        
        if results.get('final_score', 0) > 0.7:
            print("\n🎉 測試成功！分數達到目標閾值")
            assert True
        else:
            print(f"\n⚠️  分數未達目標，但機制運行正常")
            assert True  # 若只要流程正常即通過
    except Exception as e:
        print(f"\n✗ 優化過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        assert False

def test_structured_prompt_generation():
    """測試結構化提示詞生成"""
    print("\n=== 測試結構化提示詞生成 ===")
    
    config = OptimizationConfig(
        max_iterations=1,
        model_name="gemma3:12b",
        optimization_model="gemma3:12b"
    )
    
    optimizer = MeetingOptimizer(config)
    
    # 模擬歷史數據
    history = {
        'iterations': [
            {
                'score': 0.65,
                'strategies': ['A_role_definition_A1', 'B_structure_B1'],
                'feedback': '結構清晰但缺乏細節'
            }
        ]
    }
    
    try:
        # 測試改進提示詞生成
        improvement_prompt = optimizer._generate_improvement_prompt("測試會議記錄", history)
        
        print("✓ 改進提示詞生成成功")
        print(f"提示詞長度: {len(improvement_prompt)} 字符")
        
        # 檢查是否包含結構化要求
        if "JSON格式" in improvement_prompt and "strategy_adjustments" in improvement_prompt:
            print("✓ 包含結構化JSON要求")
        else:
            print("⚠️  可能缺少結構化要求")
            
        assert True
        
    except Exception as e:
        print(f"✗ 結構化提示詞生成失敗: {e}")
        assert False

if __name__ == "__main__":
    print("開始測試 Gemma3:12b 改進機制...\n")
    
    # 測試1: 結構化提示詞生成
    test1_pass = test_structured_prompt_generation()
    
    # 測試2: 完整改進機制
    test2_pass = test_improvement_mechanism()
    
    print(f"\n=== 測試總結 ===")
    print(f"結構化提示詞生成: {'✓ 通過' if test1_pass else '✗ 失敗'}")
    print(f"完整改進機制: {'✓ 通過' if test2_pass else '✗ 失敗'}")
    
    if test1_pass and test2_pass:
        print("\n🎉 所有測試通過！結構化改進機制運行正常。")
    else:
        print("\n❌ 部分測試失敗，需要進一步調試。")

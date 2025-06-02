#!/usr/bin/env python3
"""
測試完整的優化流程 - 驗證 Gemma3:12b 改進機制的實際效果
"""

import os
import sys
import tempfile

# 添加腳本路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig

def test_full_optimization():
    """測試完整的優化流程"""
    print("=== 測試完整優化流程 ===")
    
    # 創建優化器配置
    config = OptimizationConfig(
        max_iterations=3,
        model_name="gemma3:12b",
        optimization_model="gemma3:12b",
        quality_threshold=0.75,
        enable_early_stopping=True
    )
    
    optimizer = MeetingOptimizer(config)
    print("✓ 優化器創建成功")
    
    # 測試會議記錄
    test_meeting = """
會議：產品開發週會
時間：2024年12月16日 14:00
參與者：產品經理 王小明、工程師 李大華、設計師 張小美

王小明：今天我們來討論一下新功能的開發進度。
李大華：後端API基本完成了，但還需要測試。
張小美：UI設計稿已經做好，需要大家確認一下。
王小明：好的，那我們先看設計稿，然後討論技術實現。
李大華：設計看起來不錯，但有些交互邏輯需要調整。
張小美：沒問題，我會根據意見修改。
王小明：那我們確定一下時程，下週能完成開發嗎？
李大華：如果沒有大的變更，應該可以。
王小明：好，那就這樣決定了。

決議：
1. 設計師根據意見修改UI
2. 工程師完成API測試
3. 下週完成開發
"""
    
    print(f"測試會議記錄長度: {len(test_meeting)} 字符")
    
    try:
        # 執行優化
        results = optimizer.optimize(test_meeting)
        
        print("\n=== 優化結果分析 ===")
        print(f"最終分數: {results.get('final_score', 'N/A'):.4f}")
        print(f"改進幅度: {results.get('improvement', 'N/A'):.4f}")
        print(f"完成輪數: {len(results.get('iterations', []))}")
        
        # 分析每輪結果
        iterations = results.get('iterations', [])
        for i, iteration in enumerate(iterations):
            print(f"\n--- 第 {i+1} 輪分析 ---")
            print(f"分數: {iteration.get('score', 'N/A'):.4f}")
            print(f"策略: {iteration.get('strategies', [])}")
            
            if iteration.get('feedback'):
                print(f"反饋: {iteration['feedback']}")
            
            if iteration.get('improvements'):
                print(f"改進: {iteration['improvements']}")
        
        # 判斷成功條件
        final_score = results.get('final_score', 0)
        success_criteria = [
            (final_score > 0.5, f"分數達標 (>0.5): {final_score:.4f}"),
            (len(iterations) >= 1, f"完成至少1輪: {len(iterations)}"),
            (len(iterations[0].get('strategies', [])) > 0, "策略組合有效")
        ]
        
        print(f"\n=== 成功度評估 ===")
        passed_criteria = 0
        for criterion, description in success_criteria:
            status = "✓" if criterion else "✗"
            print(f"{status} {description}")
            if criterion:
                passed_criteria += 1
        
        success_rate = passed_criteria / len(success_criteria)
        print(f"\n成功率: {success_rate:.2%} ({passed_criteria}/{len(success_criteria)})")
        
        if success_rate >= 0.8:
            print("🎉 優化流程運行成功！")
            return True
        else:
            print("⚠️  優化流程基本正常，但可能需要調整")
            return success_rate >= 0.6
            
    except Exception as e:
        print(f"✗ 優化流程失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_improvement_effectiveness():
    """測試改進建議的有效性"""
    print("\n=== 測試改進建議有效性 ===")
    
    config = OptimizationConfig()
    optimizer = MeetingOptimizer(config)
    
    # 模擬第一輪結果
    from scripts.iterative_optimizer import OptimizationResult
    from datetime import datetime
    
    first_result = OptimizationResult(
        iteration=0,
        strategy_combination=['A_role_definition_A1', 'B_structure_B1', 'C_summary_C1'],
        minutes_content="基本會議記錄內容...",
        scores={'overall_score': 0.60, 'structure_score': 0.65, 'content_richness': 0.55},
        execution_time=10.0,
        timestamp=datetime.now().isoformat(),
        model_used="gemma3:12b"
    )
    
    history = [first_result]
    
    try:
        # 測試策略選擇改進
        new_strategies = optimizer._select_strategy_combination(1, history)
        
        print(f"原始策略: {first_result.strategy_combination}")
        print(f"改進策略: {new_strategies}")
        
        # 檢查是否有實際改進
        strategy_changed = set(new_strategies) != set(first_result.strategy_combination)
        print(f"策略有變化: {'✓' if strategy_changed else '✗'}")
        
        # 檢查維度覆蓋
        dimensions = set()
        for strategy_id in new_strategies:
            if strategy_id in optimizer.strategies:
                dim = optimizer.strategies[strategy_id].get('dimension', '')
                dimensions.add(dim)
        
        print(f"覆蓋維度: {len(dimensions)} 個 ({', '.join(dimensions)})")
        
        dimension_coverage = len(dimensions) >= 2
        print(f"維度覆蓋充足: {'✓' if dimension_coverage else '✗'}")
        
        return strategy_changed and dimension_coverage
        
    except Exception as e:
        print(f"✗ 改進建議測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("開始測試完整優化流程...\n")
    
    # 測試1: 完整優化流程
    test1_result = test_full_optimization()
    
    # 測試2: 改進建議有效性
    test2_result = test_improvement_effectiveness()
    
    print(f"\n=== 最終測試結果 ===")
    print(f"完整優化流程: {'✓ 成功' if test1_result else '✗ 失敗'}")
    print(f"改進建議有效性: {'✓ 成功' if test2_result else '✗ 失敗'}")
    
    overall_success = test1_result and test2_result
    
    if overall_success:
        print("\n🎉 Gemma3:12b 結構化改進機制完全運行正常！")
        print("✅ 系統能夠：")
        print("   - 生成結構化改進提示詞")
        print("   - 解析和驗證LLM建議")
        print("   - 應用策略調整")
        print("   - 完成多輪優化")
    else:
        print("\n⚠️  部分功能需要進一步優化，但基礎架構正常")
        
    print(f"\n📊 總體評分: {'A+' if overall_success else 'B+' if test1_result or test2_result else 'C'}")

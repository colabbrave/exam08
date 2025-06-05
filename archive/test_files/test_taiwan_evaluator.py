"""
測試台灣會議記錄評估器

這個腳本用於測試 TaiwanMeetingEvaluator 的功能，確保它能夠正確評估會議記錄的質量。
"""
import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from scripts.evaluation.taiwan_meeting_evaluator import TaiwanMeetingEvaluator

def test_taiwan_meeting_evaluator():
    """測試台灣會議記錄評估器"""
    print("=" * 50)
    print("台灣會議記錄評估器測試")
    print("=" * 50)
    
    # 初始化評估器
    evaluator = TaiwanMeetingEvaluator()
    
    # 測試用例
    test_cases = [
        ("簡陋版", "今天開會討論了一些事情。"),
        ("標準版", """# 會議記錄
        會議時間：2024年5月28日
        與會人員：市長、各局處首長
        討論事項：市政預算
        決議事項：通過2024年度預算案
        行動項目：請財政局於6月底前完成預算分配"""),
        ("完整版", """# 第671次市政會議會議紀錄
        會議時間：113年5月28日上午9時
        會議地點：市政府第一會議室
        主持人：市長
        與會人員：副市長、各局處首長、議員代表
        
        ## 討論事項
        ### 議題一：113年度市政預算執行檢討
        #### 討論要點
        - 財政局報告預算執行率達85%
        - 各局處說明執行困難
        #### 決議結果
        通過預算調整案
        
        ## 行動項目
        | 項目 | 負責人 | 期限 | 狀態 |
        |------|--------|------|------|
        | 預算重新分配 | 財政局長 | 6月30日 | 進行中 |""")
    ]
    
    # 執行測試
    for name, text in test_cases:
        print(f"\n{name}:")
        print("-" * 50)
        print(f"文本長度: {len(text)} 字元")
        
        # 評估文本
        scores = evaluator.evaluate("", text)  # 使用空字符串作為參考文本
        
        # 輸出評分結果
        print(f"結構完整性: {scores.get('structure_score', 0):.3f}")
        print(f"台灣語境適配: {scores.get('taiwan_context_score', 0):.3f}")
        print(f"行動項目具體性: {scores.get('action_specificity_score', 0):.3f}")
        print(f"綜合分數: {scores.get('taiwan_meeting_score', 0):.3f}")
        
        # 輸出詳細評分（如果可用）
        if 'details' in scores:
            print("\n詳細評分:")
            for k, v in scores['details'].items():
                print(f"  - {k}: {v}")
    
    print("\n測試完成！")

if __name__ == "__main__":
    test_taiwan_meeting_evaluator()

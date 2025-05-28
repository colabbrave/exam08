#!/usr/bin/env python3
"""
測試 MeetingEvaluator 導入
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from scripts.evaluation import MeetingEvaluator
    print("✅ 成功導入 MeetingEvaluator")
    print(f"MeetingEvaluator 類: {MeetingEvaluator}")
    
    # 測試創建實例
    try:
        evaluator = MeetingEvaluator()
        print("✅ 成功創建 MeetingEvaluator 實例")
    except Exception as e:
        print(f"❌ 創建 MeetingEvaluator 實例時出錯: {e}")
        raise
        
except ImportError as e:
    print(f"❌ 導入 MeetingEvaluator 時出錯: {e}")
    print("Python 路徑:")
    for p in sys.path:
        print(f"  - {p}")

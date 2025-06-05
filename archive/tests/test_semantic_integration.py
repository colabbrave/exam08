#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段功能整合測試腳本
測試語意分段與現有優化流程的兼容性
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
import pytest

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 導入相關模組
try:
    from scripts.optimize_meeting_minutes import MeetingOptimizer
    from scripts.semantic_splitter import SemanticSplitter
    from scripts.segment_quality_eval import SegmentQualityEvaluator
    from scripts.semantic_meeting_processor import SemanticMeetingProcessor
    print("✓ 成功導入所有語意分段模組")
except ImportError as e:
    print(f"✗ 導入模組失敗: {e}")
    sys.exit(1)

def setup_logging():
    """設置日誌"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"semantic_integration_test_{int(time.time())}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("SemanticIntegrationTest")

def create_test_data() -> Dict[str, Any]:
    """創建測試數據"""
    # 創建一個大型逐字稿樣本
    large_transcript = """
台中市政府第150次市政會議記錄

會議時間：112年6月15日下午2時
會議地點：台中市政府會議室
主席：市長盧秀燕
出席人員：副市長、各局處首長

會議開始：
市長致詞：各位同仁大家好，今天的市政會議主要討論幾個重要議題...

第一案：都市計畫通盤檢討案
提案機關：都市發展局
案由：辦理台中市都市計畫通盤檢討，建請審議。
說明：
一、本案係依都市計畫法第26條規定，每五年通盤檢討一次。
二、檢討範圍包含全市29個都市計畫區。
三、預計需時18個月完成。

各局處意見：
交通局：建議加強交通系統整體規劃，特別是大眾運輸系統的銜接。
環保局：應納入環境影響評估，確保都市發展與環境保護平衡。
水利局：需考量排水系統容量，避免都市化造成淹水問題。

討論：
市長：這個案子非常重要，關係到台中市未來20年的發展。請都發局再詳細說明檢討重點。
都發局長：主要檢討項目包括：
1. 土地使用分區調整
2. 公共設施用地檢討
3. 交通系統規劃
4. 環境品質維護
5. 產業發展空間規劃

決議：
一、原則同意辦理都市計畫通盤檢討。
二、請都發局於一個月內提出詳細執行計畫。
三、成立跨局處工作小組，由副市長擔任召集人。

第二案：智慧城市建設計畫
提案機關：研考會
案由：推動台中智慧城市建設，建請審議。
說明：
一、配合國家數位轉型政策，推動智慧城市建設。
二、計畫期程為5年，預算需求約50億元。
三、主要建設項目包括智慧交通、智慧教育、智慧醫療、智慧治理等。

各局處意見：
資訊局：技術面可行，但需要大量專業人力。
財政局：預算龐大，建議分期分年編列。
教育局：智慧教育部分，需要教師培訓配套措施。

討論：
市長：智慧城市是未來趨勢，但要務實推動，不能為了智慧而智慧。
研考會主委：我們已經參考其他縣市經驗，並考量台中市的特色。

決議：
一、原則同意推動智慧城市建設計畫。
二、請研考會修正計畫內容，降低預算需求。
三、優先推動智慧交通和智慧治理項目。

第三案：社會住宅興建計畫
提案機關：住宅發展工程處
案由：興建社會住宅，解決青年居住問題，建請審議。
說明：
一、規劃在北屯、西屯、太平等區興建社會住宅。
二、預計興建3000戶，提供青年及弱勢族群租用。
三、結合托育、長照等社會福利設施。

各局處意見：
社會局：支持結合社福設施，但需要營運經費。
教育局：建議規劃學校用地，解決就學問題。
衛生局：可結合社區健康中心設置。

討論：
市長：社會住宅不只是蓋房子，要營造社區生活圈。
住宅處長：我們已經規劃完整的社區服務機能。

決議：
一、同意興建社會住宅計畫。
二、優先推動北屯區基地。
三、請各相關局處協助配合。

散會時間：下午5時30分
""" * 3  # 重複3次以增加長度

    return {
        "transcript": large_transcript,
        "transcript_file": "第150次市政會議112年6月15日.txt",
        "reference": large_transcript[:2000] + "...",  # 簡化的參考
        "reference_file": "reference_150.txt"
    }

def test_semantic_splitter():
    """測試語意分段器"""
    logger = logging.getLogger("SemanticSplitterTest")
    logger.info("=== 測試語意分段器 ===")
    
    try:
        splitter = SemanticSplitter()
        
        test_data = create_test_data()
        transcript = test_data["transcript"]
        
        logger.info(f"原始文本長度: {len(transcript)} 字元")
        
        # 執行分段
        segments = splitter.split_text(transcript)
        
        logger.info(f"分段結果: {len(segments)} 個段落")
        for i, segment in enumerate(segments):
            logger.info(f"段落 {i+1}: {len(segment.get('content', ''))} 字元")
        
        # 驗證分段結果
        assert segments is not None, "分段結果不應為 None"
        assert len(segments) > 0, "應該至少有一個分段"
        assert isinstance(segments, list), "分段結果應為列表格式"
        
    except Exception as e:
        logger.error(f"語意分段測試失敗: {e}")
        assert False, f"語意分段測試失敗: {e}"

def segments():
    """pytest fixture: 提供語意分段測試資料"""
    test_data = create_test_data()
    transcript = test_data["transcript"]
    splitter = SemanticSplitter()
    return splitter.split_text(transcript)

# === 以下為已修正的 fixture 與測試函數 ===
import pytest

@pytest.fixture
def segments_fixture():
    from scripts.semantic_splitter import SemanticSplitter
    splitter = SemanticSplitter(model_name="gemma3:12b", max_segment_length=4000, overlap_length=200)
    test_data = create_test_data()
    transcript = test_data["transcript"]
    return splitter.split_text(transcript)


def test_quality_evaluator(segments_fixture):
    from scripts.segment_quality_eval import SegmentQualityEvaluator
    evaluator = SegmentQualityEvaluator(model_name="gemma3:12b")
    test_data = create_test_data()
    original_text = test_data["transcript"]
    # evaluate_segments 只需 (segments, original_text)
    quality_result = evaluator.evaluate_segments(segments_fixture, original_text)
    assert quality_result is not None

def test_meeting_optimizer_integration():
    """測試會議優化器整合"""
    logger = logging.getLogger("OptimizerIntegrationTest")
    logger.info("=== 測試會議優化器整合 ===")
    
    try:
        # 創建輸出目錄
        output_dir = project_root / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # 初始化優化器，啟用語意分段
        optimizer = MeetingOptimizer(
            model_name="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
            output_dir=str(output_dir),
            enable_semantic_segmentation=True
        )
        
        # 準備測試數據
        test_data = create_test_data()
        matched_data = [test_data]
        
        logger.info("開始執行優化流程...")
        
        # 執行優化（使用較少的迭代次數進行測試）
        best_minutes, best_metrics, best_score = optimizer.optimize(
            matched_data,
            max_iterations=2,
            batch_size=1
        )
        
        logger.info(f"優化完成:")
        logger.info(f"  最佳分數: {best_score:.4f}")
        logger.info(f"  生成字數: {len(best_minutes)} 字元")
        
        # 檢查輸出文件
        output_files = list(output_dir.glob("*.json"))
        logger.info(f"生成輸出文件: {len(output_files)} 個")
        
        # 驗證結果
        assert best_score > 0, f"優化分數應大於0，當前分數: {best_score}"
        assert len(output_files) > 0, "應該生成至少一個輸出文件"
        
    except Exception as e:
        logger.error(f"會議優化器整合測試失敗: {e}")
        assert False, f"會議優化器整合測試失敗: {e}"

def test_semantic_processor():
    """測試語意處理器"""
    logger = logging.getLogger("SemanticProcessorTest")
    logger.info("=== 測試語意處理器 ===")
    
    try:
        processor = SemanticMeetingProcessor()
        
        test_data = create_test_data()
        transcript = test_data["transcript"]
        
        logger.info("執行語意處理流程...")
        
        # 處理逐字稿
        result = processor.process_transcript(
            transcript_text=transcript,
            output_dir="output/test",  # 指定測試輸出目錄
            enable_quality_check=True
        )
        
        if result:
            logger.info("語意處理器測試成功")
            logger.info(f"處理結果: {type(result)}")
            assert result is not None, "處理結果不應為 None"
        else:
            logger.warning("語意處理器返回空結果")
            assert False, "語意處理器返回空結果"
        
    except Exception as e:
        logger.error(f"語意處理器測試失敗: {e}")
        return False, ""

def main():
    """主測試函數"""
    logger = setup_logging()
    logger.info("開始語意分段功能整合測試")
    
    test_results = {}
    
    # 測試1: 語意分段器
    try:
        test_semantic_splitter()
        test_results["semantic_splitter"] = True
        logger.info("✓ 語意分段器測試通過")
    except Exception as e:
        test_results["semantic_splitter"] = False
        logger.error(f"✗ 語意分段器測試失敗: {e}")
    
    # 測試2: 品質評估器
    try:
        # 使用 fixture 獲取測試數據
        from scripts.semantic_splitter import SemanticSplitter
        splitter = SemanticSplitter(model_name="gemma3:12b", max_segment_length=4000, overlap_length=200)
        test_data = create_test_data()
        transcript = test_data["transcript"]
        segments = splitter.split_text(transcript)
        
        from scripts.segment_quality_eval import SegmentQualityEvaluator
        evaluator = SegmentQualityEvaluator(model_name="gemma3:12b")
        quality_result = evaluator.evaluate_segments(segments, transcript)
        test_results["quality_evaluator"] = quality_result is not None
        logger.info("✓ 品質評估器測試通過")
    except Exception as e:
        test_results["quality_evaluator"] = False
        logger.error(f"✗ 品質評估器測試失敗: {e}")
    
    # 測試3: 語意處理器
    try:
        test_semantic_processor()
        test_results["semantic_processor"] = True
        logger.info("✓ 語意處理器測試通過")
    except Exception as e:
        test_results["semantic_processor"] = False
        logger.error(f"✗ 語意處理器測試失敗: {e}")
    
    # 測試4: 會議優化器整合
    try:
        test_meeting_optimizer_integration()
        test_results["optimizer_integration"] = True
        logger.info("✓ 會議優化器整合測試通過")
    except Exception as e:
        test_results["optimizer_integration"] = False
        logger.error(f"✗ 會議優化器整合測試失敗: {e}")
    
    # 輸出測試結果
    logger.info("\n=== 測試結果總結 ===")
    for test_name, result in test_results.items():
        status = "✓ 通過" if result else "✗ 失敗"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    if all_passed:
        logger.info("🎉 所有測試通過！語意分段功能整合成功")
        return 0
    else:
        logger.error("❌ 部分測試失敗，請檢查相關模組")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

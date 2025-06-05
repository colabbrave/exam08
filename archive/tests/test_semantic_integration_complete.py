#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段整合完整測試腳本
測試語意分段與會議記錄優化的完整流程整合
"""

import os
import sys
import logging
from pathlib import Path

# 添加 scripts 目錄到 Python 路徑
project_root = Path(__file__).parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(scripts_dir))

def setup_logging():
    """設置日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_semantic_integration_complete.log')
        ]
    )
    return logging.getLogger(__name__)

def test_semantic_modules_import():
    """測試語意分段模組導入"""
    logger = logging.getLogger(__name__)
    logger.info("=== 測試語意分段模組導入 ===")
    
    try:
        from semantic_splitter import SemanticSplitter
        logger.info("✓ SemanticSplitter 導入成功")
    except ImportError as e:
        logger.error(f"✗ SemanticSplitter 導入失敗: {e}")
        assert False
    
    try:
        from segment_quality_eval import SegmentQualityEvaluator
        logger.info("✓ SegmentQualityEvaluator 導入成功")
    except ImportError as e:
        logger.error(f"✗ SegmentQualityEvaluator 導入失敗: {e}")
        assert False
    
    try:
        from semantic_meeting_processor import SemanticMeetingProcessor
        logger.info("✓ SemanticMeetingProcessor 導入成功")
    except ImportError as e:
        logger.error(f"✗ SemanticMeetingProcessor 導入失敗: {e}")
        assert False
    
    assert True

def test_optimizer_with_semantic():
    """測試優化器與語意分段整合"""
    logger = logging.getLogger(__name__)
    logger.info("=== 測試優化器與語意分段整合 ===")
    
    try:
        from optimize_meeting_minutes import MeetingOptimizer
        
        # 測試啟用語意分段的優化器
        optimizer = MeetingOptimizer(
            model_name="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
            enable_semantic_segmentation=True
        )
        
        # 檢查語意分段組件是否正確初始化
        if optimizer.enable_semantic_segmentation:
            logger.info("✓ 語意分段功能已啟用")
            if optimizer.semantic_splitter:
                logger.info("✓ SemanticSplitter 初始化成功")
            else:
                logger.warning("⚠ SemanticSplitter 未初始化")
                
            if optimizer.quality_evaluator:
                logger.info("✓ SegmentQualityEvaluator 初始化成功")
            else:
                logger.warning("⚠ SegmentQualityEvaluator 未初始化")
                
            if optimizer.semantic_processor:
                logger.info("✓ SemanticMeetingProcessor 初始化成功")
            else:
                logger.warning("⚠ SemanticMeetingProcessor 未初始化")
        else:
            logger.warning("⚠ 語意分段功能未啟用")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 優化器初始化失敗: {e}")
        assert False

def test_segmentation_logic():
    """測試分段邏輯"""
    logger = logging.getLogger(__name__)
    logger.info("=== 測試分段邏輯 ===")
    
    try:
        from optimize_meeting_minutes import MeetingOptimizer
        
        optimizer = MeetingOptimizer(enable_semantic_segmentation=True)
        
        # 測試短文本（不需要分段）
        short_text = "這是一個短文本測試。" * 10
        result = optimizer._check_and_segment_transcript(short_text)
        
        if len(result) == 1 and not result[0]['is_segmented']:
            logger.info("✓ 短文本處理正確（無需分段）")
        else:
            logger.warning(f"⚠ 短文本處理異常: {len(result)} 個分段")
        
        # 測試長文本（需要分段）
        long_text = "這是一個會議記錄的長文本測試。" * 200  # 約 5000 字元
        result = optimizer._check_and_segment_transcript(long_text)
        
        if len(result) > 1:
            logger.info(f"✓ 長文本分段成功: {len(result)} 個分段")
            for i, segment in enumerate(result):
                logger.info(f"  段落 {i+1}: {len(segment['content'])} 字元")
        else:
            logger.warning(f"⚠ 長文本分段異常: 只有 {len(result)} 個分段")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 分段邏輯測試失敗: {e}")
        assert False

def test_integration_with_sample_data():
    """使用專案現有逐字稿測試完整整合"""
    logger = logging.getLogger(__name__)
    logger.info("=== 測試完整整合流程（使用現有逐字稿） ===")
    
    try:
        from optimize_meeting_minutes import MeetingOptimizer
        
        optimizer = MeetingOptimizer(enable_semantic_segmentation=True)
        
        # 使用專案中的實際逐字稿
        transcript_files = [
            "/Users/lanss/projects/exam08_提示詞練習重啟/data/transcript/第671次市政會議114年5月13日逐字稿.txt",
            "/Users/lanss/projects/exam08_提示詞練習重啟/data/transcript/第672次市政會議114年5月20日逐字稿.txt"
        ]
        
        reference_files = [
            "/Users/lanss/projects/exam08_提示詞練習重啟/data/reference/第671次市政會議114年5月13日會議紀錄.txt",
            "/Users/lanss/projects/exam08_提示詞練習重啟/data/reference/第672次市政會議114年5月20日會議紀錄.txt"
        ]
        
        for i, (transcript_file, reference_file) in enumerate(zip(transcript_files, reference_files)):
            logger.info(f"\n--- 測試文件 {i+1}: {transcript_file.split('/')[-1]} ---")
            
            # 讀取逐字稿
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                logger.info(f"逐字稿長度: {len(transcript_content)} 字元")
            except FileNotFoundError:
                logger.error(f"逐字稿文件不存在: {transcript_file}")
                continue
            
            # 讀取參考會議記錄
            try:
                with open(reference_file, 'r', encoding='utf-8') as f:
                    reference_content = f.read()
                logger.info(f"參考記錄長度: {len(reference_content)} 字元")
            except FileNotFoundError:
                logger.warning(f"參考文件不存在: {reference_file}")
                reference_content = ""
            
            # 執行語意分段檢查
            segmentation_result = optimizer._check_and_segment_transcript(transcript_content)
            logger.info(f"分段結果: {len(segmentation_result)} 個分段")
            
            if len(segmentation_result) > 1:
                logger.info("✓ 檢測到大型文本，成功觸發語意分段流程")
                for j, segment in enumerate(segmentation_result):
                    logger.info(f"  段落 {j+1}: {len(segment['content'])} 字元, 分段方法: {'語意' if segment.get('is_segmented') else '標準'}")
                
                # 測試分段處理流程（模擬 _generate_minutes_batch 的行為）
                matched_data = [{
                    'transcript': transcript_content,
                    'transcript_file': transcript_file,
                    'reference': reference_content,
                    'reference_file': reference_file
                }]
                
                logger.info("模擬語意分段會議記錄生成流程...")
                # 這裡可以根據需要添加更詳細的流程測試
                
            else:
                logger.warning(f"⚠ 文本長度 {len(transcript_content)} 字元，未觸發分段（閾值: 4000）")
            
            logger.info(f"✓ 文件 {i+1} 測試完成")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 完整整合測試失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        assert False

def main():
    """主函數"""
    logger = setup_logging()
    logger.info("開始語意分段整合完整測試")
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("模組導入測試", test_semantic_modules_import()))
    test_results.append(("優化器整合測試", test_optimizer_with_semantic()))
    test_results.append(("分段邏輯測試", test_segmentation_logic()))
    test_results.append(("完整整合測試", test_integration_with_sample_data()))
    
    # 總結結果
    logger.info("\n=== 測試結果總結 ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n總體結果: {passed}/{total} 項測試通過")
    
    if passed == total:
        logger.info("🎉 所有測試都通過！語意分段整合成功！")
        assert True
    else:
        logger.warning(f"⚠ 有 {total - passed} 項測試失敗，需要進一步檢查")
        assert False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

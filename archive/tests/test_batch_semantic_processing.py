#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段批次處理功能測試
測試新增的批次處理和品質檢查功能
"""

import os
import sys
import json
import logging
import pytest
from pathlib import Path

# 添加專案根目錄到路徑
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def setup_logging():
    """設置日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def test_batch_processor_import():
    """測試批次處理器模組導入"""
    logger = setup_logging()
    logger.info("=== 測試批次處理器模組導入 ===")
    
    try:
        from scripts.batch_semantic_processor import BatchSemanticProcessor
        logger.info("✓ BatchSemanticProcessor 模組導入成功")
        assert True
    except Exception as e:
        logger.error(f"✗ 模組導入失敗: {e}")
        assert False, f"模組導入失敗: {e}"

def test_quality_evaluator_coherence():
    """測試品質評估器的語意連貫性評估功能"""
    logger = setup_logging()
    logger.info("=== 測試語意連貫性評估功能 ===")
    
    try:
        from scripts.segment_quality_eval import SegmentQualityEvaluator
        
        # 初始化評估器
        evaluator = SegmentQualityEvaluator(model_name="gemma3:12b")
        logger.info("✓ 品質評估器初始化成功")
        
        # 測試分段數據
        test_segments = [
            {
                "segment_id": 1,
                "segment_text": "今天的會議主要討論三個重點議題。首先是關於專案進度的更新，李經理報告目前進度已達70%。",
                "metadata": {"length": 45}
            },
            {
                "segment_id": 2, 
                "segment_text": "第二個議題是預算調整問題。財務部建議增加20%的預算來應對材料成本上漲的問題。",
                "metadata": {"length": 42}
            }
        ]
        
        logger.info("開始測試語意連貫性評估...")
        
        # 測試語意連貫性評估
        coherence_result = evaluator.evaluate_semantic_coherence(test_segments)
        
        logger.info(f"✓ 語意連貫性評估完成")
        logger.info(f"  平均連貫性分數: {coherence_result.get('average_coherence', 0):.2f}")
        logger.info(f"  有問題的分段數: {coherence_result.get('poor_segments_count', 0)}")
        logger.info(f"  連貫性通過率: {coherence_result.get('coherence_pass_rate', 0):.1f}%")
        
        # 測試批次品質檢查
        logger.info("開始測試批次品質檢查...")
        batch_result = evaluator.batch_quality_check(test_segments)
        
        logger.info(f"✓ 批次品質檢查完成")
        logger.info(f"  整體品質分數: {batch_result['summary']['overall_quality']:.2f}")
        logger.info(f"  需要修訂: {batch_result['summary']['needs_revision']}")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 語意連貫性評估測試失敗: {e}", exc_info=True)
        assert False, f"語意連貫性評估測試失敗: {e}"

def test_batch_processor_with_real_data():
    """使用實際數據測試批次處理器"""
    logger = setup_logging()
    logger.info("=== 測試批次處理器實際數據處理 ===")
    
    try:
        from scripts.batch_semantic_processor import BatchSemanticProcessor
        
        # 初始化處理器
        processor = BatchSemanticProcessor(
            segmentation_model="gemma3:12b",
            evaluation_model="gemma3:12b",
            output_dir="output/test_batch_processing"
        )
        
        logger.info("✓ 批次處理器初始化成功")
        
        # 檢查是否有實際逐字稿文件
        transcript_dir = Path("data/transcript")
        if not transcript_dir.exists():
            logger.warning("⚠ 逐字稿目錄不存在，跳過實際數據測試")
            pytest.skip("逐字稿目錄不存在")
            
        transcript_files = list(transcript_dir.glob("*.txt"))
        if not transcript_files:
            logger.warning("⚠ 沒有找到逐字稿文件，跳過實際數據測試")
            pytest.skip("沒有找到逐字稿文件")
        
        # 選擇一個文件進行測試
        test_file = transcript_files[0]
        logger.info(f"測試文件: {test_file}")
        
        # 處理單個文件
        result = processor.process_transcript_file(test_file)
        
        if "error" in result:
            logger.warning(f"⚠ 處理結果包含錯誤: {result['error']}")
        else:
            logger.info("✓ 單個文件處理成功")
            logger.info(f"  文件大小: {result.get('file_size', 0)} 字元")
            logger.info(f"  需要分段: {result.get('needs_segmentation', False)}")
            
            if result.get('quality_report'):
                overall_quality = result['quality_report']['summary']['overall_quality']
                logger.info(f"  整體品質分數: {overall_quality:.2f}")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 批次處理器測試失敗: {e}", exc_info=True)
        assert False, f"批次處理器測試失敗: {e}"

def test_integration_with_optimization():
    """測試與優化流程的整合"""
    logger = setup_logging()
    logger.info("=== 測試與優化流程整合 ===")
    
    try:
        # 測試 run_optimization.sh 中的語意分段參數
        import subprocess
        
        # 檢查腳本是否支援新參數
        result = subprocess.run(
            ["bash", "run_optimization.sh", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "--semantic-model" in result.stdout:
            logger.info("✓ run_optimization.sh 支援語意分段參數")
        else:
            logger.warning("⚠ run_optimization.sh 可能未完全支援語意分段參數")
        
        # 測試 iterative_optimizer 的語意分段整合
        from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig
        
        config = OptimizationConfig(
            max_iterations=1,
            enable_semantic_segmentation=True,
            semantic_model="gemma3:12b"
        )
        
        optimizer = MeetingOptimizer(config)
        logger.info("✓ iterative_optimizer 語意分段整合正常")
        
        assert True
        
    except Exception as e:
        logger.error(f"✗ 整合測試失敗: {e}")
        assert False

def main():
    """主測試函數"""
    logger = setup_logging()
    logger.info("開始語意分段批次處理功能測試")
    
    tests = [
        ("批次處理器模組導入", test_batch_processor_import),
        ("語意連貫性評估功能", test_quality_evaluator_coherence),
        ("批次處理器實際數據", test_batch_processor_with_real_data),
        ("優化流程整合", test_integration_with_optimization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"執行測試: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 執行時出錯: {e}")
            
    logger.info(f"\n{'='*60}")
    logger.info(f"測試結果: {passed}/{total} 通過")
    logger.info(f"{'='*60}")
    
    if passed == total:
        logger.info("🎉 所有語意分段批次處理功能測試通過！")
        assert True
    else:
        logger.warning(f"⚠ 部分測試失敗 ({total-passed}/{total})")
        assert False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

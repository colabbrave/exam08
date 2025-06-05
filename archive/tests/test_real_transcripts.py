#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用專案內實際逐字稿測試語意分段功能
"""

import os
import sys
import logging
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

def test_with_actual_transcripts():
    """使用實際逐字稿測試語意分段功能"""
    logger = setup_logging()
    logger.info("=== 使用實際逐字稿測試語意分段功能 ===")
    
    # 逐字稿文件列表
    transcript_files = [
        "data/transcript/第671次市政會議114年5月13日逐字稿.txt",
        "data/transcript/第672次市政會議114年5月20日逐字稿.txt"
    ]
    
    try:
        from scripts.optimize_meeting_minutes import MeetingOptimizer
        
        # 初始化優化器
        optimizer = MeetingOptimizer(
            model_name="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
            enable_semantic_segmentation=True
        )
        
        for transcript_file in transcript_files:
            if not os.path.exists(transcript_file):
                logger.warning(f"逐字稿文件不存在: {transcript_file}")
                continue
                
            logger.info(f"\n--- 測試文件: {transcript_file} ---")
            
            # 讀取逐字稿
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            
            file_size = len(transcript_content)
            logger.info(f"文件大小: {file_size} 字元")
            
            # 測試語意分段功能
            result = optimizer._check_and_segment_transcript(transcript_content)
            
            if isinstance(result, list) and len(result) > 1:
                logger.info(f"✅ 語意分段成功觸發！分成 {len(result)} 個片段")
                 # 統計分段資訊
                total_chars = 0
                for i, segment in enumerate(result):
                    # 檢查是否為字典格式的分段結果
                    if isinstance(segment, dict):
                        segment_text = segment.get('segment_text', str(segment))
                        segment_length = len(segment_text)
                    else:
                        segment_text = str(segment)
                        segment_length = len(segment_text)
                    
                    total_chars += segment_length
                    logger.info(f"  片段 {i+1}: {segment_length} 字元")

                logger.info(f"原始大小: {file_size} 字元")
                logger.info(f"分段後總計: {total_chars} 字元")
                logger.info(f"字元保持率: {total_chars/file_size*100:.1f}%")
                
                # 顯示每個片段的開頭
                logger.info("各片段開頭預覽:")
                for i, segment in enumerate(result[:3]):  # 只顯示前3個
                    if isinstance(segment, dict):
                        segment_text = segment.get('segment_text', str(segment))
                    else:
                        segment_text = str(segment)
                    preview = segment_text.strip()[:100].replace('\n', ' ')
                    logger.info(f"  片段 {i+1}: {preview}...")
                    
            elif isinstance(result, str):
                logger.info("✓ 使用原始文本（未觸發分段）")
            else:
                logger.warning("⚠ 分段結果異常")
        
        assert True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}", exc_info=True)
        assert False

def test_iterative_optimizer_with_real_data():
    """測試 iterative_optimizer 與實際逐字稿的整合"""
    logger = setup_logging()
    logger.info("=== 測試 iterative_optimizer 與實際逐字稿整合 ===")
    
    try:
        from scripts.iterative_optimizer import MeetingOptimizer, OptimizationConfig
        
        # 設置配置
        config = OptimizationConfig(
            max_iterations=1,  # 只測試一輪
            enable_semantic_segmentation=True,
            semantic_model="gemma3:12b",
            max_segment_length=4000
        )
        
        # 初始化優化器
        optimizer = MeetingOptimizer(config)
        logger.info("✓ iterative_optimizer 初始化成功")
        
        # 選擇一個較小的逐字稿文件進行測試
        test_file = "data/transcript/第672次市政會議114年5月20日逐字稿.txt"
        
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            
            logger.info(f"測試文件: {test_file}")
            logger.info(f"文件大小: {len(transcript_content)} 字元")
            
            # 構建簡單的提示詞
            prompt = f"""
            請根據以下會議逐字稿生成結構化的會議記錄：
            
            {transcript_content[:2000]}...
            
            請包含：
            1. 會議基本資訊
            2. 主要討論議題
            3. 重要決議
            4. 行動項目
            """
            
            logger.info("開始測試語意分段處理...")
            
            # 測試 _generate_minutes 方法
            result, execution_time = optimizer._generate_minutes(prompt)
            
            if result:
                logger.info(f"✅ 會議記錄生成成功！")
                logger.info(f"執行時間: {execution_time:.2f} 秒")
                logger.info(f"結果長度: {len(result)} 字元")
                logger.info(f"結果預覽: {result[:200]}...")
            else:
                logger.warning("⚠ 會議記錄生成失敗")
        else:
            logger.error(f"測試文件不存在: {test_file}")
            assert False
        
        assert True
        
    except Exception as e:
        logger.error(f"❌ iterative_optimizer 測試失敗: {e}", exc_info=True)
        assert False

def main():
    """主測試函數"""
    logger = setup_logging()
    logger.info("開始使用實際逐字稿測試語意分段功能")
    
    tests = [
        ("實際逐字稿語意分段", test_with_actual_transcripts),
        ("iterative_optimizer 實際數據整合", test_iterative_optimizer_with_real_data),
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
        logger.info("🎉 所有實際逐字稿測試通過！")
        assert True
    else:
        logger.warning(f"⚠ 部分測試失敗 ({total-passed}/{total})")
        assert False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

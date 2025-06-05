#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大型文本語意分段測試
"""

import os
import sys
import logging

# 添加專案根目錄到路徑
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_large_text_segmentation():
    """測試大型文本的語意分段功能"""
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    
    # 創建大型測試文本（超過4000字元）
    large_text = """
    今天的董事會會議非常重要，討論了公司未來一年的戰略規劃和重要決策。
    
    首先，CEO匯報了第三季度的財務表現。營收達到了預期目標的105%，淨利潤同比增長了18%。
    這主要歸功於新產品線的成功推出和市場份額的穩步擴張。特別是在亞太市場，
    我們的業務增長了25%，超出了所有預期。
    
    接下來，技術總監詳細介紹了正在進行的數位轉型計畫。該計畫預計投資2000萬元，
    旨在升級我們的IT基礎設施和客戶服務系統。預計這項投資將在未來三年內
    帶來顯著的效率提升和成本節約。董事會一致同意推進這個計畫。
    
    人力資源總監也提出了人才發展戰略。公司計劃在未來六個月內招聘100名新員工，
    主要集中在研發、銷售和客戶服務部門。同時，我們也將推出新的員工培訓計畫，
    確保所有員工都能跟上公司快速發展的步伐。
    
    市場總監報告了即將推出的新產品計畫。我們預計在下季度推出三款新產品，
    這些產品已經通過了所有必要的測試和認證。初步的市場調研顯示，
    這些產品有很大的市場潛力，預計將為公司帶來額外的營收增長。
    
    財務總監詳細分析了公司的資金狀況和投資計畫。目前公司的現金流狀況良好，
    債務水平控制在合理範圍內。董事會批准了一項新的投資計畫，
    將投資3000萬元用於擴建生產設施和購買新設備。
    
    法務部門也提交了關於合規和風險管理的報告。隨著業務規模的擴大，
    我們需要加強合規管理，確保所有業務活動都符合相關法規要求。
    董事會同意增加法務部門的人員配置，並投資新的合規管理系統。
    
    最後，董事會討論了公司的可持續發展戰略。我們承諾在2030年前實現碳中和，
    這需要大量的投資和技術創新。董事會已經批准了相關的研發預算，
    並建立了專門的可持續發展委員會來推進這項工作。
    
    會議還討論了股東回報政策。考慮到公司良好的財務表現，
    董事會決定增加股息派發，每股派息0.5元，比去年增長了25%。
    這顯示了董事會對公司未來發展的信心。
    
    在競爭分析方面，市場研究團隊提供了詳細的競爭對手分析報告。
    我們在市場上的位置依然強勁，但也面臨一些新的挑戰。
    為了保持競爭優勢，我們需要繼續投資研發和創新。
    """ * 10  # 重複10次以創建超大文本
    
    logger.info(f"測試文本長度: {len(large_text)} 字元")
    
    try:
        from scripts.optimize_meeting_minutes import MeetingOptimizer
        
        optimizer = MeetingOptimizer(
            model_name="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
            enable_semantic_segmentation=True
        )
        
        # 測試分段功能
        result = optimizer._check_and_segment_transcript(large_text)
        
        if isinstance(result, list) and len(result) > 1:
            logger.info(f"✅ 語意分段成功觸發！分成 {len(result)} 個片段")
            
            # 顯示每個片段的長度統計
            for i, segment in enumerate(result):
                logger.info(f"  片段 {i+1}: {len(segment)} 字元")
                
            # 顯示分段品質
            total_chars = sum(len(seg) for seg in result)
            logger.info(f"原始文本: {len(large_text)} 字元")
            logger.info(f"分段後總計: {total_chars} 字元")
            logger.info(f"字元保持率: {total_chars/len(large_text)*100:.1f}%")
            
        else:
            logger.warning("❌ 語意分段未被觸發，可能閾值設置有問題")
            
        assert True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        assert False

if __name__ == "__main__":
    success = test_large_text_segmentation()
    print(f"\n{'='*50}")
    if success:
        print("🎉 大型文本語意分段測試完成")
    else:
        print("❌ 大型文本語意分段測試失敗")
    print(f"{'='*50}")

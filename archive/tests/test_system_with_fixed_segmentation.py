#!/usr/bin/env python3
"""
會議記錄優化系統修正驗證測試
測試修正後的語意分段功能是否解決了203段問題
"""

import os
import sys
import tempfile
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_meeting_content():
    """創建測試用會議記錄內容（約15000字元）"""
    base_content = """
會議主題：數位轉型策略討論會
會議時間：2024年12月15日下午2點至4點
與會人員：張執行長、李資訊長、王行銷總監、陳人資總監、林財務長

會議開始：
張執行長首先歡迎大家參與本次數位轉型策略討論會。他表示，在當前快速變化的商業環境中，數位轉型已經不是選擇，而是企業生存的必要條件。我們需要制定一個全面而可行的數位轉型策略，以確保企業在競爭激烈的市場中保持領先地位。

李資訊長接著報告了目前的技術基礎設施現況。他指出，我們的核心系統雖然運行穩定，但在靈活性和擴展性方面還有很大的改進空間。建議採用雲端原生架構，導入微服務設計模式，並建立統一的數據平台來支撐未來的業務發展。這將需要大約18個月的時間完成，預算估計在800萬到1200萬之間。

王行銷總監從市場角度分析了數位轉型的迫切性。她提到，客戶行為正在快速數位化，特別是年輕消費者群體。我們需要建立全通路的客戶體驗，整合線上線下的接觸點，並運用數據分析來個性化客戶服務。同時，社群媒體行銷和內容行銷將成為重要的策略重點。

陳人資總監強調了人才發展在數位轉型中的關鍵作用。她表示，技術進步需要相應的人才支撐，建議制定全面的數位技能培訓計劃，包括內部培訓、外部課程和跨部門輪調。同時，需要建立新的績效評估體系，以適應數位化工作模式的要求。

林財務長從財務角度評估了數位轉型的投資回報。他指出，雖然初期投資較大，但長期來看，數位化能夠顯著提升營運效率，降低成本，並創造新的收入來源。建議分階段投資，優先處理投資回報率較高的項目，並建立詳細的財務監控機制。

討論環節中，大家針對具體的實施步驟進行了深入交流。首先確定了三個優先級較高的項目：客戶關係管理系統升級、電子商務平台建設、以及數據分析平台建置。這些項目將在未來六個月內啟動，並設定明確的里程碑和成功指標。

關於組織架構調整，與會者一致認為需要成立專門的數位轉型委員會，由張執行長親自擔任主席，各部門主管作為委員。同時設立數位轉型辦公室，負責日常的協調和推進工作。這個辦公室將配置專職人員，包括項目經理、數據分析師和變革管理專家。

在風險管理方面，大家討論了可能面臨的挑戰，包括技術風險、人員阻力、預算超支等。決定建立風險評估矩陣，定期檢視和更新風險狀況，並制定相應的應對措施。特別是對於關鍵系統的遷移，將採用漸進式的方法，確保業務連續性。

會議最後，張執行長總結了本次討論的重點和決議事項。他強調，數位轉型是一個長期的過程，需要全體員工的共同努力和持續學習。公司將提供充分的資源支持，但同時也期望每個人都能積極擁抱變化，為企業的未來發展貢獻力量。

下一步行動計劃包括：成立數位轉型委員會、制定詳細的項目計劃、啟動人才培訓計劃、建立績效指標體系等。下次會議將在一個月後召開，屆時將檢視各項工作的進展情況。
"""
    
    # 複製內容多次以達到約15000字元
    content = ""
    target_length = 15000
    while len(content) < target_length:
        content += base_content
    
    return content[:target_length]

def main():
    """主測試函數"""
    print("=== 會議記錄優化系統修正驗證測試 ===\n")
    
    # 創建測試內容
    test_content = create_test_meeting_content()
    print(f"測試內容長度: {len(test_content)} 字元")
    
    # 創建臨時測試文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    print(f"臨時測試文件: {temp_file}")
    
    try:
        # 導入並運行優化系統
        from scripts.optimize_meeting_minutes import MeetingOptimizer
        
        # 創建優化器實例
        optimizer = MeetingOptimizer()
        
        print("\n=== 開始語意分段測試 ===")
        
        # 測試分段功能（使用預設的4000字元作為最大長度）
        segments = optimizer._simple_segment(test_content, max_length=4000)
        
        print(f"\n分段結果:")
        print(f"總分段數: {len(segments)}")
        
        # 檢查分段詳情
        total_chars = 0
        short_segments = 0
        
        for i, segment in enumerate(segments, 1):
            content_length = len(segment['content'])
            total_chars += content_length
            print(f"  第 {i} 段: {content_length} 字元")
            
            if content_length < 500:  # 檢查過短分段
                short_segments += 1
        
        print(f"\n統計結果:")
        print(f"  原始內容: {len(test_content)} 字元")
        print(f"  分段總計: {total_chars} 字元")
        print(f"  過短分段數 (<500字元): {short_segments}")
        
        # 判斷測試結果
        if len(segments) < 10 and short_segments == 0:
            print(f"\n✅ 測試通過！分段功能正常工作")
            print(f"   - 分段數量合理: {len(segments)} 段")
            print(f"   - 無過短分段問題")
            print(f"   - 203段問題已修正 ✓")
        else:
            print(f"\n❌ 測試失敗！")
            if len(segments) >= 10:
                print(f"   - 分段數量過多: {len(segments)} 段")
            if short_segments > 0:
                print(f"   - 存在過短分段: {short_segments} 個")
    
    except Exception as e:
        print(f"\n❌ 測試執行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理臨時文件
        try:
            os.unlink(temp_file)
            print(f"\n清理臨時文件: {temp_file}")
        except:
            pass

if __name__ == "__main__":
    main()

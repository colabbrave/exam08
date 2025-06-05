"""
台灣會議記錄專用評估器

提供針對台灣政府會議記錄特化的評估指標，包括：
1. 結構完整性評分
2. 台灣政府用語適配性
3. 行動項目具體性
"""
import re
from typing import Dict, List, Tuple, Optional, Any, Union
import json
from pathlib import Path

class TaiwanMeetingEvaluator:
    """台灣會議記錄專用評估器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化評估器
        
        Args:
            config_path: 配置檔案路徑，如為None則使用預設配置
        """
        self.required_elements = {
            '會議基本資訊': ['時間', '地點', '主持人', '與會人員'],
            '程序完整性': ['報告事項', '討論事項', '決議事項'],
            '台灣政府格式': ['局處', '議員', '市政府', '會議紀錄']
        }
        
        # 載入自定義配置（如果提供）
        if config_path and Path(config_path).exists():
            self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> None:
        """載入自定義配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.required_elements = config.get('required_elements', self.required_elements)
        except Exception as e:
            print(f"警告：載入配置檔案失敗，使用預設配置。錯誤：{e}")
    
    def evaluate(self, reference: str, candidate: str) -> Dict[str, Union[float, str]]:
        """
        評估會議記錄質量
        
        Args:
            reference: 參考文本（用於比較）
            candidate: 待評估的會議記錄文本
            
        Returns:
            包含各項評分的字典
        """
        try:
            scores: Dict[str, Union[float, str]] = {}
            
            # 1. 結構完整性評分 (40%)
            structure_score = self._evaluate_structure(candidate)
            scores['structure_score'] = structure_score
            
            # 2. 台灣政府用語適配性 (30%)
            taiwan_score = self._evaluate_taiwan_context(candidate)
            scores['taiwan_context_score'] = taiwan_score
            
            # 3. 行動項目具體性 (30%)
            action_score = self._evaluate_action_items(candidate)
            scores['action_specificity_score'] = action_score
            
            # 4. 計算綜合分數（加權平均）
            scores['taiwan_meeting_score'] = (
                structure_score * 0.4 + 
                taiwan_score * 0.3 + 
                action_score * 0.3
            )
            
            # 5. 如果提供了參考文本，計算與參考文本的相似度
            if reference and reference.strip():
                # 計算與參考文本的結構相似度
                ref_structure = self._evaluate_structure(reference)
                cand_structure = structure_score
                
                # 計算與參考文本的用語相似度
                ref_taiwan = self._evaluate_taiwan_context(reference)
                cand_taiwan = taiwan_score
                
                # 計算相似度調整因子 (0.8-1.2)
                structure_sim = 1.0 - abs(ref_structure - cand_structure)
                taiwan_sim = 1.0 - abs(ref_taiwan - cand_taiwan)
                similarity_factor = 0.8 + 0.4 * ((structure_sim + taiwan_sim) / 2.0)
                
                # 調整綜合分數
                taiwan_score_value = scores.get('taiwan_meeting_score', 0.0)
                if isinstance(taiwan_score_value, (int, float)):
                    scores['taiwan_meeting_score'] = min(1.0, float(taiwan_score_value) * similarity_factor)
                else:
                    scores['taiwan_meeting_score'] = 0.0
                scores['similarity_to_reference'] = float((structure_sim + taiwan_sim) / 2.0)
            
            return scores
            
        except Exception as e:
            # 發生錯誤時返回最低分
            print(f"評估會議記錄時出錯: {str(e)}")
            return {
                'taiwan_meeting_score': 0.0,
                'structure_score': 0.0,
                'taiwan_context_score': 0.0,
                'action_specificity_score': 0.0,
                'error': str(e)
            }
    
    def _evaluate_structure(self, text: str) -> float:
        """
        評估會議記錄結構完整性
        
        Returns:
            結構完整性分數 (0-1)
        """
        try:
            if not text or not isinstance(text, str):
                return 0.0
                
            # 基本結構檢查
            required_sections = ['會議時間', '與會人員', '討論事項', '決議事項', '行動項目']
            present_sections = [sec for sec in required_sections if sec in text]
            
            # 計算基本分數 (0.7 權重)
            section_score = (len(present_sections) / len(required_sections)) * 0.7
            
            # 檢查層次結構 (0.2 權重)
            heading_pattern = r'#{1,3}\s+[^\n]+'
            headings = re.findall(heading_pattern, text)
            has_hierarchy = len(headings) >= 3
            hierarchy_score = 0.2 if has_hierarchy else 0.0
            
            # 檢查段落結構 (0.1 權重)
            has_paragraphs = '\n\n' in text
            paragraph_score = 0.1 if has_paragraphs else 0.0
            
            # 檢查是否有具體行動項目
            has_action_items = any(item in text for item in ['行動項目', '待辦事項', '後續處理'])
            action_bonus = 0.1 if has_action_items else 0.0
            
            total_score = section_score + hierarchy_score + paragraph_score + action_bonus
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            print(f"評估結構時出錯: {str(e)}")
            return 0.0
    
    def _evaluate_taiwan_context(self, text: str) -> float:
        """
        評估台灣政府用語使用情況
        
        Returns:
            台灣語境適配分數 (0-1)
        """
        try:
            if not text or not isinstance(text, str):
                return 0.0
                
            # 台灣用語關鍵詞（按重要性分組）
            taiwan_terms = [
                # 高權重（政府單位和職稱）
                '市政府', '區公所', '里辦公處', '局處', '科', '課', '股',
                '市長', '局長', '處長', '科長', '課長', '股長', '承辦人',
                '議員', '里長', '主任', '委員', '顧問',
                
                # 中權重（程序用語）
                '會議紀錄', '決議', '裁示', '指示', '報告', '討論', '決議事項',
                '提案', '說明', '散會', '主席', '紀錄',
                
                # 低權重（公文用語）
                '奉交下', '敬陳', '鑒核', '核示', '核備', '備查', '照辦',
                
                # 日期格式
                r'\d+年\d+月\d+日', r'\d+/\d+/\d+',
                
                # 文號格式
                r'[\u4e00-\u9fa5]+\d+[\u4e00-\u9fa5]*\d*號',
                
                # 其他常見用語
                '請查照', '請鑒核', '請核示', '請核備', '請備查',
                '報請', '陳報', '陳核', '陳閱', '陳核示'
            ]
            
            # 大陸用語（扣分項）
            mainland_terms = [
                '领导', '部门', '会议记录', '办理', '审批', '汇报',
                '汇报工作', '汇报情况', '汇报如下', '汇报内容', '汇报材料',
                '领导批示', '领导指示', '领导要求', '领导强调', '领导指出',
                '贯彻落实', '切实做好', '认真做好', '抓紧抓好', '切实加强'
            ]
            
            # 計算台灣用語匹配數（加權計算）
            scores = []
            for i, term in enumerate(taiwan_terms):
                # 前20個詞（政府單位和職稱）權重較高
                weight = 1.5 if i < 20 else (1.2 if i < 40 else 1.0)
                if re.search(term, text):
                    scores.append(weight)
            
            # 計算加權分數
            taiwan_score = sum(scores) / (len(taiwan_terms) * 1.5)  # 標準化到0-1
            
            # 計算大陸用語扣分
            mainland_penalty: float = 0.0
            for term in mainland_terms:
                if term in text:
                    mainland_penalty += 0.05  # 每個大陸用語扣0.05分
            
            # 計算最終分數（0-1之間）
            final_score = max(0, min(1.0, taiwan_score - min(0.3, mainland_penalty)))
            
            # 確保分數不會為0（除非完全沒有匹配）
            if final_score == 0 and any(term in text for term in taiwan_terms[:10]):
                return 0.1  # 最低給0.1分，如果至少有匹配到一些基本用語
                
            return final_score
            
        except Exception as e:
            print(f"評估台灣語境時出錯: {str(e)}")
            return 0.0
    
    def _evaluate_action_items(self, text: str) -> float:
        """
        評估行動項目的具體性
        
        Returns:
            行動項目具體性分數 (0-1)
        """
        try:
            if not text or not isinstance(text, str):
                return 0.0
                
            # 行動項目模式（按重要性排序）
            action_patterns = [
                # 高權重（明確的負責人和期限）
                r'負責[人單位][:：]\s*[^\n]+',
                r'[負主]?責[人單位][:：]\s*[^\n]+',
                r'期限[:：]\s*[^\n]+',
                r'完成[時間日期][:：]\s*[^\n]+',
                
                # 中權重（明確的動作和對象）
                r'請[\w\u4e00-\u9fa5]+(?:局|處|室|科|所|課|股|隊)[^\n]*辦理',
                r'[應須]\s*[^\n]*(?:辦理|處理|研議|評估|檢討|提供|回覆)',
                
                # 低權重（表格格式）
                r'\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|',  # 簡單的表格格式
                r'\d+\.\s*[^\n]+',  # 編號列表
                
                # 其他常見模式
                r'追蹤[事項項目][:：]',
                r'後續[處理作業][:：]',
                r'待辦[事項項目][:：]'
            ]
            
            # 檢查行動項目部分
            action_section = re.search(r'##?\s*(?:行動項目|決議事項|後續處理|待辦事項)[^#]*', text, re.DOTALL | re.IGNORECASE)
            if not action_section:
                # 如果沒有明確的行動項目標題，檢查整個文本中是否有行動項目
                action_text = text
                has_action_section = False
            else:
                action_text = action_section.group(0)
                has_action_section = True
            
            # 計算匹配的模式數（加權）
            total_score = 0.0
            max_scores = [1.0] * 4 + [0.8] * 2 + [0.5] * 4 + [0.3] * 3  # 每個模式的最大分數
            
            for i, pattern in enumerate(action_patterns):
                weight = max_scores[i] if i < len(max_scores) else 0.5
                if re.search(pattern, action_text):
                    total_score += weight
            
            # 如果有明確的行動項目部分，給予基礎分
            if has_action_section:
                base_score = 0.3
            else:
                base_score = 0.1
            
            # 計算最終分數（0-1之間）
            final_score = min(1.0, base_score + (total_score * 0.7))
            
            # 確保分數不會為0（除非完全沒有匹配）
            if final_score == 0 and any(re.search(p, text) for p in action_patterns[:5]):
                return 0.1  # 最低給0.1分，如果至少有匹配到一些基本模式
                
            return final_score
            
        except Exception as e:
            print(f"評估行動項目時出錯: {str(e)}")
            return 0.0


def test_evaluation_system() -> None:
    """測試評估系統是否能區分差異"""
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
    
    evaluator = TaiwanMeetingEvaluator()
    print("="*50)
    print("台灣會議記錄評估系統測試")
    print("="*50)
    
    results = []
    for name, text in test_cases:
        scores = evaluator.evaluate("", text)
        results.append((name, scores))
        
    # 顯示結果
    for name, scores in results:
        print(f"\n{name}:")
        print(f"  結構完整性: {scores['structure_score']:.3f}")
        print(f"  台灣語境適配: {scores['taiwan_context_score']:.3f}")
        print(f"  行動項目具體性: {scores['action_specificity_score']:.3f}")
        print(f"  綜合分數: {scores['taiwan_meeting_score']:.3f}")
    
    # 檢查分數是否遞增
    score_values = [r[1]['taiwan_meeting_score'] for r in results]
    if score_values != sorted(score_values):
        print("\n警告：評估系統可能無法正確區分不同質量的會議記錄")
    else:
        print("\n評估系統測試通過：分數隨質量提升而增加")

if __name__ == "__main__":
    test_evaluation_system()

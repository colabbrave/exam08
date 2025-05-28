"""
穩定性評估指標模組

提供多種指標來評估生成文本的穩定性，包括：
- 格式一致性
- 長度穩定性
- 關鍵要素覆蓋率
- 語義穩定性
- 結構穩定性
"""
import re
import numpy as np
from typing import List, Dict, Tuple, Union, Any
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import difflib
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StabilityMetrics:
    """
    穩定性評估指標類
    
    提供多種穩定性評估方法，用於評估生成文本的一致性、穩定性和可靠性。
    """
    
    def __init__(self, min_texts_for_stability: int = 3):
        """
        初始化穩定性評估器
        
        Args:
            min_texts_for_stability: 計算穩定性所需的最小文本數量
        """
        self.min_texts = max(2, min_texts_for_stability)
    
    def calculate_stability_score(self, texts: List[str]) -> Dict[str, float]:
        """
        計算綜合穩定性分數
        
        Args:
            texts: 待評估的文本列表（至少需要2個文本）
            
        Returns:
            Dict[str, float]: 包含各項穩定性指標的分數字典
        """
        if len(texts) < 2:
            logger.warning("至少需要2個文本來計算穩定性")
            return {
                "format_consistency": 1.0,
                "length_stability": 1.0,
                "key_element_coverage": 1.0,
                "semantic_stability": 1.0,
                "overall_stability": 1.0
            }
        
        metrics = {
            "format_consistency": self.calculate_format_consistency(texts),
            "length_stability": self.calculate_length_stability(texts),
            "key_element_coverage": self.calculate_key_element_coverage(texts),
            "semantic_stability": self.calculate_semantic_stability(texts),
        }
        
        # 計算綜合穩定性分數（加權平均）
        weights = {
            "format_consistency": 0.3,
            "length_stability": 0.2,
            "key_element_coverage": 0.3,
            "semantic_stability": 0.2
        }
        
        metrics["overall_stability"] = sum(
            metrics[metric] * weights[metric] 
            for metric in weights
        )
        
        return metrics
    
    def calculate_format_consistency(self, texts: List[str]) -> float:
        """
        計算格式一致性
        
        通過比較文本的結構特徵（如標題、段落、列表等）來評估格式一致性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 格式一致性分數 (0-1)
        """
        if len(texts) < 2:
            return 1.0
            
        # 提取結構特徵
        features = []
        for text in texts:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                continue
                
            # 計算各種結構特徵
            feature = [
                len(lines),  # 總行數
                sum(len(line) for line in lines) / len(lines),  # 平均行長
                sum(1 for line in lines if line.endswith(':')) / len(lines),  # 標題比例
                sum(1 for line in lines if line.startswith('-')) / len(lines),  # 列表比例
                sum(1 for line in lines if line.strip().isdigit() and len(line.strip()) <= 2) / len(lines),  # 編號列表比例
                sum(1 for line in lines if any(c.isupper() for c in line) and len(line) < 30) / len(lines),  # 大寫標題比例
                sum(1 for line in lines if len(line) > 50) / len(lines),  # 長行比例
            ]
            features.append(feature)
        
        if len(features) < 2:
            return 0.0
            
        # 計算相似度矩陣
        try:
            similarity_matrix = cosine_similarity(features)
            np.fill_diagonal(similarity_matrix, 0)  # 排除自相似
            
            # 計算平均相似度
            n = len(similarity_matrix)
            if n < 2:
                return 0.0
                
            avg_similarity = np.sum(similarity_matrix) / (n * (n - 1))
            return float(avg_similarity)
            
        except Exception as e:
            logger.error(f"計算格式一致性時出錯: {str(e)}")
            return 0.0
    
    def calculate_length_stability(self, texts: List[str]) -> float:
        """
        計算長度穩定性
        
        評估生成文本長度的一致性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 長度穩定性分數 (0-1)
        """
        if len(texts) < 2:
            return 1.0
            
        lengths = [len(text) for text in texts]
        avg_length = np.mean(lengths)
        if avg_length == 0:
            return 0.0
            
        # 計算變異係數的倒數作為穩定性指標
        cv = np.std(lengths) / avg_length
        return float(1.0 / (1.0 + cv))
    
    def calculate_key_element_coverage(self, texts: List[str]) -> float:
        """
        計算關鍵要素覆蓋率
        
        評估關鍵要素（如時間、參與者、決議等）在多次生成中的一致性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 關鍵要素覆蓋率 (0-1)
        """
        if len(texts) < 2:
            return 1.0
            
        # 定義關鍵要素的關鍵詞模式
        key_patterns = {
            'time': r'時間[:：]|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[:：]\d{2}',
            'participants': r'與會者[:：]|參與人[:：]|出席人[:：]',
            'agenda': r'議程[:：]|議題[:：]',
            'decision': r'決議[:：]|決定[:：]|結論[:：]',
            'action': r'行動項目[:：]|待辦[:：]|任務[:：]',
            'deadline': r'期限[:：]|截止日[:：]|完成時間[:：]'
        }
        
        # 統計每個關鍵要素的出現次數
        element_counts = {key: 0 for key in key_patterns}
        
        for text in texts:
            for element, pattern in key_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    element_counts[element] += 1
        
        # 計算覆蓋率
        total_elements = len(texts) * len(key_patterns)
        if total_elements == 0:
            return 0.0
            
        covered_elements = sum(
            min(count, len(texts)) 
            for count in element_counts.values()
        )
        
        return covered_elements / total_elements
    
    def calculate_semantic_stability(self, texts: List[str]) -> float:
        """
        計算語義穩定性
        
        使用TF-IDF向量化後計算文本之間的語義相似度
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 語義穩定性分數 (0-1)
        """
        if len(texts) < 2:
            return 1.0
            
        try:
            # 使用TF-IDF向量化文本
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 計算相似度矩陣
            similarity_matrix = cosine_similarity(tfidf_matrix)
            np.fill_diagonal(similarity_matrix, 0)  # 排除自相似
            
            # 計算平均相似度
            n = len(similarity_matrix)
            if n < 2:
                return 0.0
                
            avg_similarity = np.sum(similarity_matrix) / (n * (n - 1))
            return float(avg_similarity)
            
        except Exception as e:
            logger.error(f"計算語義穩定性時出錯: {str(e)}")
            return 0.0

    @staticmethod
    def calculate_length_variation(texts: List[str]) -> float:
        """
        計算長度變異係數
        
        值越小表示穩定性越高
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 長度變異係數
        """
        lengths = [len(text) for text in texts]
        if len(lengths) < 2:
            return 0.0
        return float(np.std(lengths) / (np.mean(lengths) + 1e-8))

    @staticmethod
    def calculate_key_entities_consistency(texts: List[str]) -> float:
        """
        計算關鍵實體一致性
        
        通過比較文本中的命名實體來評估一致性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            float: 關鍵實體一致性分數 (0-1)
        """
        if len(texts) < 2:
            return 1.0
            
        # 簡單實現：使用TF-IDF計算文本相似度
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        try:
            tfidf = vectorizer.fit_transform(texts)
            similarity = (tfidf * tfidf.T).toarray()
            np.fill_diagonal(similarity, 0)  # 排除自相似
            n = len(similarity)
            return float(similarity.sum() / (n * (n - 1)) if n > 1 else 1.0)
        except Exception as e:
            print(f"計算關鍵實體一致性時出錯: {str(e)}")
            return 0.5  # 出錯時返回中間值

    @classmethod
    def calculate_all_metrics(cls, texts: List[str]) -> Dict[str, float]:
        """
        計算所有穩定性指標
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            Dict[str, float]: 包含所有穩定性指標的字典
        """
        return {
            "format_consistency": cls.calculate_format_consistency(texts),
            "length_variation": cls.calculate_length_variation(texts),
            "key_entities_consistency": cls.calculate_key_entities_consistency(texts)
        }

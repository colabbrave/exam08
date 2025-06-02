"""
評估器實現

實現多指標評估邏輯，包括穩定性評估
"""
from typing import Dict, List, Tuple, Optional, Any, Union
import json
from pathlib import Path
import numpy as np
from .config import EvaluationConfig, MetricCategory, MetricConfig
from .stability_metrics import StabilityMetrics
import logging

class MeetingEvaluator:
    """會議記錄評估器"""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()
        self.stability_metrics = StabilityMetrics()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """初始化指標計算器"""
        self.metric_calculators = {
            "bertscore_f1": self._calculate_bertscore,
            "rouge1": lambda r, c: self._calculate_rouge(r, c, "rouge1"),
            "rouge2": lambda r, c: self._calculate_rouge(r, c, "rouge2"),
            "rougeL": lambda r, c: self._calculate_rouge(r, c, "rougeL"),
            "section_heading_quality": self._calculate_heading_quality,
            "paragraph_structure": self._calculate_paragraph_structure,
            "list_usage": self._calculate_list_usage
        }
    
    def evaluate(self, reference: str, candidate: str) -> Dict[str, Any]:
        """
        評估候選文本
        
        Args:
            reference: 參考文本
            candidate: 待評估文本
            
        Returns:
            包含各項指標分數的字典，格式為：
            {
                'categories': {
                    'category_name': {
                        'name': str,
                        'score': float,
                        'metrics': {
                            'metric_name': {
                                'score': float,
                                'weight': float,
                                'details': Any
                            }
                        }
                    }
                },
                'overall_score': float
            }
        """
        results = {
            'categories': {},
            'overall_score': 0.0
        }
        
        # 計算各項指標
        for category_name, category in self.config.categories.items():
            if not category.enabled or category_name == "stability":
                continue  # 穩定性指標在 evaluate_stability 中單獨處理
                
            category_result = {
                'name': category.name,
                'score': 0.0,
                'metrics': {}
            }
            
            total_weight = 0.0
            weighted_sum = 0.0
            
            for metric_name, metric_config in category.metrics.items():
                if not metric_config.enabled:
                    continue
                    
                if metric_name in self.metric_calculators:
                    try:
                        score, details = self.metric_calculators[metric_name](reference, candidate)
                        category_result['metrics'][metric_name] = {
                            'score': score,
                            'weight': metric_config.weight,
                            'details': details
                        }
                        weighted_sum += score * metric_config.weight
                        total_weight += metric_config.weight
                    except Exception as e:
                        print(f"計算指標 {metric_name} 時出錯: {str(e)}")
                        category_result['metrics'][metric_name] = {
                            'score': 0.0,
                            'weight': metric_config.weight,
                            'details': {'error': str(e)}
                        }
            
            # 計算類別加權分數
            if total_weight > 0:
                category_result['score'] = weighted_sum / total_weight
            
            results['categories'][category_name] = category_result
        
        # 計算總分
        total_weight = sum(
            cat.weight 
            for cat in self.config.categories.values() 
            if cat.enabled and cat.name in results['categories']
        )
        
        if total_weight > 0:
            results['overall_score'] = sum(
                results['categories'][cat.name]['score'] * (cat.weight / total_weight)
                for cat in self.config.categories.values()
                if cat.enabled and cat.name in results['categories']
            )
        
        return results
        
    def evaluate_stability(self, texts: List[str]) -> Dict[str, float]:
        """
        評估一組文本的穩定性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            包含穩定性指標的字典
        """
        try:
            return self.stability_metrics.calculate_all_metrics(texts)
        except TypeError as e:
            logging.getLogger(__name__).error(f"evaluate_stability: 參數錯誤: {e}")
            return {"format_consistency": 0.0, "length_variation": 1.0, "key_entities_consistency": 0.0}
        except Exception as e:
            logging.getLogger(__name__).error(f"evaluate_stability: 未知錯誤: {e}")
            return {"format_consistency": 0.0, "length_variation": 1.0, "key_entities_consistency": 0.0}
    
    def evaluate_batch(self, references: Union[str, List[str]], candidates: List[str]) -> Dict[str, Any]:
        """
        批量評估候選文本
        
        Args:
            references: 參考文本或參考文本列表
            candidates: 候選文本列表
            
        Returns:
            包含評估結果的字典
        """
        # 如果參考文本是單個，則重複以匹配候選文本數量
        if isinstance(references, str):
            references = [references] * len(candidates)
            
        if len(references) != len(candidates):
            raise ValueError(f"參考文本數量({len(references)})與候選文本數量({len(candidates)})不匹配")
            
        # 評估每個候選的質量
        quality_results = []
        for ref, cand in zip(references, candidates):
            result = self.evaluate(ref, cand)
            quality_results.append(result)
        
        # 評估穩定性
        stability_results = self.evaluate_stability(candidates)
        
        # 計算平均質量分數
        avg_quality = np.mean([r.get("overall_score", 0) for r in quality_results]) if quality_results else 0.0
        
        # 計算穩定性分數（將變異係數轉換為穩定性分數）
        stability_score = (
            0.4 * stability_results.get("format_consistency", 0) +
            0.3 * (1 - min(stability_results.get("length_variation", 1), 1)) +  # 變異係數越小越好
            0.3 * stability_results.get("key_entities_consistency", 0)
        )
        
        # 合併結果
        return {
            "quality": quality_results,
            "stability": stability_results,
            "average_quality": avg_quality,
            "stability_score": stability_score,
            "overall_score": 0.7 * avg_quality + 0.3 * stability_score
        }
    
    # 以下是各個指標的具體實現
    def _calculate_bertscore(self, reference: str, candidate: str, max_retries: int = 2) -> Tuple[float, dict]:
        """計算 BERTScore
        
        Args:
            reference: 參考文本
            candidate: 待評估文本
            max_retries: 最大重試次數
            
        Returns:
            (分數, 詳細信息) 元組
        """
        from bert_score import score as bert_score
        import torch
        import time
        from pathlib import Path
        import os
        
        # 設置環境變數，指定緩存目錄
        cache_dir = Path.home() / '.cache' / 'bert_score'
        os.makedirs(cache_dir, exist_ok=True)
        os.environ['TRANSFORMERS_CACHE'] = str(cache_dir)
        
        # 檢查緩存中是否已有模型
        model_name = 'bert-base-chinese'
        model_path = cache_dir / 'models--bert-base-chinese'
        
        for attempt in range(max_retries + 1):
            try:
                # 設置較短的超時時間
                import socket
                socket.setdefaulttimeout(60)  # 60秒超時
                
                P, R, F1 = bert_score(
                    [candidate], 
                    [reference],
                    lang="zh",
                    model_type=model_name,
                    verbose=False,
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    batch_size=1  # 減少內存使用
                )
                
                return float(F1[0]), {
                    "precision": float(P[0]),
                    "recall": float(R[0]),
                    "f1": float(F1[0])
                }
                
            except (socket.timeout, ConnectionError) as e:
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5  # 指數退避
                    print(f"下載 BERT 模型超時，{wait_time}秒後重試 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"BERTScore 計算失敗: {str(e)}")
                    return 0.0, {"error": f"BERTScore 計算失敗: {str(e)}"}
                    
            except Exception as e:
                print(f"BERTScore 計算出錯: {str(e)}")
                return 0.0, {"error": str(e)}
        
        # 所有重試都失敗
        return 0.0, {"error": "達到最大重試次數，無法計算 BERTScore"}
    
    def _calculate_rouge(self, reference: str, candidate: str, rouge_type: str) -> Tuple[float, dict]:
        """計算 ROUGE 分數"""
        from rouge_score import rouge_scorer
        
        scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=True)
        scores = scorer.score(reference, candidate)
        
        score = scores[rouge_type]
        return score.fmeasure, {
            "precision": score.precision,
            "recall": score.recall,
            "fmeasure": score.fmeasure
        }
    
    def _calculate_heading_quality(self, reference: str, candidate: str) -> Tuple[float, dict]:
        def extract_headings(text: str) -> List[str]:
            import re
            return [line.strip() for line in text.split('\n') if re.match(r'^#+\s+', line)]
        
        ref_headings = extract_headings(reference)
        cand_headings = extract_headings(candidate)
        
        if not ref_headings and not cand_headings:
            return 1.0, {"message": "No headings found"}
        
        if not ref_headings or not cand_headings:
            return 0.0, {"message": "Missing headings in reference or candidate"}
        
        heading_count_similarity = 1 - abs(len(ref_headings) - len(cand_headings)) / max(len(ref_headings), 1)
        
        return heading_count_similarity, {
            "reference_headings": ref_headings,
            "candidate_headings": cand_headings,
            "similarity": heading_count_similarity
        }
    
    def _calculate_paragraph_structure(self, reference: str, candidate: str) -> Tuple[float, dict]:
        ref_paragraphs = [p for p in reference.split('\n\n') if p.strip()]
        cand_paragraphs = [p for p in candidate.split('\n\n') if p.strip()]
        
        if not ref_paragraphs and not cand_paragraphs:
            return 1.0, {"message": "No paragraphs found"}
        
        if not ref_paragraphs or not cand_paragraphs:
            return 0.0, {"message": "Missing paragraphs in reference or candidate"}
        
        para_count_similarity = 1 - abs(len(ref_paragraphs) - len(cand_paragraphs)) / max(len(ref_paragraphs), 1)
        
        return para_count_similarity, {
            "reference_paragraph_count": len(ref_paragraphs),
            "candidate_paragraph_count": len(cand_paragraphs),
            "similarity": para_count_similarity
        }
    
    def _calculate_list_usage(self, reference: str, candidate: str) -> Tuple[float, dict]:
        def count_lists(text: str) -> int:
            return sum(1 for line in text.split('\n') if line.strip().startswith(('-', '*', '•')))
        
        ref_list_count = count_lists(reference)
        cand_list_count = count_lists(candidate)
        
        if ref_list_count == 0 and cand_list_count == 0:
            return 1.0, {"message": "No lists found"}
        
        if ref_list_count == 0 or cand_list_count == 0:
            return 0.0, {"message": "Missing lists in reference or candidate"}
        
        list_usage_similarity = 1 - abs(ref_list_count - cand_list_count) / max(ref_list_count, 1)
        
        return list_usage_similarity, {
            "reference_list_count": ref_list_count,
            "candidate_list_count": cand_list_count,
            "similarity": list_usage_similarity
        }

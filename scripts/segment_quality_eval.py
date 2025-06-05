#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分段品質評估模組 - 自動化評估語意分段的品質
提供多維度品質指標和自動化檢查機制
"""

import os
import json
import logging
import re
import statistics
from typing import List, Dict, Tuple, Optional, Any, Union
from datetime import datetime
import requests

class SegmentQualityEvaluator:
    """分段品質評估器"""
    
    def __init__(self, 
                 model_name: str = "gemma3:12b",
                 ollama_url: str = "http://localhost:11434/api/generate"):
        """
        初始化品質評估器
        
        Args:
            model_name: Ollama 模型名稱
            ollama_url: Ollama API 端點
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.logger = self._setup_logger()
        
        # 品質評估標準
        self.quality_thresholds = {
            "excellent": 8.5,
            "good": 7.0,
            "acceptable": 5.5,
            "poor": 3.0
        }
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger(f"QualityEvaluator_{self.model_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _call_ollama(self, prompt: str, temperature: float = 0.2) -> str:
        """調用 Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=180)
            response.raise_for_status()
            
            result = response.json()
            return str(result.get("response", "")).strip()
            
        except Exception as e:
            self.logger.error(f"Ollama API 調用失敗: {e}")
            return ""
    
    def evaluate_segment_boundaries(self, segments: List[Dict]) -> Dict[str, float]:
        """
        評估分段邊界的合理性
        
        Args:
            segments: 分段結果列表
            
        Returns:
            邊界品質評估結果
        """
        boundary_scores = []
        
        for i in range(len(segments) - 1):
            current_segment = segments[i]["segment_text"]
            next_segment = segments[i + 1]["segment_text"]
            
            # 檢查分段邊界是否自然
            evaluation_prompt = f"""
請評估以下兩個相鄰文本段落的分段邊界是否合理：

段落A結尾：
...{current_segment[-200:]}

段落B開頭：
{next_segment[:200]}...

請從以下角度評分（0-10分）：
1. 語意切分是否自然
2. 是否在句子中間切斷
3. 主題轉換是否合理
4. 資訊是否有遺漏或重複

請以JSON格式回答：
{{
    "boundary_score": 分數,
    "is_natural_break": true/false,
    "issues": ["問題描述"],
    "suggestions": ["改進建議"]
}}
"""
            
            response = self._call_ollama(evaluation_prompt)
            
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    boundary_scores.append(result.get("boundary_score", 7.0))
                else:
                    boundary_scores.append(7.0)
            except:
                boundary_scores.append(7.0)
        
        if boundary_scores:
            return {
                "average_boundary_score": statistics.mean(boundary_scores),
                "min_boundary_score": min(boundary_scores),
                "boundary_count": len(boundary_scores),
                "poor_boundaries": len([s for s in boundary_scores if s < 5.0])
            }
        else:
            return {
                "average_boundary_score": 10.0,
                "min_boundary_score": 10.0,
                "boundary_count": 0,
                "poor_boundaries": 0
            }
    
    def evaluate_content_coverage(self, original_text: str, segments: List[Dict]) -> Dict[str, float]:
        """
        評估內容覆蓋完整性
        
        Args:
            original_text: 原始完整文本
            segments: 分段結果列表
            
        Returns:
            內容覆蓋評估結果
        """
        # 重組分段文本
        reconstructed_text = ""
        for segment in segments:
            reconstructed_text += segment["segment_text"] + "\n"
        
        # 計算基本統計
        original_length = len(original_text)
        reconstructed_length = len(reconstructed_text)
        coverage_ratio = reconstructed_length / original_length if original_length > 0 else 0
        
        # 使用AI評估內容完整性
        coverage_prompt = f"""
請比較原始文本和重組文本的內容完整性：

原始文本長度：{original_length} 字元
重組文本長度：{reconstructed_length} 字元

原始文本開頭：
{original_text[:500]}...

原始文本結尾：
...{original_text[-500:]}

重組文本開頭：
{reconstructed_text[:500]}...

重組文本結尾：
...{reconstructed_text[-500:]}

請評估：
1. 重要資訊是否遺漏
2. 是否有內容重複
3. 整體完整性如何

請以JSON格式回答：
{{
    "content_completeness": 分數0-10,
    "information_loss": 分數0-10（越低越好）,
    "redundancy_level": 分數0-10（越低越好）,
    "overall_coverage": 分數0-10
}}
"""
        
        response = self._call_ollama(coverage_prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                ai_result = json.loads(json_match.group())
            else:
                ai_result = {}
        except:
            ai_result = {}
        
        return {
            "length_coverage_ratio": coverage_ratio,
            "content_completeness": ai_result.get("content_completeness", 8.0),
            "information_loss": ai_result.get("information_loss", 2.0),
            "redundancy_level": ai_result.get("redundancy_level", 3.0),
            "overall_coverage": ai_result.get("overall_coverage", 8.0)
        }
    
    def evaluate_segment_balance(self, segments: List[Dict]) -> Dict[str, float]:
        """
        評估分段長度平衡性
        
        Args:
            segments: 分段結果列表
            
        Returns:
            長度平衡評估結果
        """
        lengths = [seg["metadata"]["length"] for seg in segments]
        
        if not lengths:
            return {"balance_score": 0.0}
        
        avg_length = statistics.mean(lengths)
        length_variance = statistics.variance(lengths) if len(lengths) > 1 else 0
        length_std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        
        # 計算變異係數
        cv = length_std / avg_length if avg_length > 0 else 0
        
        # 平衡性評分（變異係數越小越好）
        balance_score = max(0, 10 - cv * 20)
        
        return {
            "average_length": avg_length,
            "length_std": length_std,
            "coefficient_of_variation": cv,
            "balance_score": balance_score,
            "min_length": min(lengths),
            "max_length": max(lengths),
            "length_range": max(lengths) - min(lengths)
        }
    
    def detect_quality_issues(self, segments: List[Dict]) -> List[Dict]:
        """
        檢測品質問題
        
        Args:
            segments: 分段結果列表
            
        Returns:
            問題列表
        """
        issues = []
        
        for i, segment in enumerate(segments):
            segment_id = segment.get("segment_id", i + 1)
            analysis = segment.get("analysis", {})
            metadata = segment.get("metadata", {})
            text = segment.get("segment_text", "")
            
            # 如果沒有分析數據，跳過品質檢查
            if not analysis:
                continue
            
            # 檢查語意完整性
            semantic_score = analysis.get("semantic_completeness", 5.0)
            if semantic_score < self.quality_thresholds["acceptable"]:
                issues.append({
                    "segment_id": segment_id,
                    "issue_type": "語意不完整",
                    "severity": "high" if semantic_score < self.quality_thresholds["poor"] else "medium",
                    "score": semantic_score,
                    "description": "段落語意不夠完整，可能在關鍵位置切斷"
                })
            
            # 檢查長度異常
            if metadata["length"] < 100:
                issues.append({
                    "segment_id": segment_id,
                    "issue_type": "段落過短",
                    "severity": "medium",
                    "score": metadata["length"],
                    "description": f"段落長度僅 {metadata['length']} 字元，可能包含資訊不足"
                })
            elif metadata["length"] > 6000:
                issues.append({
                    "segment_id": segment_id,
                    "issue_type": "段落過長",
                    "severity": "medium",
                    "score": metadata["length"],
                    "description": f"段落長度達 {metadata['length']} 字元，可能需要進一步分段"
                })
            
            # 檢查主題一致性
            topic_score = analysis.get("topic_consistency", 5.0)
            if topic_score < self.quality_thresholds["acceptable"]:
                issues.append({
                    "segment_id": segment_id,
                    "issue_type": "主題不一致",
                    "severity": "medium" if topic_score < self.quality_thresholds["poor"] else "low",
                    "score": topic_score,
                    "description": "段落內容主題跳躍，缺乏一致性"
                })
            
            # 檢查開頭結尾
            if text.startswith(("，", "。", "、", "；", "：")) or text.endswith(("，", "、", "；", "：")):
                issues.append({
                    "segment_id": segment_id,
                    "issue_type": "分段邊界問題",
                    "severity": "low",
                    "score": 0,
                    "description": "段落開頭或結尾有標點符號問題"
                })
        
        return issues
    
    def generate_improvement_suggestions(self, 
                                       segments: List[Dict], 
                                       issues: List[Dict]) -> List[Dict]:
        """
        生成改進建議
        
        Args:
            segments: 分段結果列表
            issues: 檢測到的問題列表
            
        Returns:
            改進建議列表
        """
        suggestions = []
        
        # 按段落分組問題
        issues_by_segment: Dict[int, List[Dict[str, Any]]] = {}
        for issue in issues:
            seg_id = issue["segment_id"]
            if seg_id not in issues_by_segment:
                issues_by_segment[seg_id] = []
            issues_by_segment[seg_id].append(issue)
        
        # 為每個有問題的段落生成建議
        for seg_id, seg_issues in issues_by_segment.items():
            segment = next((s for s in segments if s["segment_id"] == seg_id), None)
            if not segment:
                continue
            
            # 分析問題類型
            issue_types = [issue["issue_type"] for issue in seg_issues]
            high_severity_count = len([i for i in seg_issues if i["severity"] == "high"])
            
            suggestion_prompt = f"""
段落 {seg_id} 存在以下品質問題：
{[f"{issue['issue_type']}: {issue['description']}" for issue in seg_issues]}

段落內容預覽：
{segment['segment_text'][:300]}...

請提供具體的改進建議：

請以JSON格式回答：
{{
    "priority": "high/medium/low",
    "action_type": "重新分段/邊界調整/內容整理/合併段落",
    "specific_suggestions": ["具體建議1", "具體建議2"],
    "expected_improvement": "預期改善效果"
}}
"""
            
            response = self._call_ollama(suggestion_prompt)
            
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    ai_suggestion = json.loads(json_match.group())
                    
                    suggestions.append({
                        "segment_id": seg_id,
                        "issues": seg_issues,
                        "priority": ai_suggestion.get("priority", "medium"),
                        "action_type": ai_suggestion.get("action_type", "內容整理"),
                        "suggestions": ai_suggestion.get("specific_suggestions", []),
                        "expected_improvement": ai_suggestion.get("expected_improvement", "提升品質")
                    })
            except:
                # 默認建議
                priority = "high" if high_severity_count > 0 else "medium"
                suggestions.append({
                    "segment_id": seg_id,
                    "issues": seg_issues,
                    "priority": priority,
                    "action_type": "重新檢查",
                    "suggestions": ["重新評估分段邊界", "檢查語意完整性"],
                    "expected_improvement": "改善分段品質"
                })
        
        return suggestions
    
    def evaluate_segments(self, 
                         segments: List[Dict], 
                         original_text: Optional[str] = None) -> Dict:
        """
        綜合評估分段品質
        
        Args:
            segments: 分段結果列表
            original_text: 原始完整文本（用於覆蓋分析）
            
        Returns:
            綜合評估結果
        """
        self.logger.info(f"開始評估 {len(segments)} 個分段的品質")
        
        # 收集各項評估指標
        evaluation_results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "segment_count": len(segments),
            "model_name": self.model_name
        }
        
        # 1. 個別段落品質評估
        segment_scores = []
        for segment in segments:
            if "analysis" in segment and "overall_score" in segment["analysis"]:
                segment_scores.append(segment["analysis"]["overall_score"])
        
        if segment_scores:
            evaluation_results["individual_quality"] = {
                "average_score": statistics.mean(segment_scores),
                "min_score": min(segment_scores),
                "max_score": max(segment_scores),
                "std_score": statistics.stdev(segment_scores) if len(segment_scores) > 1 else 0,
                "excellent_count": len([s for s in segment_scores if s >= self.quality_thresholds["excellent"]]),
                "good_count": len([s for s in segment_scores if s >= self.quality_thresholds["good"]]),
                "acceptable_count": len([s for s in segment_scores if s >= self.quality_thresholds["acceptable"]]),
                "poor_count": len([s for s in segment_scores if s < self.quality_thresholds["acceptable"]])
            }
        
        # 2. 分段邊界評估
        evaluation_results["boundary_quality"] = self.evaluate_segment_boundaries(segments)
        
        # 3. 長度平衡評估
        evaluation_results["balance_quality"] = self.evaluate_segment_balance(segments)
        
        # 4. 內容覆蓋評估（如果有原文）
        if original_text:
            evaluation_results["coverage_quality"] = self.evaluate_content_coverage(original_text, segments)
        
        # 5. 問題檢測
        issues = self.detect_quality_issues(segments)
        evaluation_results["issues"] = issues
        evaluation_results["issue_summary"] = {
            "total_issues": len(issues),
            "high_severity": len([i for i in issues if i["severity"] == "high"]),
            "medium_severity": len([i for i in issues if i["severity"] == "medium"]),
            "low_severity": len([i for i in issues if i["severity"] == "low"])
        }
        
        # 6. 改進建議
        suggestions = self.generate_improvement_suggestions(segments, issues)
        evaluation_results["improvement_suggestions"] = suggestions
        
        # 7. 綜合品質評分
        quality_components = []
        weights = {}
        
        if segment_scores:
            quality_components.append(statistics.mean(segment_scores))
            weights["individual"] = 0.4
        
        boundary_score = evaluation_results["boundary_quality"]["average_boundary_score"]
        quality_components.append(boundary_score)
        weights["boundary"] = 0.3
        
        balance_score = evaluation_results["balance_quality"]["balance_score"]
        quality_components.append(balance_score)
        weights["balance"] = 0.2
        
        if original_text:
            coverage_score = evaluation_results["coverage_quality"]["overall_coverage"]
            quality_components.append(coverage_score)
            weights["coverage"] = 0.1
        
        # 計算加權平均
        total_weight = sum(weights.values())
        if total_weight > 0:
            overall_score = sum(quality_components) / len(quality_components)
        else:
            overall_score = 7.0
        
        # 根據問題數量調整分數
        issue_penalty = min(2.0, len(issues) * 0.2)
        overall_score = max(0, overall_score - issue_penalty)
        
        evaluation_results["overall_quality"] = {
            "score": overall_score,
            "grade": self._get_quality_grade(overall_score),
            "is_acceptable": overall_score >= self.quality_thresholds["acceptable"],
            "components": quality_components,
            "weights": weights
        }
        
        self.logger.info(f"評估完成，綜合品質分數: {overall_score:.2f}/10")
        return evaluation_results
    
    def _get_quality_grade(self, score: float) -> str:
        """根據分數獲取品質等級"""
        if score >= self.quality_thresholds["excellent"]:
            return "優秀"
        elif score >= self.quality_thresholds["good"]:
            return "良好"
        elif score >= self.quality_thresholds["acceptable"]:
            return "可接受"
        else:
            return "需改進"
    
    def save_evaluation_report(self, evaluation_results: Dict, output_dir: str) -> str:
        """
        保存評估報告
        
        Args:
            evaluation_results: 評估結果
            output_dir: 輸出目錄
            
        Returns:
            報告文件路徑
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_evaluation_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"評估報告已保存至: {filepath}")
        return filepath

    def evaluate_semantic_coherence(self, segments: List[Dict]) -> Dict[str, Union[float, List[Dict[str, Any]]]]:
        """
        評估每個分段的語意連貫性
        使用 LLM 自動判斷段落語意是否完整、無斷裂
        
        Args:
            segments: 分段結果列表
            
        Returns:
            語意連貫性評估結果
        """
        coherence_scores = []
        problematic_segments = []
        
        for i, segment in enumerate(segments):
            segment_text = segment.get("segment_text", "")
            
            # 語意連貫性檢查提示詞
            coherence_prompt = f"""請判斷下列段落是否語意連貫且無明顯斷裂，回覆'是'或'否'並簡述原因。

評估標準：
1. 段落開頭是否自然，沒有突然開始
2. 段落結尾是否完整，沒有突然中斷
3. 內容是否形成完整的語意單元
4. 是否在句子中間或關鍵詞語中間切斷
5. 主題或討論點是否完整

段落內容：
'''
{segment_text}
'''

請以JSON格式回答：
{{
    "is_coherent": true/false,
    "coherence_score": 0-10分,
    "issues": ["具體問題描述"],
    "suggestions": ["改進建議"],
    "natural_start": true/false,
    "complete_ending": true/false,
    "topic_completeness": 0-10分
}}"""
            
            try:
                response = self._call_ollama(coherence_prompt)
                
                # 解析 JSON 回應
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    coherence_score = result.get("coherence_score", 5.0)
                    coherence_scores.append(coherence_score)
                    
                    # 記錄有問題的分段
                    if not result.get("is_coherent", True) or coherence_score < 6.0:
                        problematic_segments.append({
                            "segment_id": i + 1,
                            "coherence_score": coherence_score,
                            "issues": result.get("issues", []),
                            "suggestions": result.get("suggestions", []),
                            "natural_start": result.get("natural_start", True),
                            "complete_ending": result.get("complete_ending", True),
                            "topic_completeness": result.get("topic_completeness", 5.0)
                        })
                else:
                    # 如果無法解析，給予中等分數
                    coherence_scores.append(6.0)
                    
            except Exception as e:
                self.logger.warning(f"段落 {i+1} 語意連貫性評估失敗: {e}")
                coherence_scores.append(5.0)
        
        # 計算統計資料
        if coherence_scores:
            avg_coherence = statistics.mean(coherence_scores)
            min_coherence = min(coherence_scores)
            poor_segments_count = len([s for s in coherence_scores if s < 6.0])
            
            return {
                "average_coherence": avg_coherence,
                "min_coherence": min_coherence,
                "coherence_scores": coherence_scores,
                "problematic_segments": problematic_segments,
                "poor_segments_count": poor_segments_count,
                "coherence_pass_rate": (len(coherence_scores) - poor_segments_count) / len(coherence_scores) * 100
            }
        else:
            return {
                "average_coherence": 0.0,
                "min_coherence": 0.0,
                "coherence_scores": [],
                "problematic_segments": [],
                "poor_segments_count": 0,
                "coherence_pass_rate": 0.0
            }
    
    def batch_quality_check(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        批次品質檢查 - 對所有分段執行自動品質檢查
        
        Args:
            segments: 分段結果列表
            
        Returns:
            完整的品質檢查報告
        """
        self.logger.info(f"開始批次品質檢查，共 {len(segments)} 個分段")
        
        # 執行各項評估
        boundary_eval = self.evaluate_segment_boundaries(segments)
        balance_eval = self.evaluate_segment_balance(segments)
        coherence_eval = self.evaluate_semantic_coherence(segments)
        quality_issues = self.detect_quality_issues(segments)
        
        # 生成綜合報告
        report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "total_segments": len(segments),
            "boundary_evaluation": boundary_eval,
            "balance_evaluation": balance_eval,
            "coherence_evaluation": coherence_eval,
            "quality_issues": quality_issues,
            "summary": {
                "overall_quality": self._calculate_overall_quality(
                    boundary_eval, balance_eval, coherence_eval
                ),
                "needs_revision": len(quality_issues) > 0,
                "revision_suggestions": self._generate_revision_suggestions(
                    boundary_eval, balance_eval, coherence_eval, quality_issues
                )
            }
        }
        
        self.logger.info(f"品質檢查完成，整體品質分數: {report['summary']['overall_quality']:.2f}")
        
        return report
    
    def _calculate_overall_quality(self, boundary_eval: Dict[str, Any], balance_eval: Dict[str, Any], coherence_eval: Dict[str, Any]) -> float:
        """計算整體品質分數"""
        boundary_score = float(boundary_eval.get("average_boundary_score", 5.0))
        balance_score = float(balance_eval.get("balance_score", 5.0))
        coherence_score = float(coherence_eval.get("average_coherence", 5.0))
        
        # 加權平均（語意連貫性權重最高）
        weights = {"boundary": 0.3, "balance": 0.2, "coherence": 0.5}
        overall_score = (
            boundary_score * weights["boundary"] +
            balance_score * weights["balance"] +
            coherence_score * weights["coherence"]
        )
        
        return min(10.0, max(0.0, overall_score))
    
    def _generate_revision_suggestions(self, boundary_eval: Dict[str, Any], balance_eval: Dict[str, Any], 
                                     coherence_eval: Dict[str, Any], quality_issues: List[Dict[str, Any]]) -> List[str]:
        """生成修訂建議"""
        suggestions = []
        
        # 基於邊界評估的建議
        if boundary_eval.get("poor_boundaries", 0) > 0:
            suggestions.append("建議重新檢查分段邊界，確保在自然的語意切分點分段")
        
        # 基於平衡性評估的建議
        if balance_eval.get("balance_score", 10) < 6.0:
            suggestions.append("分段長度不夠平衡，建議調整分段策略以獲得更均勻的分段")
        
        # 基於語意連貫性的建議
        if coherence_eval.get("poor_segments_count", 0) > 0:
            suggestions.append(f"發現 {coherence_eval['poor_segments_count']} 個語意連貫性不佳的分段，建議重新分段")
        
        # 基於具體問題的建議
        for issue in quality_issues:
            if issue["issue_type"] == "段落過短":
                suggestions.append("考慮合併過短的段落以增加資訊密度")
            elif issue["issue_type"] == "段落過長":
                suggestions.append("考慮進一步細分過長的段落")
        
        return list(set(suggestions))  # 去重


def main() -> None:
    """測試品質評估功能"""
    # 示例分段數據
    sample_segments = [
        {
            "segment_id": 1,
            "segment_text": "會議開始時間為上午9點整，由張經理主持本次季度業務回顧會議。首先，張經理歡迎所有與會人員，並簡要介紹了會議議程。",
            "analysis": {
                "semantic_completeness": 8.5,
                "topic_consistency": 9.0,
                "logical_coherence": 8.0,
                "information_completeness": 8.5,
                "overall_score": 8.5
            },
            "metadata": {
                "start_pos": 0,
                "end_pos": 100,
                "length": 100,
                "is_optimized": False
            }
        },
        {
            "segment_id": 2,
            "segment_text": "第一項議題是第三季度銷售業績回顧。李副理報告指出，本季度總銷售額達到2,500萬元，較去年同期成長15%。",
            "analysis": {
                "semantic_completeness": 7.0,
                "topic_consistency": 8.5,
                "logical_coherence": 7.5,
                "information_completeness": 8.0,
                "overall_score": 7.8
            },
            "metadata": {
                "start_pos": 100,
                "end_pos": 180,
                "length": 80,
                "is_optimized": True
            }
        }
    ]
    
    # 初始化評估器
    evaluator = SegmentQualityEvaluator(model_name="gemma3:12b")
    
    # 執行評估
    evaluation_results = evaluator.evaluate_segments(sample_segments)
    
    # 顯示結果
    print(f"\n=== 分段品質評估結果 ===")
    print(f"綜合品質分數: {evaluation_results['overall_quality']['score']:.2f}/10")
    print(f"品質等級: {evaluation_results['overall_quality']['grade']}")
    print(f"是否可接受: {evaluation_results['overall_quality']['is_acceptable']}")
    
    if evaluation_results["issues"]:
        print(f"\n發現 {len(evaluation_results['issues'])} 個問題:")
        for issue in evaluation_results["issues"][:3]:  # 顯示前3個問題
            print(f"  - 段落{issue['segment_id']}: {issue['issue_type']} ({issue['severity']})")
    
    # 保存報告
    report_path = evaluator.save_evaluation_report(evaluation_results, "tmp_staging")
    print(f"\n評估報告已保存至: {report_path}")


if __name__ == "__main__":
    main()

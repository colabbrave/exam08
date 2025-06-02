#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
會議記錄優化與評估系統 - 核心優化引擎
依據 act.md 流程實現完整的疊代優化、評分、策略管理、early stopping
"""

import os
import json
import time
import logging
import argparse
import subprocess
from glob import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# 導入評估模組
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from evaluation import MeetingEvaluator, EvaluationConfig
    EVALUATOR_AVAILABLE = True
except ImportError:
    print("警告: 無法載入評估模組，將建立基本評估功能")
    EVALUATOR_AVAILABLE = False

@dataclass
class OptimizationResult:
    """優化結果資料結構"""
    iteration: int
    strategy_combination: List[str]
    minutes_content: str
    scores: Dict[str, float]
    execution_time: float
    timestamp: str
    model_used: str

@dataclass
class OptimizationConfig:
    """優化配置"""
    max_iterations: int = 5
    quality_threshold: float = 0.8
    min_improvement: float = 0.02
    strategy_max_count: int = 3
    model_name: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest"
    optimization_model: str = "gemma3:12b"
    enable_early_stopping: bool = True
    save_all_iterations: bool = True

class MeetingOptimizer:
    """會議記錄優化器 - 實現完整的疊代優化流程"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.strategies = self._load_strategies()
        self.logger = self._setup_logger()
        self.results_history: List[OptimizationResult] = []
        
        # 初始化評估器
        if EVALUATOR_AVAILABLE:
            eval_config = EvaluationConfig()
            self.evaluator = MeetingEvaluator(eval_config)
        else:
            self.evaluator = None
            
    def _setup_logger(self) -> logging.Logger:
        """設置日誌"""
        logger = logging.getLogger('MeetingOptimizer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_strategies(self) -> Dict[str, Any]:
        """載入優化策略"""
        strategy_path = "config/improvement_strategies.json"
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"載入策略失敗: {e}")
            return {}
    
    def _find_reference(self, transcript_name: str) -> Optional[str]:
        """尋找對應的參考會議記錄"""
        reference_dir = "data/reference"
        
        # 嘗試多種命名模式
        patterns = [
            transcript_name.replace("逐字稿", "會議紀錄"),
            transcript_name.replace("逐字稿", "會議記錄"),
            transcript_name.replace("逐字稿", ""),
        ]
        
        for pattern in patterns:
            ref_files = glob(os.path.join(reference_dir, f"{pattern}*.txt"))
            if ref_files:
                with open(ref_files[0], "r", encoding="utf-8") as f:
                    return f.read()
        
        return None
    
    def _select_strategy_combination(self, iteration: int, history: List[OptimizationResult]) -> List[str]:
        """選擇策略組合，考慮衝突規則和維度平衡"""
        if iteration == 0:
            # 第一輪使用基本策略組合
            return ["A_role_definition_A1", "B_structure_B1", "C_summary_C1"]
        
        # 分析歷史表現，選擇最佳策略組合
        if history:
            best_result = max(history, key=lambda x: x.scores.get('overall_score', 0))
            
            # 基於最佳結果調整策略
            if iteration < 3:
                # 前期探索不同維度組合
                strategy_pools = self._get_strategy_pools_by_dimension()
                
                # 智能選擇策略，避免衝突
                selected = self._select_compatible_strategies(strategy_pools, iteration)
                
                return selected[:self.config.strategy_max_count]
            else:
                # 後期基於最佳結果進行微調
                base_strategies = best_result.strategy_combination.copy()
                # 隨機替換一個策略進行探索
                if len(base_strategies) > 0:
                    replace_idx = iteration % len(base_strategies)
                    dimension = self._get_strategy_dimension(base_strategies[replace_idx])
                    alternative_strategies = self._get_dimension_strategies(dimension)
                    if alternative_strategies:
                        alternative = alternative_strategies[iteration % len(alternative_strategies)]
                        if alternative != base_strategies[replace_idx]:
                            base_strategies[replace_idx] = alternative
                
                return base_strategies
        
        # 默認策略組合
        available_strategies = list(self.strategies.keys())
        return available_strategies[:min(self.config.strategy_max_count, len(available_strategies))]
    
    def _get_strategy_pools_by_dimension(self) -> Dict[str, List[str]]:
        """根據維度分組策略"""
        pools = {
            'role': [],
            'structure': [],
            'content': [],
            'format': [],
            'language': [],
            'quality': []
        }
        
        for strategy_id, strategy_data in self.strategies.items():
            dimension = strategy_data.get('dimension', '')
            if dimension == '角色':
                pools['role'].append(strategy_id)
            elif dimension == '結構':
                pools['structure'].append(strategy_id)
            elif dimension == '內容':
                pools['content'].append(strategy_id)
            elif dimension == '格式':
                pools['format'].append(strategy_id)
            elif dimension == '語言':
                pools['language'].append(strategy_id)
            elif dimension == '品質':
                pools['quality'].append(strategy_id)
        
        return pools
    
    def _select_compatible_strategies(self, strategy_pools: Dict[str, List[str]], iteration: int) -> List[str]:
        """選擇兼容的策略組合"""
        selected = []
        used_dimensions = set()
        
        # 優先從不同維度選擇策略
        dimension_order = ['role', 'structure', 'content', 'format', 'language', 'quality']
        
        for dim in dimension_order:
            if len(selected) >= self.config.strategy_max_count:
                break
                
            if dim in strategy_pools and strategy_pools[dim] and dim not in used_dimensions:
                # 選擇該維度的策略
                strategy_options = strategy_pools[dim]
                chosen_strategy = strategy_options[iteration % len(strategy_options)]
                
                # 檢查衝突
                if not self._has_conflict(chosen_strategy, selected):
                    selected.append(chosen_strategy)
                    used_dimensions.add(dim)
        
        return selected
    
    def _has_conflict(self, strategy_id: str, selected_strategies: List[str]) -> bool:
        """檢查策略是否與已選策略衝突"""
        strategy_data = self.strategies.get(strategy_id, {})
        conflicts = strategy_data.get('conflict_with', [])
        
        for selected_strategy in selected_strategies:
            if selected_strategy in conflicts:
                return True
                
        return False
    
    def _get_strategy_dimension(self, strategy_id: str) -> str:
        """獲取策略的維度"""
        strategy_data = self.strategies.get(strategy_id, {})
        return strategy_data.get('dimension', '')
    
    def _get_dimension_strategies(self, dimension: str) -> List[str]:
        """獲取指定維度的所有策略"""
        strategies = []
        for strategy_id, strategy_data in self.strategies.items():
            if strategy_data.get('dimension', '') == dimension:
                strategies.append(strategy_id)
        return strategies
    
    def _generate_improvement_prompt(self, history: List[OptimizationResult], reference: Optional[str] = None) -> str:
        """生成策略改進提示詞"""
        if not history:
            return ""
        
        latest_result = history[-1]
        
        prompt = f"""
# 會議記錄優化策略改進分析

## 當前結果分析
策略組合: {', '.join(latest_result.strategy_combination)}
評分結果: {json.dumps(latest_result.scores, indent=2, ensure_ascii=False)}

## 優化目標
請分析當前結果的優缺點，並建議改進策略：

1. 內容結構優化建議
2. 語言表達改進方向
3. 格式規範調整建議

## 產生的會議記錄
{latest_result.minutes_content[:1000]}...

請提供具體的改進建議，包括：
- 策略調整方向
- 提示詞優化建議
- 格式改進要點
"""
        
        if reference:
            prompt += f"""
## 參考標準
{reference[:500]}...

請對比參考標準，指出差距並提出改進建議。
"""
        
        return prompt
    
    def _get_strategy_improvements(self, history: List[OptimizationResult], reference: Optional[str] = None) -> Dict[str, Any]:
        """使用 LLM 獲取策略改進建議"""
        if not history:
            return {}
        
        prompt = self._generate_improvement_prompt(history, reference)
        
        try:
            result = subprocess.run(
                ["ollama", "run", self.config.optimization_model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                improvement_text = result.stdout.strip()
                self.logger.info("獲得策略改進建議")
                return {"suggestions": improvement_text}
            else:
                self.logger.warning(f"策略改進建議生成失敗: {result.stderr}")
                
        except Exception as e:
            self.logger.warning(f"獲取策略改進建議時出錯: {e}")
        
        return {}
    
    def _assemble_prompt(self, strategies: List[str], transcript: str, reference: Optional[str] = None, improvements: Optional[Dict] = None) -> str:
        """組裝優化提示詞，根據策略動態生成"""
        prompt_parts = []
        
        # 根據策略確定主要角色
        role_strategy = self._get_primary_role_strategy(strategies)
        if role_strategy:
            role_def = self.strategies[role_strategy]['components'].get('role_definition', 
                "你是一位專業的會議記錄專員，具備豐富的行政經驗。")
            prompt_parts.extend([
                "# 會議記錄優化任務\n\n",
                "## 角色定義\n",
                f"{role_def}\n\n"
            ])
        else:
            prompt_parts.extend([
                "# 會議記錄優化任務\n\n",
                "## 角色定義\n",
                "你是一位專業的會議記錄專員，具備豐富的行政經驗，擅長將口語化的會議逐字稿轉換為結構化、專業的會議記錄。\n\n"
            ])
        
        # 添加策略指引
        if strategies and self.strategies:
            prompt_parts.append("## 優化策略\n")
            for strategy_id in strategies:
                if strategy_id in self.strategies:
                    strategy = self.strategies[strategy_id]
                    dimension = strategy.get('dimension', '')
                    prompt_parts.append(f"### {dimension} - {strategy.get('name', strategy_id)}\n")
                    prompt_parts.append(f"{strategy.get('description', '')}\n")
                    
                    # 添加具體組件指引
                    components = strategy.get('components', {})
                    for key, value in components.items():
                        if key not in ['role_definition'] and isinstance(value, str):
                            prompt_parts.append(f"- **{key}**: {value}\n")
                        elif key == 'sections' and isinstance(value, list):
                            prompt_parts.append(f"- **必要章節**: {', '.join(value)}\n")
                    
                    prompt_parts.append("\n")
        
        # 添加改進建議
        if improvements and 'suggestions' in improvements:
            prompt_parts.extend([
                "## 特別改進建議\n",
                improvements['suggestions'],
                "\n\n"
            ])
        
        # 添加參考範例
        if reference:
            prompt_parts.extend([
                "## 參考範例\n",
                "以下是一份優質的會議記錄範例，請參考其格式和風格：\n",
                "```markdown\n",
                reference[:2000],  # 限制長度避免 token 過多
                "\n```\n\n"
            ])
        
        # 根據策略動態確定輸出格式
        format_requirements = self._generate_format_requirements(strategies)
        prompt_parts.extend([
            "## 輸出格式要求\n",
            format_requirements,
            "\n"
        ])
        
        # 添加逐字稿
        prompt_parts.extend([
            "## 會議逐字稿\n",
            "請根據以上策略和要求，將以下逐字稿轉換為專業的會議記錄：\n\n",
            "```\n",
            transcript,
            "\n```\n\n",
            "## 輸出\n",
            "請輸出完整的會議記錄（僅輸出會議記錄內容，不要包含其他說明）：\n"
        ])
        
        return "".join(prompt_parts)
    
    def _get_primary_role_strategy(self, strategies: List[str]) -> Optional[str]:
        """獲取主要角色策略"""
        for strategy_id in strategies:
            if strategy_id in self.strategies:
                if self.strategies[strategy_id].get('dimension') == '角色':
                    return strategy_id
        return None
    
    def _generate_format_requirements(self, strategies: List[str]) -> str:
        """根據策略生成格式要求"""
        requirements = []
        
        # 基本要求
        requirements.append("請輸出標準的 Markdown 格式會議記錄")
        
        # 根據結構策略確定章節要求
        structure_sections = None
        for strategy_id in strategies:
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
                if strategy.get('dimension') == '結構':
                    components = strategy.get('components', {})
                    if 'sections' in components:
                        structure_sections = components['sections']
                        break
        
        if structure_sections:
            requirements.append(f"必須包含以下章節：{', '.join(structure_sections)}")
        else:
            requirements.append("包含：會議標題、會議資訊、討論事項、決議事項、待辦事項")
        
        # 根據格式策略確定格式細節
        for strategy_id in strategies:
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
                if strategy.get('dimension') == '格式':
                    components = strategy.get('components', {})
                    if 'template' in components:
                        requirements.append("採用正式公文格式")
                    elif 'simple_format' in components:
                        requirements.append("採用簡潔實用的格式")
                    elif 'tabular' in components:
                        requirements.append("重要資訊請使用表格形式呈現")
                    elif 'timeline' in components:
                        requirements.append("採用時間軸形式記錄")
        
        # 根據語言策略確定語言風格
        for strategy_id in strategies:
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
                if strategy.get('dimension') == '語言':
                    components = strategy.get('components', {})
                    if 'formal_tone' in components:
                        requirements.append("使用正式、客觀的語調")
                    elif 'natural_tone' in components:
                        requirements.append("保持自然、親和的語調")
                    elif 'active_voice' in components:
                        requirements.append("優先使用主動語態")
        
        return "\n".join(f"- {req}" for req in requirements)
        
        # 添加待優化的逐字稿
        prompt_parts.extend([
            "## 待優化逐字稿\n",
            "請將以下會議逐字稿轉換為專業的會議記錄：\n",
            "```\n",
            transcript,
            "\n```\n\n",
            "請根據以上指引，輸出優化後的會議記錄。確保內容專業、結構清晰、格式統一。"
        ])
        
        return "".join(prompt_parts)
    
    def _generate_minutes(self, prompt: str) -> Tuple[str, float]:
        """使用 LLM 生成會議記錄"""
        try:
            start_time = time.time()
            result = subprocess.run(
                ["ollama", "run", self.config.model_name],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=600
            )
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                content = result.stdout.strip()
                if content:
                    return content, execution_time
            
            self.logger.error(f"模型生成失敗: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            self.logger.error("模型生成超時")
        except Exception as e:
            self.logger.error(f"模型生成出錯: {e}")
        
        return "", 0.0
    
    def _evaluate_minutes(self, minutes: str, reference: Optional[str] = None) -> Dict[str, float]:
        """評估會議記錄品質"""
        if self.evaluator and reference:
            try:
                batch_result = self.evaluator.evaluate_batch([reference], [minutes])
                if batch_result and 'quality' in batch_result and len(batch_result['quality']) > 0:
                    # 提取第一個評估結果並轉換為簡化的分數字典
                    quality_result = batch_result['quality'][0]
                    simplified_scores = {
                        'overall_score': quality_result.get('overall_score', 0.0),
                        'stability_score': batch_result.get('stability_score', 0.0)
                    }
                    
                    # 提取各類別分數
                    if 'categories' in quality_result:
                        for cat_name, cat_data in quality_result['categories'].items():
                            simplified_scores[f'{cat_name}_score'] = cat_data.get('score', 0.0)
                    
                    return simplified_scores
            except Exception as e:
                self.logger.warning(f"使用高級評估器失敗: {e}")
        
        # 基本評估邏輯
        scores = {}
        
        # 長度評估
        word_count = len(minutes.split())
        scores['length_score'] = min(word_count / 500, 1.0) if word_count > 0 else 0.0
        
        # 結構評估
        structure_score = 0.0
        required_sections = ['會議', '討論', '決議', '待辦']
        for section in required_sections:
            if section in minutes:
                structure_score += 0.25
        scores['structure_score'] = structure_score
        
        # 格式評估
        format_score = 0.0
        if '##' in minutes:  # 有標題
            format_score += 0.3
        if '- ' in minutes or '1.' in minutes:  # 有列表
            format_score += 0.3
        if '**' in minutes or '*' in minutes:  # 有強調
            format_score += 0.2
        if '```' in minutes or '`' in minutes:  # 有代碼格式
            format_score += 0.2
        scores['format_score'] = min(format_score, 1.0)
        
        # 內容豐富度評估
        unique_words = len(set(minutes.lower().split()))
        total_words = len(minutes.split())
        diversity_ratio = unique_words / total_words if total_words > 0 else 0
        scores['content_richness'] = min(diversity_ratio * 2, 1.0)
        
        # 專業度評估（關鍵詞檢查）
        professional_keywords = ['決議', '討論', '報告', '提案', '建議', '執行', '負責人', '期限']
        professional_count = sum(1 for keyword in professional_keywords if keyword in minutes)
        scores['professionalism'] = min(professional_count / len(professional_keywords), 1.0)
        
        # 計算總分
        scores['overall_score'] = sum(scores.values()) / len(scores)
        
        return scores
    
    def _should_stop_early(self, history: List[OptimizationResult]) -> Tuple[bool, str]:
        """判斷是否應該提前停止"""
        if not self.config.enable_early_stopping or len(history) < 2:
            return False, ""
        
        latest = history[-1]
        
        # 檢查是否達到品質閾值
        if latest.scores.get('overall_score', 0) >= self.config.quality_threshold:
            return True, f"達到品質閾值 {self.config.quality_threshold}"
        
        # 檢查是否連續無改善
        if len(history) >= 3:
            recent_scores = [r.scores.get('overall_score', 0) for r in history[-3:]]
            if all(abs(recent_scores[i] - recent_scores[i-1]) < self.config.min_improvement 
                   for i in range(1, len(recent_scores))):
                return True, "連續三輪無顯著改善"
        
        return False, ""
    
    def _save_iteration_result(self, result: OptimizationResult, transcript_name: str):
        """保存疊代結果"""
        if not self.config.save_all_iterations:
            return
        
        # 創建結果目錄
        results_dir = f"results/iterations/{transcript_name}"
        os.makedirs(results_dir, exist_ok=True)
        
        # 保存會議記錄
        minutes_file = os.path.join(results_dir, f"iteration_{result.iteration:02d}_minutes.md")
        with open(minutes_file, "w", encoding="utf-8") as f:
            f.write(result.minutes_content)
        
        # 保存評分結果
        scores_file = os.path.join(results_dir, f"iteration_{result.iteration:02d}_scores.json")
        with open(scores_file, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"保存第 {result.iteration + 1} 輪結果到 {results_dir}")
    
    def _save_final_results(self, best_result: OptimizationResult, transcript_name: str, history: List[OptimizationResult]):
        """保存最終結果"""
        # 創建最終結果目錄
        final_dir = "results/optimized"
        os.makedirs(final_dir, exist_ok=True)
        
        # 保存最佳會議記錄
        best_minutes_file = os.path.join(final_dir, f"{transcript_name}_best.md")
        with open(best_minutes_file, "w", encoding="utf-8") as f:
            f.write(best_result.minutes_content)
        
        # 保存評分報告
        report_file = os.path.join(final_dir, f"{transcript_name}_report.json")
        report = {
            "transcript_name": transcript_name,
            "optimization_summary": {
                "total_iterations": len(history),
                "best_iteration": best_result.iteration + 1,
                "best_scores": best_result.scores,
                "best_strategy_combination": best_result.strategy_combination,
                "total_time": sum(r.execution_time for r in history),
            },
            "iteration_history": [asdict(r) for r in history],
            "config": asdict(self.config)
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存優化歷史
        history_file = os.path.join(final_dir, f"{transcript_name}_history.json")
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in history], f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"最終結果保存到 {final_dir}")
        self.logger.info(f"最佳分數: {best_result.scores.get('overall_score', 0):.4f}")
        self.logger.info(f"最佳策略組合: {', '.join(best_result.strategy_combination)}")
    
    def optimize_transcript(self, transcript_path: str) -> OptimizationResult:
        """優化單個逐字稿 - 完整的疊代流程"""
        transcript_name = Path(transcript_path).stem
        self.logger.info(f"開始優化逐字稿: {transcript_name}")
        
        # 載入逐字稿
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        
        if not transcript.strip():
            raise ValueError(f"逐字稿檔案 {transcript_path} 是空的")
        
        # 尋找參考會議記錄
        reference = self._find_reference(transcript_name)
        if reference:
            self.logger.info("找到對應的參考會議記錄")
        else:
            self.logger.info("未找到對應的參考會議記錄，將使用無參考評估")
        
        history = []
        
        # 開始疊代優化
        for iteration in range(self.config.max_iterations):
            self.logger.info(f"第 {iteration + 1}/{self.config.max_iterations} 輪優化")
            
            # 選擇策略組合
            strategies = self._select_strategy_combination(iteration, history)
            self.logger.info(f"使用策略組合: {', '.join(strategies)}")
            
            # 獲取策略改進建議（從第二輪開始）
            improvements = self._get_strategy_improvements(history, reference) if iteration > 0 else None
            
            # 組裝提示詞
            prompt = self._assemble_prompt(strategies, transcript, reference, improvements)
            
            # 生成會議記錄
            self.logger.info("正在生成會議記錄...")
            minutes_content, exec_time = self._generate_minutes(prompt)
            
            if not minutes_content:
                self.logger.error(f"第 {iteration + 1} 輪生成失敗，跳過")
                continue
            
            # 評估結果
            self.logger.info("正在評估結果...")
            scores = self._evaluate_minutes(minutes_content, reference)
            
            # 創建結果記錄
            result = OptimizationResult(
                iteration=iteration,
                strategy_combination=strategies,
                minutes_content=minutes_content,
                scores=scores,
                execution_time=exec_time,
                timestamp=datetime.now().isoformat(),
                model_used=self.config.model_name
            )
            
            history.append(result)
            
            # 保存疊代結果
            self._save_iteration_result(result, transcript_name)
            
            # 輸出結果
            overall_score = scores.get('overall_score', 0)
            self.logger.info(f"第 {iteration + 1} 輪完成，總分: {overall_score:.4f}")
            
            # 檢查是否應該提前停止
            should_stop, reason = self._should_stop_early(history)
            if should_stop:
                self.logger.info(f"提前停止優化: {reason}")
                break
        
        # 選擇最佳結果
        best_result = max(history, key=lambda x: x.scores.get('overall_score', 0))
        self.logger.info(f"優化完成，共進行 {len(history)} 輪，最佳分數: {best_result.scores.get('overall_score', 0):.4f}")
        
        # 保存最終結果
        self._save_final_results(best_result, transcript_name, history)
        
        return best_result

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="會議記錄優化與評估系統")
    parser.add_argument("transcript_file", type=str, nargs='?', help="要優化的逐字稿檔案")
    parser.add_argument("--transcript-dir", type=str, default="data/transcript", 
                       help="逐字稿目錄")
    parser.add_argument("--max-iterations", type=int, default=5, 
                       help="最大疊代次數")
    parser.add_argument("--quality-threshold", type=float, default=0.8, 
                       help="品質閾值")
    parser.add_argument("--model", type=str, 
                       default="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                       help="生成模型")
    parser.add_argument("--optimization-model", type=str, default="gemma3:12b",
                       help="策略優化模型")
    parser.add_argument("--disable-early-stopping", action="store_true",
                       help="禁用提前停止")
    
    args = parser.parse_args()
    
    # 創建配置
    config = OptimizationConfig(
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
        model_name=args.model,
        optimization_model=args.optimization_model,
        enable_early_stopping=not args.disable_early_stopping
    )
    
    # 創建優化器
    optimizer = MeetingOptimizer(config)
    
    # 確定要處理的檔案
    if args.transcript_file:
        transcript_files = [args.transcript_file]
    else:
        transcript_files = glob(os.path.join(args.transcript_dir, "*.txt"))
    
    if not transcript_files:
        print(f"在 {args.transcript_dir} 中找不到逐字稿檔案")
        return
    
    # 處理每個逐字稿
    for transcript_file in transcript_files:
        try:
            optimizer.optimize_transcript(transcript_file)
        except Exception as e:
            print(f"處理 {transcript_file} 時發生錯誤: {e}")
            continue
    
    print("所有優化任務完成！")

if __name__ == "__main__":
    main()

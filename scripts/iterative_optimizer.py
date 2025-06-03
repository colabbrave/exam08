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
    patience: int = 3  # early stopping 耐心次數
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
        """選擇策略組合，考慮衝突規則和維度平衡，並整合 LLM 改進建議"""
        if iteration == 0:
            # 第一輪使用基本策略組合
            return ["A_role_definition_A1", "B_structure_B1", "C_summary_C1"]
        
        # 從第二輪開始整合 LLM 改進建議
        try:
            if len(history) > 0:
                # 獲取結構化改進建議
                meeting_record = history[-1].minutes_content if history else ""
                history_dict = {"iterations": [asdict(result) for result in history]}
                improvements = self._get_strategy_improvements(meeting_record, history_dict)
                
                if improvements and "structured_suggestions" in improvements:
                    return self._apply_improvement_suggestions(improvements["structured_suggestions"], history)
        except Exception as e:
            self.logger.warning(f"獲取改進建議失敗，使用默認策略選擇: {e}")
        
        # 降級為原有的策略選擇邏輯
        
        # 分析歷史表現，選擇最佳策略組合
        if history:
            best_result = max(history, key=lambda x: x.scores.get('overall_score', 0))
            current_score = history[-1].scores.get('overall_score', 0)
            
            # 基於最佳結果調整策略（原有邏輯）
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
    
    def _try_replace_weaker_strategy(self, new_strategy: str, current_strategies: List[str], history: List[OptimizationResult]) -> Optional[str]:
        """嘗試替換同維度的較弱策略"""
        try:
            # 確定新策略的維度
            new_dimension = self._get_strategy_dimension(new_strategy)
            if not new_dimension:
                return None
            
            # 查找同維度的現有策略
            same_dimension_strategies = []
            for strategy in current_strategies:
                if self._get_strategy_dimension(strategy) == new_dimension:
                    same_dimension_strategies.append(strategy)
            
            if not same_dimension_strategies:
                return None
            
            # 如果有多個同維度策略，選擇「較弱」的進行替換
            # 這裡簡化為選擇第一個同維度策略進行替换
            strategy_to_replace = same_dimension_strategies[0]
            
            # 執行替換
            index = current_strategies.index(strategy_to_replace)
            current_strategies[index] = new_strategy
            
            return strategy_to_replace
            
        except Exception as e:
            self.logger.warning(f"策略替換失敗: {e}")
            return None

    def _try_intelligent_strategy_replacement(self, new_strategy: str, current_strategies: List[str], history: List[OptimizationResult]) -> Optional[str]:
        """智能策略替換邏輯：優先同維度替換，其次考慮維度平衡"""
        try:
            # 首先嘗試同維度替換
            replaced = self._try_replace_weaker_strategy(new_strategy, current_strategies, history)
            if replaced:
                return replaced
            
            # 如果沒有同維度策略，考慮維度平衡替換
            new_dimension = self._get_strategy_dimension(new_strategy)
            if not new_dimension:
                return None
            
            # 分析當前策略的維度分布
            dimension_count = {}
            for strategy in current_strategies:
                dim = self._get_strategy_dimension(strategy)
                if dim:
                    dimension_count[dim] = dimension_count.get(dim, 0) + 1
            
            # 找出重複維度最多的策略進行替換
            max_count = max(dimension_count.values()) if dimension_count else 0
            if max_count > 1:
                # 找到重複最多的維度
                for dim, count in dimension_count.items():
                    if count == max_count and dim != new_dimension:
                        # 替換該維度的第一個策略
                        for strategy in current_strategies:
                            if self._get_strategy_dimension(strategy) == dim:
                                index = current_strategies.index(strategy)
                                current_strategies[index] = new_strategy
                                self.logger.info(f"維度平衡替換 ({dim} -> {new_dimension})")
                                return strategy
            
            # 如果沒有重複維度，考慮歷史表現替換策略
            if history and len(history) >= 2:
                # 分析哪個維度的策略效果較差（這裡簡化處理）
                # 替換第一個非關鍵維度的策略（保留角色和結構）
                critical_dimensions = ['角色', '結構']
                for strategy in current_strategies:
                    dim = self._get_strategy_dimension(strategy)
                    if dim not in critical_dimensions:
                        index = current_strategies.index(strategy)
                        current_strategies[index] = new_strategy
                        self.logger.info(f"表現優化替換 ({dim} -> {new_dimension})")
                        return strategy
            
            return None
            
        except Exception as e:
            self.logger.warning(f"智能策略替換失敗: {e}")
            return None
    
    def _get_strategy_dimension(self, strategy_id: str) -> Optional[str]:
        """獲取策略的維度"""
        if strategy_id.startswith('A_'):
            return '角色'
        elif strategy_id.startswith('B_'):
            return '結構'
        elif strategy_id.startswith('C_'):
            return '內容'
        elif strategy_id.startswith('D_'):
            return '格式'
        elif strategy_id.startswith('E_'):
            return '語言'
        elif strategy_id.startswith('F_'):
            return '品質'
        return None
    
    def _get_dimension_strategies(self, dimension: Optional[str]) -> List[str]:
        """根據維度獲取該維度的所有策略"""
        if not dimension:
            return []
        
        dimension_strategies = []
        for strategy_id, strategy_data in self.strategies.items():
            # 檢查策略數據中的維度字段
            strategy_dimension = strategy_data.get('dimension', '')
            
            # 如果策略數據中沒有維度字段，根據ID前綴判斷
            if not strategy_dimension:
                strategy_dimension = self._get_strategy_dimension(strategy_id)
            
            if strategy_dimension == dimension:
                dimension_strategies.append(strategy_id)
        
        return dimension_strategies
    
    def _generate_improvement_prompt(self, meeting_record: str, history: Dict, reference: Optional[str] = None) -> str:
        """生成結構化策略改進提示詞"""
        if not history or 'iterations' not in history:
            return ""
        
        iterations = history['iterations']
        if not iterations:
            return ""
            
        latest_result = iterations[-1]
        
        # 分析得分趨勢
        score_trend = ""
        if len(iterations) > 1:
            prev_score = iterations[-2].get('scores', {}).get('overall_score', 0)
            curr_score = latest_result.get('scores', {}).get('overall_score', 0)
            change = curr_score - prev_score
            score_trend = f"分數變化: {change:+.4f} ({prev_score:.4f} → {curr_score:.4f})"
        
        # 獲取可用策略列表
        available_strategies = self._get_available_strategies_by_dimension()
        
        # 獲取當前策略組合
        current_strategies = latest_result.get('strategy_combination', [])
        current_scores = latest_result.get('scores', {})
        
        prompt = f"""
# 會議記錄策略優化分析師

你是一位專業的提示詞優化專家，負責分析會議記錄生成結果並提供結構化的策略改進建議。

## 當前狀況分析
### 使用策略組合
{', '.join(current_strategies)}

### 評分詳情
{json.dumps(current_scores, indent=2, ensure_ascii=False)}

### 得分趨勢
{score_trend}

### 生成內容品質分析
{meeting_record[:800]}...

## 可用策略資源
{self._format_available_strategies(available_strategies)}

## 任務要求
請基於上述分析，以JSON格式輸出結構化的策略改進建議：

```json
{{
  "score_analysis": {{
    "weakest_metrics": ["指標1", "指標2"],
    "improvement_priority": "high|medium|low",
    "root_causes": ["問題原因1", "問題原因2"]
  }},
  "strategy_adjustments": {{
    "remove_strategies": ["需要移除的策略ID"],
    "add_strategies": ["建議新增的策略ID"],
    "dimension_focus": "角色|結構|內容|格式|語言|品質",
    "rationale": "調整理由說明"
  }},
  "specific_im
    "content_structure": "具體的內容結構改進建議",
    "language_style": "語言風格調整方向",
    "format_enhancement": "格式改進要點"
  }},
  "expected_impact": {{
    "target_metrics": ["預期改善的指標"],
    "expected_score_gain": 0.05
  }}
}}
```

請確保建議的策略ID存在於可用策略列表中，並避免策略衝突。
"""
        
        if reference:
            prompt += f"""
## 參考標準會議記錄
{reference[:500]}...

請對比參考標準，在建議中重點說明如何縮小差距。
"""
        
        return prompt
    
    def _get_strategy_improvements(self, meeting_record: str, history: Dict, reference: Optional[str] = None) -> Dict[str, Any]:
        """使用 LLM 獲取結構化策略改進建議"""
        if not history or 'iterations' not in history or not history['iterations']:
            return {}
        
        prompt = self._generate_improvement_prompt(meeting_record, history, reference)
        
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
                
                # 解析結構化建議
                parsed_suggestions = self._parse_improvement_suggestions(improvement_text)
                
                # 驗證建議的策略是否存在且兼容
                validated_suggestions = self._validate_strategy_suggestions(parsed_suggestions)
                
                return {
                    "structured_suggestions": validated_suggestions,
                    "raw_suggestions": improvement_text
                }
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
                    # 補充標準會議記錄要素
                    prompt_parts.append("\n### 標準會議記錄應具備要素\n")
                    prompt_parts.append("- 會議基本資訊（名稱、日期、地點、主持人、記錄人、出席/列席/缺席人員）\n")
                    prompt_parts.append("- 會議議程/流程\n")
                    prompt_parts.append("- 討論事項（摘要、發言重點、意見建議）\n")
                    prompt_parts.append("- 決議事項（內容、狀態、負責人、期限）\n")
                    prompt_parts.append("- 待辦事項/行動項目（指派、負責人、預定完成時間）\n")
                    prompt_parts.append("- 其他事項（臨時動議、補充說明）\n")
                    prompt_parts.append("- 附錄（相關文件、附件、參考資料）\n")
                    prompt_parts.append("- 結語（下次會議資訊、結束時間）\n")
                    prompt_parts.append("- 條列式、分段清楚，標題明確，關鍵資訊可用表格或清單，語氣正式客觀\n\n")
        
        # 添加結構化改進建議
        if improvements and 'structured_suggestions' in improvements:
            structured = improvements['structured_suggestions']
            if 'specific_improvements' in structured:
                improvements_section = structured['specific_improvements']
                prompt_parts.extend([
                    "## 特別改進重點\n",
                    f"**內容結構優化**: {improvements_section.get('content_structure', '維持現有結構')}\n",
                    f"**語言風格調整**: {improvements_section.get('language_style', '保持專業語氣')}\n", 
                    f"**格式強化要點**: {improvements_section.get('format_enhancement', '確保格式一致')}\n\n"
                ])
        elif improvements and 'suggestions' in improvements:
            # 向後兼容原有格式
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
        
        # 檢查是否連續無改善 (使用 patience 和 min_improvement)
        patience = self.config.patience
        # 需要至少 patience+1 次歷史記錄以比較差異
        if len(history) >= patience + 1:
            recent_scores = [r.scores.get('overall_score', 0) for r in history[-(patience+1):]]
            # 比較每輪分數差異
            if all(abs(recent_scores[i] - recent_scores[i-1]) < self.config.min_improvement for i in range(1, len(recent_scores))):
                return True, f"連續{patience}輪無顯著改善"
        
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
            improvements = None
            if iteration > 0 and history:
                try:
                    # 構建歷史数據用於改進建議
                    history_dict = {"iterations": [asdict(result) for result in history]}
                    improvements = self._get_strategy_improvements(transcript, history_dict, reference)
                    
                    if improvements and "structured_suggestions" in improvements:
                        self.logger.info("獲得結構化改進建議")
                except Exception as e:
                    self.logger.warning(f"獲取改進建議失敗: {e}")
                    improvements = None
            
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

    def optimize(self, meeting_record: str) -> Dict[str, Any]:
        """優化會議記錄文本並返回結果字典"""
        try:
            # 創建臨時文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(meeting_record)
                tmp_file_path = tmp_file.name
            
            # 使用現有的 optimize_transcript 方法
            result = self.optimize_transcript(tmp_file_path)
            
            # 清理臨時文件
            import os
            os.unlink(tmp_file_path)
            
            # 構建簡化的歷史結果
            history = {
                'iterations': [
                    {
                        'score': result.scores.get('overall_score', 0),
                        'strategies': result.strategy_combination,
                        'feedback': '優化完成',
                        'improvements': '已應用策略組合'
                    }
                ]
            }
            
            return {
                'final_score': result.scores.get('overall_score', 0),
                'improvement': 0.0,  # 單輪優化無法計算改進幅度
                'iterations': history['iterations']
            }
            
        except Exception as e:
            self.logger.error(f"優化過程發生錯誤: {e}")
            return {
                'final_score': 0.0,
                'improvement': 0.0,
                'iterations': []
            }
    
    def _get_available_strategies_by_dimension(self) -> Dict[str, List[Dict]]:
        """獲取按維度分組的可用策略"""
        dimensions = {
            '角色': [],
            '結構': [], 
            '內容': [],
            '格式': [],
            '語言': [],
            '品質': []
        }
        
        for strategy_id, strategy_data in self.strategies.items():
            dimension = strategy_data.get('dimension', '')
            if dimension in dimensions:
                dimensions[dimension].append({
                    'id': strategy_id,
                    'name': strategy_data.get('name', strategy_id),
                    'description': strategy_data.get('description', '')
                })
        
        return dimensions
    
    def _format_available_strategies(self, strategies_by_dimension: Dict[str, List[Dict]]) -> str:
        """格式化可用策略列表為文字描述"""
        formatted = []
        for dimension, strategies in strategies_by_dimension.items():
            if strategies:
                formatted.append(f"### {dimension}維度")
                for strategy in strategies:
                    formatted.append(f"- {strategy['id']}: {strategy['name']} - {strategy['description']}")
                formatted.append("")
        
        return "\n".join(formatted)
    
    def _parse_improvement_suggestions(self, improvement_text: str) -> Dict[str, Any]:
        """解析LLM返回的結構化改進建議"""
        try:
            # 嘗試提取JSON部分
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', improvement_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
                return parsed
            else:
                # 嘗試直接解析文本中的大括號範圍
                try:
                    start = improvement_text.find('{')
                    end = improvement_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_str = improvement_text[start:end+1]
                        parsed = json.loads(json_str)
                        return parsed
                    else:
                        raise ValueError("無法提取JSON區塊")
                except Exception as ex:
                    self.logger.warning(f"解析改進建議JSON失敗: {ex}")
                    return {}
        except Exception as e:
            self.logger.warning(f"解析改進建議失敗: {e}")
            return {}
    
    def _fallback_parse_improvements(self, text: str) -> Dict[str, Any]:
        """降級文本解析改進建議"""
        return {
            "strategy_adjustments": {
                "add_strategies": [],
                "remove_strategies": [],
                "dimension_focus": "品質",
                "rationale": text[:200]
            },
            "specific_improvements": {
                "content_structure": "需要改進內容結構",
                "language_style": "優化語言表達",
                "format_enhancement": "強化格式規範"
            }
        }
    
    def _validate_strategy_suggestions(self, suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """驗證並修正策略建議"""
        validated = suggestions.copy()
        
        if 'strategy_adjustments' in suggestions:
            adjustments = suggestions['strategy_adjustments']
            
            # 驗證新增策略是否存在
            if 'add_strategies' in adjustments:
                valid_add = []
                for strategy_id in adjustments['add_strategies']:
                    if strategy_id in self.strategies:
                        valid_add.append(strategy_id)
                    else:
                        self.logger.warning(f"建議的策略不存在: {strategy_id}")
                validated['strategy_adjustments']['add_strategies'] = valid_add
            
            # 驗證移除策略是否合理
            if 'remove_strategies' in adjustments:
                valid_remove = []
                for strategy_id in adjustments['remove_strategies']:
                    if strategy_id in self.strategies:
                        valid_remove.append(strategy_id)
                validated['strategy_adjustments']['remove_strategies'] = valid_remove
            
            # 檢查策略衝突
            if 'add_strategies' in validated['strategy_adjustments']:
                conflict_free_strategies = []
                for strategy_id in validated['strategy_adjustments']['add_strategies']:
                    if not self._has_strategy_conflicts(strategy_id, conflict_free_strategies):
                        conflict_free_strategies.append(strategy_id)
                    else:
                        self.logger.info(f"移除衝突策略: {strategy_id}")
                validated['strategy_adjustments']['add_strategies'] = conflict_free_strategies
        
        return validated
    
    def _has_strategy_conflicts(self, strategy_id: str, existing_strategies: List[str]) -> bool:
        """檢查策略是否與現有策略衝突"""
        if strategy_id not in self.strategies:
            return True
            
        strategy_data = self.strategies[strategy_id]
        conflicts = strategy_data.get('conflict_with', [])
        
        for existing in existing_strategies:
            if existing in conflicts:
                return True
                
        return False
    
    def _apply_improvement_suggestions(self, suggestions: Dict[str, Any], history: List[OptimizationResult]) -> List[str]:
        """應用結構化改進建議生成新的策略組合"""
        try:
            if not suggestions or 'strategy_adjustments' not in suggestions:
                return self._fallback_strategy_selection(history)
            
            adjustments = suggestions['strategy_adjustments']
            
            # 獲取當前最佳策略組合作為基礎
            if history:
                best_result = max(history, key=lambda x: x.scores.get('overall_score', 0))
                base_strategies = best_result.strategy_combination.copy()
            else:
                base_strategies = ["A_role_definition_A1", "B_structure_B1", "C_summary_C1"]
            
            # 應用移除建議
            if 'remove_strategies' in adjustments:
                for strategy_to_remove in adjustments['remove_strategies']:
                    if strategy_to_remove in base_strategies:
                        base_strategies.remove(strategy_to_remove)
                        self.logger.info(f"移除策略: {strategy_to_remove}")
            
            # 應用新增建議
            if 'add_strategies' in adjustments:
                for strategy_to_add in adjustments['add_strategies']:
                    if strategy_to_add not in base_strategies:
                        # 檢查是否與現有策略衝突
                        if not self._has_strategy_conflicts(strategy_to_add, base_strategies):
                            if len(base_strategies) < self.config.strategy_max_count:
                                # 直接新增
                                base_strategies.append(strategy_to_add)
                                self.logger.info(f"新增策略: {strategy_to_add}")
                            else:
                                # 如果已達上限，嘗試智能替換策略
                                replaced = self._try_intelligent_strategy_replacement(strategy_to_add, base_strategies, history)
                                if replaced:
                                    self.logger.info(f"智能替換策略: {replaced} -> {strategy_to_add}")
                                else:
                                    self.logger.info(f"無法新增策略(已達上限且無合適替換): {strategy_to_add}")
                        else:
                            self.logger.warning(f"策略衝突，跳過: {strategy_to_add}")
            
            # 確保策略數量符合限制
            if len(base_strategies) > self.config.strategy_max_count:
                base_strategies = base_strategies[:self.config.strategy_max_count]
            elif len(base_strategies) < 2:  # 至少保持2個策略
                # 補充基本策略
                basic_strategies = ["A_role_definition_A1", "B_structure_B1", "C_summary_C1"]
                for strategy in basic_strategies:
                    if strategy not in base_strategies and len(base_strategies) < self.config.strategy_max_count:
                        base_strategies.append(strategy)
            
            self.logger.info(f"應用改進建議後的策略組合: {base_strategies}")
            return base_strategies
            
        except Exception as e:
            self.logger.error(f"應用改進建議時出錯: {e}")
            return self._fallback_strategy_selection(history)
    
    def _fallback_strategy_selection(self, history: List[OptimizationResult]) -> List[str]:
        """降級策略選擇邏輯"""
        # 分析歷史表現，選擇最佳策略組合
        if history:
            best_result = max(history, key=lambda x: x.scores.get('overall_score', 0))
            current_score = history[-1].scores.get('overall_score', 0)
            iteration = len(history)
            
            # 基於最佳結果調整策略（原有邏輯）
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

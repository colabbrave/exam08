"""
收斂優化器模組

實現了基於收斂監控的提示詞優化流程，支援多階段漸進式優化。
"""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
import numpy as np
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationStage:
    """優化階段配置"""
    name: str
    target_weight: float
    priority_metrics: List[str]
    min_improvement: float = 0.01
    max_iterations: int = 5
    current_iteration: int = 0
    best_score: float = 0.0
    converged: bool = False
    metrics_history: List[Dict[str, float]] = field(default_factory=list)

    def update_metrics(self, metrics: Dict[str, float]):
        """更新指標歷史記錄"""
        self.metrics_history.append(metrics)
        
        # 計算階段分數（加權平均）
        stage_score = 0.0
        total_weight = 0.0
        
        for metric_name in self.priority_metrics:
            if metric_name in metrics:
                stage_score += metrics[metric_name]
                total_weight += 1.0
        
        if total_weight > 0:
            stage_score /= total_weight
            
            # 檢查是否找到更好的分數
            if stage_score > self.best_score + self.min_improvement:
                self.best_score = stage_score
                self.current_iteration = 0
            else:
                self.current_iteration += 1
                
            # 檢查是否收斂
            if self.current_iteration >= self.max_iterations:
                self.converged = True
                
        return stage_score

class ConvergenceMonitor:
    """收斂監控器"""
    
    def __init__(self, min_improvement: float = 0.01, patience: int = 3):
        """
        初始化收斂監控器
        
        Args:
            min_improvement: 最小改善閾值
            patience: 允許的無改善迭代次數
        """
        self.min_improvement = min_improvement
        self.patience = patience
        self.best_score = -float('inf')
        self.no_improvement_epochs = 0
        self.converged = False
    
    def update(self, score: float) -> bool:
        """
        更新監控器狀態
        
        Args:
            score: 當前評估分數
            
        Returns:
            bool: 是否達到收斂條件
        """
        improvement = score - self.best_score
        
        if improvement > self.min_improvement:
            self.best_score = score
            self.no_improvement_epochs = 0
            logger.info(f"找到更好的分數: {score:.4f} (改善: {improvement:.4f})")
        else:
            self.no_improvement_epochs += 1
            logger.info(f"未達改善閾值 ({improvement:.4f} < {self.min_improvement})")
        
        self.converged = self.no_improvement_epochs >= self.patience
        return self.converged

class ProgressiveOptimizer:
    """漸進式優化器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化漸進式優化器
        
        Args:
            config_path: 配置檔案路徑
        """
        self.stages = self._load_stages(config_path)
        self.current_stage_idx = 0
        self.convergence_monitor = ConvergenceMonitor()
        self.history = []
        
    def _load_stages(self, config_path: Optional[str] = None) -> List[OptimizationStage]:
        """載入優化階段配置"""
        default_stages = [
            OptimizationStage(
                name="format",
                target_weight=0.4,
                priority_metrics=["format_score", "completeness"],
                min_improvement=0.01,
                max_iterations=5
            ),
            OptimizationStage(
                name="content",
                target_weight=0.3,
                priority_metrics=["accuracy", "relevance"],
                min_improvement=0.01,
                max_iterations=5
            ),
            OptimizationStage(
                name="style",
                target_weight=0.3,
                priority_metrics=["readability", "tone"],
                min_improvement=0.01,
                max_iterations=5
            )
        ]
        
        if not config_path or not os.path.exists(config_path):
            logger.warning(f"未找到配置檔案 {config_path}，使用預設階段配置")
            return default_stages
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return [
                OptimizationStage(**stage_config) 
                for stage_config in config.get('stages', default_stages)
            ]
        except Exception as e:
            logger.error(f"載入階段配置失敗: {e}，使用預設配置")
            return default_stages
    
    def get_current_stage(self) -> Optional[OptimizationStage]:
        """取得當前優化階段"""
        if self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx]
        return None
    
    def next_stage(self) -> bool:
        """移動到下一個優化階段"""
        if self.current_stage_idx < len(self.stages) - 1:
            self.current_stage_idx += 1
            if current_stage := self.get_current_stage():
                self.convergence_monitor = ConvergenceMonitor(
                    min_improvement=current_stage.min_improvement
                )
            return True
        return False
    
    def is_complete(self) -> bool:
        """檢查是否所有階段都已完成"""
        return all(stage.converged for stage in self.stages)
    
    def save_progress(self, output_dir: str = "optimization_progress"):
        """保存優化進度"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存階段狀態
        stage_states = [asdict(stage) for stage in self.stages]
        
        progress_data = {
            'current_stage': self.current_stage_idx,
            'stages': stage_states,
            'history': self.history,
            'timestamp': timestamp
        }
        
        output_path = os.path.join(output_dir, f"optimization_progress_{timestamp}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存優化進度至 {output_path}")
        return output_path

class PromptOptimizer:
    """提示詞優化器"""
    
    def __init__(self, base_prompt: str, evaluator: Any):
        """
        初始化提示詞優化器
        
        Args:
            base_prompt: 基礎提示詞
            evaluator: 評估器實例
        """
        self.base_prompt = base_prompt
        self.evaluator = evaluator
        self.optimizer = ProgressiveOptimizer()
        self.current_prompt = base_prompt
        self.best_prompt = base_prompt
        self.best_score = -float('inf')
    
    def optimize(self, input_text: str, reference: str, max_iterations: int = 10) -> Tuple[str, Dict]:
        """
        執行優化流程
        
        Args:
            input_text: 輸入文本
            reference: 參考文本
            max_iterations: 最大迭代次數
            
        Returns:
            Tuple[str, Dict]: 優化後的提示詞和評估結果
        """
        iteration = 0
        
        while not self.optimizer.is_complete() and iteration < max_iterations:
            current_stage = self.optimizer.get_current_stage()
            if not current_stage:
                break
                
            logger.info(f"\n=== 階段 {current_stage.name.upper()} (迭代 {current_stage.current_iteration + 1}/{current_stage.max_iterations}) ===")
            
            # 1. 生成候選提示詞變體
            candidate_prompts = self._generate_candidates(
                self.current_prompt,
                current_stage.priority_metrics
            )
            
            # 2. 評估候選提示詞
            best_candidate, best_metrics = self._evaluate_candidates(
                candidate_prompts,
                input_text,
                reference,
                current_stage.priority_metrics
            )
            
            # 3. 更新階段狀態
            stage_score = current_stage.update_metrics(best_metrics)
            
            # 4. 更新最佳提示詞
            if stage_score > self.best_score:
                self.best_score = stage_score
                self.best_prompt = best_candidate
                logger.info(f"找到更好的提示詞，分數: {self.best_score:.4f}")
            
            # 5. 檢查階段是否完成
            if current_stage.converged:
                logger.info(f"階段 {current_stage.name.upper()} 已收斂，最佳分數: {current_stage.best_score:.4f}")
                self.optimizer.next_stage()
            
            # 6. 保存進度
            self.optimizer.save_progress()
            
            iteration += 1
        
        return self.best_prompt, {"final_score": self.best_score, "iterations": iteration}
    
    def _generate_candidates(self, prompt: str, priority_metrics: List[str]) -> List[str]:
        """生成候選提示詞變體"""
        # 這裡可以實現多種提示詞變體生成策略
        candidates = [prompt]  # 至少包含當前提示詞
        
        # 根據優先指標生成變體
        if "format" in priority_metrics:
            candidates.append(self._modify_format(prompt))
        if "readability" in priority_metrics:
            candidates.append(self._improve_readability(prompt))
        if "completeness" in priority_metrics:
            candidates.append(self._enhance_completeness(prompt))
            
        return list(set(candidates))  # 去重
    
    def _evaluate_candidates(self, candidates: List[str], input_text: str, 
                           reference: str, priority_metrics: List[str]) -> Tuple[str, Dict]:
        """評估候選提示詞"""
        best_score = -1
        best_prompt = ""
        best_metrics = {}
        
        for candidate in candidates:
            try:
                # 使用候選提示詞生成結果
                generated_text = self._generate_with_prompt(candidate, input_text)
                
                # 評估生成結果
                metrics = self.evaluator.evaluate(reference, generated_text)
                
                # 計算加權分數（優先考慮當前階段的指標）
                score = 0.0
                total_weight = 0.0
                
                for metric_name in priority_metrics:
                    if metric_name in metrics.get('scores', {}):
                        score += metrics['scores'][metric_name]
                        total_weight += 1.0
                
                if total_weight > 0:
                    score /= total_weight
                    
                    if score > best_score:
                        best_score = score
                        best_prompt = candidate
                        best_metrics = metrics['scores']
                        
                        logger.debug(f"候選提示詞評分: {score:.4f}")
                        
            except Exception as e:
                logger.error(f"評估候選提示詞時出錯: {e}")
                continue
        
        return best_prompt, best_metrics
    
    def _generate_with_prompt(self, prompt: str, input_text: str) -> str:
        """使用給定提示詞生成文本"""
        # 這裡應該實現實際的模型調用邏輯
        # 目前僅返回示例文本
        return f"Generated text using prompt: {prompt[:50]}..."
    
    def _modify_format(self, prompt: str) -> str:
        """修改提示詞格式"""
        # 實現格式修改邏輯
        return f"# 格式優化版\n{prompt}"
    
    def _improve_readability(self, prompt: str) -> str:
        """提高可讀性"""
        # 實現可讀性改進邏輯
        return f"# 可讀性優化版\n{prompt}"
    
    def _enhance_completeness(self, prompt: str) -> str:
        """增強完整性"""
        # 實現完整性增強邏輯
        return f"# 完整性增強版\n{prompt}"

# 使用示例
if __name__ == "__main__":
    # 創建評估器實例
    from evaluation.evaluator import MeetingEvaluator
    
    evaluator = MeetingEvaluator()
    
    # 初始化優化器
    base_prompt = "請將以下會議記錄整理成結構化格式："
    optimizer = PromptOptimizer(base_prompt, evaluator)
    
    # 執行優化
    input_text = "今天我們討論了專案進度..."
    reference = "# 會議記錄\n## 主題：專案進度討論..."
    
    best_prompt, results = optimizer.optimize(input_text, reference)
    
    print(f"\n最佳提示詞：{best_prompt}")
    print(f"最終分數：{results['final_score']:.4f}")

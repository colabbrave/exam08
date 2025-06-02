"""
穩定性優化器

用於優化會議記錄生成的穩定性，實現自動化迭代優化循環。
整合多種穩定性評估指標，通過自動調整提示詞來提高生成結果的穩定性。
"""
import os
import sys
import json
import logging
import random
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime

# 添加專案根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from scripts.evaluation.evaluator import MeetingEvaluator
from scripts.evaluation.config import EvaluationConfig
from scripts.evaluation.stability_metrics import StabilityMetrics
from scripts.evaluation.taiwan_meeting_evaluator import TaiwanMeetingEvaluator

# 定義優化策略類型
OptimizationStrategy = Callable[[str, Dict[str, Any]], str]

@dataclass
class OptimizationResult:
    """優化結果數據類"""
    iteration: int
    template: str
    stability_score: float
    quality_score: float
    overall_score: float
    metrics: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "iteration": self.iteration,
            "stability_score": self.stability_score,
            "quality_score": self.quality_score,
            "overall_score": self.overall_score,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }

class StabilityOptimizer:
    """
    穩定性優化器類
    
    用於優化會議記錄生成的穩定性，通過調整模板和生成參數來提高生成結果的穩定性。
    實現自動化迭代優化循環，整合多種穩定性評估指標。
    """
    
    def __init__(
        self,
        model_name: str = "gemma3:12b",
        stability_threshold: float = 0.7,
        quality_threshold: float = 0.6,
        max_iterations: int = 10,
        batch_size: int = 3,
        warmup_iterations: int = 2,
        early_stopping_rounds: int = 3,
        min_improvement: float = 0.01,
        output_dir: str = "./optimized_results",
        generation_model: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
    ) -> None:
        """
        初始化穩定性優化器
        
        Args:
            model_name (str): 使用的模型名稱，默認使用 gemma3:12b
            stability_threshold (float): 穩定性閾值，達到此閾值後停止優化 (0-1)
            quality_threshold (float): 質量閾值，低於此值時觸發質量改進策略 (0-1)
            max_iterations (int): 最大迭代次數
            batch_size (int): 每批生成的樣本數，用於評估穩定性
            warmup_iterations (int): 預熱迭代次數，用於收集基準性能
            early_stopping_rounds (int): 早停輪數，當連續多輪無改進時停止
            min_improvement (float): 最小改進閾值，當改進小於此值時停止優化
            output_dir (str): 輸出目錄，用於保存優化結果和日誌
            generation_model (str): 生成模型名稱，默認使用 cwchang/llama3-taide-lx-8b-chat-alpha1:latest
        """
        self.model_name = model_name
        self.generation_model = generation_model
        self.output_dir = Path(output_dir)
        self.stability_threshold = stability_threshold
        self.quality_threshold = quality_threshold
        # 強制只跑 1 次迭代（debug/tracing 用）
        self.max_iterations = 1
        self.batch_size = batch_size
        self.warmup_iterations = warmup_iterations
        self.early_stopping_rounds = early_stopping_rounds
        self.min_improvement = min_improvement
        
        # 設置隨機種子
        random.seed(42)
        np.random.seed(42)
        
        # 創建輸出目錄
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir = self.output_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # 初始化評估器和穩定性指標
        self.evaluator = MeetingEvaluator()
        self.taiwan_evaluator = TaiwanMeetingEvaluator()
        self.stability_metrics = StabilityMetrics()
        
        # 優化歷史記錄
        self.optimization_history: List[OptimizationResult] = []
        self.best_result: Optional[OptimizationResult] = None
        
        # 設置日誌
        self._setup_logging()
        
        # 註冊優化策略
        self.strategies: List[OptimizationStrategy] = [
            self._strategy_improve_formatting,
            self._strategy_add_examples,
            self._strategy_simplify_language,
            self._strategy_add_constraints,
            self._strategy_enhance_structure,
            self._strategy_improve_quality
        ]
        
        self.logger.info(f"初始化穩定性優化器: model={model_name}, stability_threshold={stability_threshold}")
        self.logger.info(f"輸出目錄: {self.output_dir.absolute()}")
        
    def _generate_with_ollama(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        使用 Ollama 生成文本
        
        Args:
            prompt: 提示詞
            temperature: 溫度參數
            model: 使用的模型，如果為 None 則使用 self.model_name
            
        Returns:
            生成的文本
        """
        model = model or self.model_name
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_ctx": 4096
                    },
                },
                timeout=600,  # 增加超時時間
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            self.logger.error(f"生成文本時出錯 (模型: {model}): {str(e)}")
            return ""
    
    def _evaluate_stability(self, texts: List[str]) -> Dict[str, float]:
        """
        評估生成文本的穩定性
        
        Args:
            texts: 待評估的文本列表
            
        Returns:
            包含穩定性指標的字典
        """
        if len(texts) < 2:
            return {"overall_stability": 1.0}
            
        return self.stability_metrics.calculate_stability_score(texts)
    
    def _select_optimization_strategy(self, metrics: Dict[str, float]) -> OptimizationStrategy:
        """
        根據當前指標選擇最適合的優化策略
        
        Args:
            metrics: 當前評估指標
            
        Returns:
            選中的優化策略函數
        """
        # 提取會議特定指標
        meeting_metrics = {k.replace('meeting_', ''): v 
                         for k, v in metrics.items() 
                         if k.startswith('meeting_')}
        
        # 如果穩定性低於閾值，優先提升穩定性
        if metrics.get("stability_score", 0) < self.stability_threshold * 0.8:
            self.logger.info("穩定性低於閾值，優先提升結構穩定性")
            return self._strategy_enhance_structure
        
        # 如果質量低於閾值，優先提升質量
        if metrics.get("quality_score", 0) < self.quality_threshold * 0.8:
            # 根據具體問題選擇最適合的改進策略
            if meeting_metrics.get('has_meeting_info', 0) < 0.5 or meeting_metrics.get('has_agenda', 0) < 0.5:
                self.logger.info("會議基本信息或議程不完整，改進格式")
                return self._strategy_improve_formatting
                
            if meeting_metrics.get('has_decisions', 0) < 0.5 or meeting_metrics.get('has_action_items', 0) < 0.5:
                self.logger.info("決議事項或行動項目不完整，增強結構")
                return self._strategy_enhance_structure
                
            if meeting_metrics.get('has_owners', 0) < 0.5 or meeting_metrics.get('has_deadlines', 0) < 0.5:
                self.logger.info("行動項目缺少負責人或截止日期，添加約束")
                return self._strategy_add_constraints
                
            if meeting_metrics.get('structure_score', 0) < 0.7:
                self.logger.info("文檔結構需要改進，增強結構")
                return self._strategy_enhance_structure
                
            if meeting_metrics.get('clarity_score', 0) < 0.7:
                self.logger.info("語言清晰度需要提高，簡化語言")
                return self._strategy_simplify_language
                
            # 如果沒有具體問題，使用綜合質量改進策略
            return self._strategy_improve_quality
        
        # 如果特定指標低於閾值，優先改進這些指標
        if meeting_metrics.get('has_meeting_info', 0) < 0.5 or meeting_metrics.get('has_agenda', 0) < 0.5:
            self.logger.info("會議基本信息或議程不完整，改進格式")
            return self._strategy_improve_formatting
            
        if meeting_metrics.get('has_decisions', 0) < 0.5 or meeting_metrics.get('has_action_items', 0) < 0.5:
            self.logger.info("決議事項或行動項目不完整，增強結構")
            return self._strategy_enhance_structure
            
        if meeting_metrics.get('has_owners', 0) < 0.5 or meeting_metrics.get('has_deadlines', 0) < 0.5:
            self.logger.info("行動項目缺少負責人或截止日期，添加約束")
            return self._strategy_add_constraints
        
        # 如果結構或清晰度不足，選擇相應策略
        if meeting_metrics.get('structure_score', 0) < 0.7:
            self.logger.info("文檔結構需要改進，增強結構")
            return self._strategy_enhance_structure
            
        if meeting_metrics.get('clarity_score', 0) < 0.7:
            self.logger.info("語言清晰度需要提高，簡化語言")
            return self._strategy_simplify_language
        
        # 如果所有指標都良好，但仍有改進空間，隨機選擇一個策略
        self.logger.info("所有指標良好，隨機選擇優化策略")
        return random.choice(self.strategies)
    
    # 各種優化策略實現...
    def _strategy_improve_formatting(self, template: str, metrics: Dict[str, Any]) -> str:
        """改進格式化的策略"""
        prompt = f"""你是一個專業的提示詞工程師。請改進以下會議記錄模板的格式，使其更加結構化和易讀。
        請確保包含以下部分：
        1. 會議基本資訊（時間、地點、參與者）
        2. 議程項目
        3. 討論要點
        4. 決議事項
        5. 行動項目（負責人、截止日期）
        
        當前模板：
        {template}
        
        請輸出改進後的模板，保持簡潔明瞭。"""
        
        return self._generate_with_ollama(prompt, temperature=0.3)
    
    def _strategy_add_examples(self, template: str, metrics: Dict[str, Any]) -> str:
        """添加示例的策略"""
        prompt = f"""你是一個專業的提示詞工程師。請為以下會議記錄模板添加具體的示例，
        以幫助模型更好地理解預期的輸出格式和內容。
        
        當前模板：
        {template}
        
        請在適當的位置添加2-3個具體的示例，並用<example>和</example>標記。"""
        
        return self._generate_with_ollama(prompt, temperature=0.4)
    
    def _strategy_simplify_language(self, template: str, metrics: Dict[str, Any]) -> str:
        """簡化語言的策略"""
        prompt = f"""你是一個專業的提示詞工程師。請簡化以下會議記錄模板的語言，
        使其更加簡潔明瞭，同時保持所有關鍵信息。
        
        當前模板：
        {template}
        
        請輸出簡化後的模板。"""
        
        return self._generate_with_ollama(prompt, temperature=0.2)
    
    def _strategy_add_constraints(self, template: str, metrics: Dict[str, Any]) -> str:
        """添加約束條件的策略"""
        prompt = f"""你是一個專業的提示詞工程師。請為以下會議記錄模板添加必要的約束條件，
        以確保生成的內容符合要求。考慮以下方面：
        - 長度限制
        - 格式要求
        - 必須包含的關鍵要素
        - 風格指南
        
        當前模板：
        {template}
        
        請輸出添加了約束條件後的模板。"""
        
        return self._generate_with_ollama(prompt, temperature=0.3)
    
    def _strategy_enhance_structure(self, template: str, metrics: Dict[str, Any]) -> str:
        """增強結構的策略"""
        prompt = f"""你是一個專業的提示詞工程師。請增強以下會議記錄模板的結構，
        確保它具有良好的層次結構和邏輯流。考慮：
        1. 使用清晰的標題和副標題
        2. 適當的段落劃分
        3. 列表和項目符號的使用
        4. 一致的格式
        
        當前模板：
        {template}
        
        請輸出結構增強後的模板。"""
        return self._generate_with_ollama(prompt, temperature=0.3)
        
    def _strategy_improve_quality(self, template: str, metrics: Dict[str, Any]) -> str:
        """
        改進模板質量的策略
        
        Args:
            template: 當前模板
            metrics: 當前評估指標
            
        Returns:
            改進後的模板
        """
        # 分析會議特定指標
        meeting_metrics = {k.replace('meeting_', ''): v 
                         for k, v in metrics.items() 
                         if k.startswith('meeting_')}
        
        self.logger.info("開始分析會議記錄模板質量...")
        
        # 根據具體問題提供改進建議
        suggestions = []
        
        # 會議基本信息
        if meeting_metrics.get('has_meeting_info', 0) < 0.5:
            suggestions.append("在模板開頭添加會議基本信息，包括：\n  - 會議標題\n  - 日期和時間\n  - 地點（或線上會議連結）\n  - 主持人\n  - 與會者名單")
        
        # 議程相關
        if meeting_metrics.get('has_agenda', 0) < 0.5:
            suggestions.append("添加會議議程部分，列出：\n  - 討論主題\n  - 每個主題的預計時間\n  - 負責人或報告人")
        
        # 決议事项
        if meeting_metrics.get('has_decisions', 0) < 0.5:
            suggestions.append("添加'決議事項'部分，明確記錄：\n  - 每項決議的具體內容\n  - 表決結果（如適用）\n  - 相關背景或討論要點")
        
        # 行動項目
        action_items_suggestion = []
        if meeting_metrics.get('has_action_items', 0) < 0.5:
            action_items_suggestion.append("添加具體的行動項目")
        if meeting_metrics.get('has_owners', 0) < 0.5:
            action_items_suggestion.append("為每個行動項目指定明確的負責人")
        if meeting_metrics.get('has_deadlines', 0) < 0.5:
            action_items_suggestion.append("為每個行動項目設定具體的截止日期")
        
        if action_items_suggestion:
            suggestions.append("改進行動項目部分：\n  - " + 
                            "\n  - ".join(action_items_suggestion))
        
        # 文檔結構
        if meeting_metrics.get('structure_score', 0) < 0.7:
            suggestions.append("改進文檔結構：\n"
                            "  - 使用清晰的標題層級\n"
                            "  - 確保內容邏輯連貫\n"
                            "  - 使用項目符號或編號列表提高可讀性\n"
                            "  - 確保各部分之間的過渡自然")
        
        # 語言清晰度
        if meeting_metrics.get('clarity_score', 0) < 0.7:
            suggestions.append("提高語言清晰度：\n"
                            "  - 使用簡潔明瞭的語言\n"
                            "  - 避免使用模糊或主觀的表述\n"
                            "  - 使用主動語態\n"
                            "  - 確保專業術語使用一致")
        
        # 記錄改進建議
        self.logger.info(f"生成 {len(suggestions)} 條改進建議")
        if suggestions:
            self.logger.debug(f"具體改進建議：{suggestions}")
        else:
            self.logger.info("沒有發現具體的改進建議，將進行一般性質量改進")
        
        # 構建提示詞
        if suggestions:
            prompt = f"""# 會議記錄模板改進指南

你是一個專業的會議記錄專家，請根據以下具體建議改進會議記錄模板。請確保：
1. 保持專業、正式的語氣
2. 確保所有必填欄位都有明確的佔位符（如[會議標題]、[日期]等）
3. 使用清晰的層級結構
4. 確保所有行動項目都有明確的負責人和截止日期

## 需要改進的方面：
{chr(10).join(['- ' + s for s in suggestions])}

## 當前模板：
```
{template}
```

## 請直接輸出改進後的模板，不要添加額外的解釋或標記。
請確保改進後的模板：
1. 包含所有必要的會議元素
2. 結構清晰，易於閱讀
3. 使用一致的格式和風格
4. 包含明確的佔位符指導用戶輸入具體內容
5. 保持專業和正式的語氣
6. 確保行動項目具體、可執行、可追蹤"""
        else:
            # 如果沒有具體問題，嘗試一般性的質量改進
            prompt = f"""# 會議記錄模板優化

你是一個專業的會議記錄專家，請改進以下會議記錄模板的整體質量。改進時請注意：

## 改進重點：
1. 結構清晰，有明確的章節劃分
2. 語言簡潔明瞭，避免冗長
3. 包含所有必要的會議元素
4. 行動項目明確且可執行
5. 使用一致的格式和風格
6. 包含適當的佔位符（如[會議標題]、[日期]等）
7. 確保專業和正式的語氣
8. 優化可讀性和可維護性

## 當前模板：
```
{template}
```

## 請直接輸出改進後的模板，不要添加額外的解釋或標記。
請確保改進後的模板專業、完整、易於使用且符合最佳實踐。"""
        
        self.logger.info("正在生成改進後的模板...")
        self.logger.debug(f"提示詞長度：{len(prompt)} 字元")
        
        try:
            # 生成改進後的模板
            improved_template = self._generate_with_ollama(prompt, temperature=0.3)
            
            # 確保返回的內容是有效的模板
            if not improved_template or len(improved_template.strip()) < 10:  # 簡單的長度檢查
                self.logger.warning("生成的模板過短或為空，將使用原始模板")
                return template
            
            self.logger.info("模板改進完成")
            self.logger.debug(f"改進後的模板長度：{len(improved_template)} 字元")
            
            return improved_template.strip()
            
        except Exception as e:
            self.logger.error(f"生成改進模板時出錯: {str(e)}", exc_info=True)
            self.logger.warning("發生錯誤，將返回原始模板")
            return template  # 發生錯誤時返回原始模板
    
    def _setup_logging(self):
        """設置日誌記錄"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        
        log_file = log_dir / f"optimization_{self._get_timestamp()}.log"
        
        # 清除現有的日誌處理程序
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 配置日誌格式
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件處理程序
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(log_format)
        
        # 控制台處理程序
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        
        # 配置根日誌記錄器
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler],
            force=True
        )
        
        self.logger = logging.getLogger("StabilityOptimizer")
        self.logger.info(f"日誌已初始化，日誌文件: {log_file.absolute()}")
    
    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def optimize_template(
        self,
        template: str,
        reference_texts: List[str],
        max_iterations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        使用 Gemma 3 12B 模型優化模板
        
        Args:
            template: 初始模板
            reference_texts: 參考文本列表
            max_iterations: 最大迭代次數
            
        Returns:
            優化結果字典
        """
        self.logger.info("開始優化模板...")
        
        # 初始化最佳結果
        self.best_result = None
        
        # 設置最大迭代次數
        max_iter = max_iterations or self.max_iterations
        
        try:
            # 主優化循環
            for i in range(max_iter):
                self.logger.info(f"\n--- 迭代 {i+1}/{max_iter} ---")
                self.logger.info(f"本輪模板內容：\n{template}\n")
                # 生成候選結果
                self.logger.info("生成候選結果...")
                candidates = self._generate_candidates(template, reference_texts)
                if not candidates:
                    self.logger.warning("未生成候選結果，跳過本輪迭代")
                    continue
                # 評估穩定性
                self.logger.info("評估穩定性...")
                stability_metrics = self._evaluate_stability(candidates)
                # 評估質量（使用第一個參考文本）
                self.logger.info("評估質量...")
                quality_metrics = self._evaluate_quality(
                    candidates[0], 
                    reference_texts[0] if reference_texts else ""
                )
                # 新增：評估會議特有細項指標
                meeting_metrics = self._evaluate_meeting_specific_quality(candidates[0])
                # 合併所有 metrics
                metrics = {
                    "stability_score": stability_metrics.get("overall_stability", 0.0),
                    "quality_score": quality_metrics.get("combined_score", 0.0),
                }
                metrics.update(meeting_metrics)
                # log metrics 內容
                self.logger.info(f"本輪 metrics: {metrics}")
                # 計算總體分數
                stability_score = metrics["stability_score"]
                quality_score = metrics["quality_score"]
                overall_score = (stability_score * 0.6) + (quality_score * 0.4)
                self.logger.info(f"穩定性分數: {stability_score:.4f}, 質量分數: {quality_score:.4f}, 總體分數: {overall_score:.4f}")
                # 保存結果
                result = OptimizationResult(
                    iteration=i,
                    template=template,
                    stability_score=stability_score,
                    quality_score=quality_score,
                    overall_score=overall_score,
                    metrics=metrics
                )
                self.optimization_history.append(result)
                # 更新最佳結果
                if self.best_result is None or overall_score > self.best_result.overall_score:
                    self.best_result = result
                    self.logger.info(f"更新最佳結果，新分數: {overall_score:.4f}")
                # 檢查是否達到閾值
                if overall_score >= self.stability_threshold:
                    self.logger.info(f"達到穩定性閾值 {self.stability_threshold}，停止優化")
                    break
                    
                # 選擇並應用優化策略（傳入完整 metrics）
                strategy = self._select_optimization_strategy(metrics)
                self.logger.info(f"應用優化策略: {strategy.__name__}")
                new_template = strategy(template, metrics)
                if new_template and new_template != template:
                    template = new_template
                    self.logger.info("模板已更新")
                else:
                    self.logger.warning("模板未更新，可能達到局部最優")
                    break
                    
        except Exception as e:
            self.logger.error(f"優化過程中出錯: {str(e)}", exc_info=True)
            if self.best_result is None:
                raise RuntimeError(f"優化失敗: {str(e)}") from e
        
        if self.best_result is None:
            raise RuntimeError("未能生成有效的優化結果")
            
        self.logger.info(f"優化完成，最佳分數: {self.best_result.overall_score:.4f}")
        return self.best_result.to_dict()
        
    def _evaluate_meeting_specific_quality(self, text: str) -> Dict[str, float]:
        """
        評估會議記錄特有的質量指標
        
        Args:
            text: 要評估的文本
            
        Returns:
            包含會議特定評分的字典
        """
        # 初始化默認分數
        scores = {
            'has_meeting_info': 0.0,      # 是否包含會議基本信息
            'has_agenda': 0.0,            # 是否包含議程
            'has_decisions': 0.0,          # 是否包含決議事項
            'has_action_items': 0.0,       # 是否包含行動項目
            'has_owners': 0.0,             # 行動項目是否指定負責人
            'has_deadlines': 0.0,          # 行動項目是否包含截止日期
            'structure_score': 0.0,         # 結構完整性評分
            'clarity_score': 0.0           # 清晰度評分
        }
        
        # 檢查基本會議信息
        info_keywords = ['會議', '時間', '地點', '參與者', 'participants', 'meeting', 'time', 'location']
        if any(keyword in text.lower() for keyword in info_keywords):
            scores['has_meeting_info'] = 1.0
        
        # 檢查議程
        agenda_keywords = ['議程', 'agenda', '討論事項', 'topics']
        if any(keyword in text.lower() for keyword in agenda_keywords):
            scores['has_agenda'] = 1.0
        
        # 檢查決議事項
        decision_keywords = ['決議', '決定', '結論', 'decisions', 'conclusions']
        if any(keyword in text.lower() for keyword in decision_keywords):
            scores['has_decisions'] = 1.0
        
        # 檢查行動項目
        action_keywords = ['行動項目', '待辦事項', 'action items', 'todo', 'next steps']
        if any(keyword in text.lower() for keyword in action_keywords):
            scores['has_action_items'] = 1.0
            
            # 檢查行動項目是否包含負責人和截止日期
            owner_keywords = ['負責人', '負責', 'owner', 'assignee', 'assigned to']
            deadline_keywords = ['截止日期', 'due', 'by', 'deadline']
            
            if any(keyword in text.lower() for keyword in owner_keywords):
                scores['has_owners'] = 1.0
            if any(keyword in text.lower() for keyword in deadline_keywords):
                scores['has_deadlines'] = 1.0
        
        # 評估結構和清晰度
        section_headers = ['會議', '議程', '討論', '決議', '行動項目']
        header_count = sum(1 for header in section_headers if header in text)
        scores['structure_score'] = min(1.0, header_count / 3)  # 至少需要3個部分
        
        # 簡單的清晰度評估（基於句子長度和標點使用）
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            scores['clarity_score'] = min(1.0, 1.0 / (avg_sentence_length / 15))  # 15個詞為理想長度
        
        return scores
    
    def _evaluate_quality(self, generated: str, reference: str) -> Dict[str, float]:
        """
        使用多種指標評估生成文本的質量
        
        Args:
            generated: 生成的文本
            reference: 參考文本
            
        Returns:
            包含各項評分的字典
        """
        if not generated:
            self.logger.warning("生成文本為空")
            return {
                'rouge1': 0.0,
                'rouge2': 0.0,
                'rougeL': 0.0,
                'bert_score_precision': 0.0,
                'bert_score_recall': 0.0,
                'bert_score_f1': 0.0,
                'bleu': 0.0,
                'combined_score': 0.0,
                'taiwan_meeting_score': 0.0,
                'structure_score': 0.0,
                'taiwan_context_score': 0.0,
                'action_specificity_score': 0.0,
                'content_completeness_score': 0.0
            }
            
        try:
            self.logger.debug(f"評估質量 - 生成文本長度: {len(generated)}, 參考文本長度: {len(reference) if reference else 0}")
            
            # 初始化結果字典
            result = {}
            
            # 計算 ROUGE 分數
            try:
                rouge_scores = self._calculate_rouge(generated, reference)
                self.logger.debug(f"ROUGE 分數: {rouge_scores}")
                result.update({
                    "rouge1": max(0.0, min(1.0, rouge_scores.get("rouge1", 0))),
                    "rouge2": max(0.0, min(1.0, rouge_scores.get("rouge2", 0))),
                    "rougeL": max(0.0, min(1.0, rouge_scores.get("rougeL", 0)))
                })
            except Exception as e:
                self.logger.warning(f"計算 ROUGE 分數時出錯: {str(e)}")
                result.update({"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0})
            
            # 計算 BERTScore
            try:
                bert_scores = self._calculate_bert_score(generated, reference)
                self.logger.debug(f"BERTScore: {bert_scores}")
                result.update({
                    "bert_score_precision": max(0.0, min(1.0, bert_scores.get("precision", 0))),
                    "bert_score_recall": max(0.0, min(1.0, bert_scores.get("recall", 0))),
                    "bert_score_f1": max(0.0, min(1.0, bert_scores.get("f1", 0)))
                })
            except Exception as e:
                self.logger.warning(f"計算 BERTScore 時出錯: {str(e)}")
                result.update({"bert_score_precision": 0.0, "bert_score_recall": 0.0, "bert_score_f1": 0.0})
            
            # 計算 BLEU 分數
            try:
                bleu_score = self._calculate_bleu(generated, reference)
                self.logger.debug(f"BLEU 分數: {bleu_score}")
                result["bleu"] = max(0.0, min(1.0, bleu_score))
            except Exception as e:
                self.logger.warning(f"計算 BLEU 分數時出錯: {str(e)}")
                result["bleu"] = 0.0
                
            # 使用台灣會議記錄評估器進行評估
            try:
                self.logger.info("正在使用台灣會議記錄評估器進行評估...")
                taiwan_scores = self.taiwan_evaluator.evaluate(reference, generated)
                self.logger.debug(f"台灣會議記錄評估原始分數: {taiwan_scores}")
                
                # 提取主要分數，確保所有分數都在 0-1 範圍內
                taiwan_meeting_score = max(0.0, min(1.0, taiwan_scores.get('taiwan_meeting_score', 0.0)))
                structure_score = max(0.0, min(1.0, taiwan_scores.get('structure_score', 0.0)))
                taiwan_context_score = max(0.0, min(1.0, taiwan_scores.get('taiwan_context_score', 0.0)))
                action_specificity_score = max(0.0, min(1.0, taiwan_scores.get('action_specificity_score', 0.0)))
                
                # 計算內容完整性分數（基於其他分數的加權平均）
                content_completeness_score = max(0.0, min(1.0, (
                    structure_score * 0.4 +
                    taiwan_context_score * 0.3 +
                    action_specificity_score * 0.3
                )))
                
                # 更新結果
                result.update({
                    'taiwan_meeting_score': taiwan_meeting_score,
                    'structure_score': structure_score,
                    'taiwan_context_score': taiwan_context_score,
                    'action_specificity_score': action_specificity_score,
                    'content_completeness_score': content_completeness_score,
                    'detailed_scores': taiwan_scores
                })
                
                # 記錄詳細評估結果
                self.logger.info("台灣會議記錄評估結果:")
                self.logger.info(f"  綜合分數: {taiwan_meeting_score:.4f}")
                self.logger.info(f"  結構完整性: {structure_score:.4f}")
                self.logger.info(f"  台灣用語適配: {taiwan_context_score:.4f}")
                self.logger.info(f"  行動項目具體性: {action_specificity_score:.4f}")
                self.logger.info(f"  內容完整性: {content_completeness_score:.4f}")
                
                # 使用台灣會議記錄分數作為主要分數
                combined_score = taiwan_meeting_score
                
            except Exception as e:
                error_msg = f"使用台灣會議記錄評估器時出錯: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                combined_score = result.get('bert_score_f1', 0.0)
                result.update({
                    'taiwan_meeting_score': combined_score,
                    'structure_score': combined_score,
                    'taiwan_context_score': combined_score,
                    'action_specificity_score': combined_score,
                    'content_completeness_score': combined_score,
                    'error': error_msg
                })
            
            # 計算綜合分數
            result['combined_score'] = combined_score
            
            self.logger.debug(f"質量評估完成 - 綜合分數: {combined_score:.4f}")
            return result
            
        except Exception as e:
            self.logger.error(f"評估質量時出錯: {str(e)}", exc_info=True)
            return {
                'rouge1': 0.0,
                'rouge2': 0.0,
                'rougeL': 0.0,
                'bert_score_precision': 0.0,
                'bert_score_recall': 0.0,
                'bert_score_f1': 0.0,
                'bleu': 0.0,
                'combined_score': 0.0,
                'taiwan_meeting_score': 0.0,
                'structure_score': 0.0,
                'taiwan_context_score': 0.0,
                'action_specificity_score': 0.0,
                'content_completeness_score': 0.0,
                'error': str(e)
            }
            
        try:
            self.logger.debug(f"評估質量 - 生成文本長度: {len(generated)}, 參考文本長度: {len(reference)}")
            
            # 初始化結果字典
            result = {}
            
            # 計算 ROUGE 分數
            try:
                rouge_scores = self._calculate_rouge(generated, reference)
                self.logger.debug(f"ROUGE 分數: {rouge_scores}")
                result.update({
                    "rouge1": max(0.0, min(1.0, rouge_scores.get("rouge1", 0))),
                    "rouge2": max(0.0, min(1.0, rouge_scores.get("rouge2", 0))),
                    "rougeL": max(0.0, min(1.0, rouge_scores.get("rougeL", 0)))
                })
            except Exception as e:
                self.logger.warning(f"計算 ROUGE 分數時出錯: {str(e)}")
                result.update({"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0})
            
            # 計算 BERTScore
            try:
                bert_scores = self._calculate_bert_score(generated, reference)
                self.logger.debug(f"BERTScore: {bert_scores}")
                result.update({
                    "bert_score_precision": max(0.0, min(1.0, bert_scores.get("precision", 0))),
                    "bert_score_recall": max(0.0, min(1.0, bert_scores.get("recall", 0))),
                    "bert_score_f1": max(0.0, min(1.0, bert_scores.get("f1", 0)))
                })
            except Exception as e:
                self.logger.warning(f"計算 BERTScore 時出錯: {str(e)}")
                result.update({"bert_score_precision": 0.0, "bert_score_recall": 0.0, "bert_score_f1": 0.0})
            
            # 計算 BLEU 分數
            try:
                bleu_score = self._calculate_bleu(generated, reference)
                self.logger.debug(f"BLEU 分數: {bleu_score}")
                result["bleu"] = max(0.0, min(1.0, bleu_score))
            except Exception as e:
                self.logger.warning(f"計算 BLEU 分數時出錯: {str(e)}")
                result["bleu"] = 0.0
            
            # 使用 Gemma 3 12B 進行質量評估
            gemma_scores = {}
            try:
                gemma_eval_prompt = f"""
                請評估以下會議記錄的質量（1-5分，5分最高）：
                
                生成的會議記錄：
                {generated}
                
                參考會議記錄：
                {reference}
                
                請從以下幾個方面評分（1-5分）：
                1. 內容完整性
                2. 準確性
                3. 結構清晰度
                4. 語言流暢度
                5. 專業性
                
                請以 JSON 格式返回評分，例如：
                {{
                    "content_completeness": 4,
                    "accuracy": 5,
                    "structure_clarity": 4,
                    "language_fluency": 5,
                    "professionalism": 5
                }}
                """
                
                gemma_feedback = self._generate_with_ollama(gemma_eval_prompt, temperature=0.1)
                gemma_scores = self._parse_gemma_feedback(gemma_feedback)
                
                # 添加 Gemma 評估結果
                if gemma_scores:
                    # 計算 Gemma 平均分（標準化到 0-1 範圍）
                    gemma_avg = sum(gemma_scores.values()) / (len(gemma_scores) * 5.0)
                    result["gemma_avg"] = gemma_avg
                    result.update({"gemma_" + k: v/5.0 for k, v in gemma_scores.items()})
                else:
                    result["gemma_avg"] = 0.0
                    
            except Exception as e:
                self.logger.warning(f"Gemma 評估時出錯: {str(e)}")
                result["gemma_avg"] = 0.0
            
            # 評估會議特定質量指標
            meeting_metrics = self._evaluate_meeting_specific_quality(generated)
            result.update({"meeting_" + k: v for k, v in meeting_metrics.items()})
            
            # 評估台灣會議記錄質量
            taiwan_metrics = self.taiwan_evaluator.evaluate(reference, generated)
            result.update({"taiwan_" + k: v for k, v in taiwan_metrics.items()})
            
            # 計算會議特定質量分數（結合通用指標和台灣專用指標）
            meeting_quality_score = (
                meeting_metrics.get('has_meeting_info', 0) * 0.1 +
                meeting_metrics.get('has_agenda', 0) * 0.1 +
                meeting_metrics.get('has_decisions', 0) * 0.15 +
                meeting_metrics.get('has_action_items', 0) * 0.15 +
                meeting_metrics.get('has_owners', 0) * 0.05 +
                meeting_metrics.get('has_deadlines', 0) * 0.05 +
                meeting_metrics.get('structure_score', 0) * 0.05 +
                meeting_metrics.get('clarity_score', 0) * 0.05 +
                taiwan_metrics.get('taiwan_meeting_score', 0) * 0.3
            )
            
            # 計算綜合分數（加權平均）
            # 調整權重：會議特定質量(0.4), ROUGE-L (0.25), BERTScore F1 (0.2), BLEU (0.05), Gemma (0.1)
            combined_score = (
                meeting_quality_score * 0.4 +
                result.get("rougeL", 0) * 0.25 +
                result.get("bert_score_f1", 0) * 0.2 +
                result.get("bleu", 0) * 0.05 +
                result.get("gemma_avg", 0) * 0.1
            )
            
            # 確保分數在 0 到 1 之間
            combined_score = max(0.0, min(1.0, combined_score))
            result["meeting_quality_score"] = meeting_quality_score
            result["combined_score"] = combined_score
            
            
            self.logger.info(f"質量評估完成 - 綜合分數: {combined_score:.4f}")
            return result
            
        except Exception as e:
            self.logger.error(f"評估質量時出錯: {str(e)}", exc_info=True)
            return {
                "rouge1": 0.0,
                "rouge2": 0.0,
                "rougeL": 0.0,
                "bert_score_precision": 0.0,
                "bert_score_recall": 0.0,
                "bert_score_f1": 0.0,
                "bleu": 0.0,
                "combined_score": 0.0
            }
        
        # 使用 Gemma 3 12B 進行質量評估（可選，因為可能耗時較長）
        try:
            gemma_eval_prompt = f"""
            請評估以下會議記錄的質量（1-5分，5分最高）：
            
            生成的會議記錄：
            {generated}
            
            參考會議記錄：
            {reference}
            
            請從以下幾個方面評分（1-5分）：
            1. 內容完整性
            2. 準確性
            3. 結構清晰度
            4. 語言流暢度
            5. 專業性
            
            請以 JSON 格式返回評分，例如：
            {{
                "content_completeness": 4,
                "accuracy": 5,
                "structure_clarity": 4,
                "language_fluency": 5,
                "professionalism": 5
            }}
            """
            
            gemma_feedback = self._generate_with_ollama(gemma_eval_prompt, temperature=0.1)
            gemma_scores = self._parse_gemma_feedback(gemma_feedback)
            
            # 添加 Gemma 評估結果（如果可用）
            if gemma_scores:
                result.update({"gemma_" + k: v for k, v in gemma_scores.items()})
                
        except Exception as e:
            self.logger.warning(f"Gemma 評估時出錯: {str(e)}")
        
        return result
        
    def _calculate_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        """
        計算 ROUGE 分數
        
        Args:
            generated: 生成的文本
            reference: 參考文本
            
        Returns:
            包含 ROUGE 分數的字典
        """
        from rouge import Rouge
        
        try:
            rouge = Rouge()
            scores = rouge.get_scores(generated, reference)[0]
            
            return {
                "rouge1": scores["rouge-1"]["f"],
                "rouge2": scores["rouge-2"]["f"],
                "rougeL": scores["rouge-l"]["f"]
            }
        except Exception as e:
            self.logger.warning(f"計算 ROUGE 分數時出錯: {str(e)}")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    
    def _calculate_bert_score(self, generated: str, reference: str) -> Dict[str, float]:
        """
        計算 BERTScore
        
        Args:
            generated: 生成的文本
            reference: 參考文本
            
        Returns:
            包含 BERTScore 的字典
        """
        from bert_score import score as bert_score_fn
        
        try:
            P, R, F1 = bert_score_fn(
                [generated],
                [reference],
                lang="zh",
                verbose=False
            )
            return {
                "precision": P.mean().item(),
                "recall": R.mean().item(),
                "f1": F1.mean().item()
            }
        except Exception as e:
            self.logger.warning(f"計算 BERTScore 時出錯: {str(e)}")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    def _calculate_bleu(self, generated: str, reference: str) -> float:
        """
        計算 BLEU 分數
        """
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        try:
            smoothie = SmoothingFunction().method4
            reference_tokens = [reference.split()]
            generated_tokens = generated.split()
            bleu = sentence_bleu(reference_tokens, generated_tokens, smoothing_function=smoothie)
            if isinstance(bleu, float):
                return bleu
            else:
                return 0.0
        except Exception as e:
            self.logger.error(f"BLEU 計算失敗: {str(e)}")
            return 0.0
    
    def _parse_gemma_feedback(self, feedback: str) -> Dict[str, float]:
        """
        解析 Gemma 模型的評估回饋
        
        Args:
            feedback: Gemma 模型的回饋文字
            
        Returns:
            包含評分的字典
        """
        try:
            # 嘗試從回饋中提取 JSON 部分
            import json
            import re
            
            # 使用正則表達式提取 JSON 部分
            json_match = re.search(r'\{.*\}', feedback, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                scores = json.loads(json_str)
                # 確保所有值都是數字
                return {k: float(v) for k, v in scores.items()}
        except Exception as e:
            self.logger.warning(f"解析 Gemma 回饋時出錯: {str(e)}")
        
        return {}
    
    def _generate_candidates(self, template: str, references: List[str]) -> List[str]:
        """
        根據目前策略與 template 實際產生新候選內容
        """
        # 這裡以所有策略各產生一個候選（可依需求調整）
        candidates = []
        for strategy in [
            self._strategy_improve_formatting,
            self._strategy_add_examples,
            self._strategy_simplify_language,
            self._strategy_add_constraints,
            self._strategy_enhance_structure,
            self._strategy_improve_quality
        ]:
            try:
                candidate = strategy(template, {"references": references})
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                self.logger.warning(f"策略 {strategy.__name__} 產生候選時出錯: {e}")
        if not candidates:
            candidates = [template]
        return candidates


def optimize_meeting_minutes(
    reference_dir: str,
    output_dir: str = "optimized_results",
    model_name: str = "gemma3:12b",
    generation_model: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
    stability_threshold: float = 0.65,
    quality_threshold: float = 0.6,
    max_iterations: int = 10,
    batch_size: int = 3,
    warmup_iterations: int = 2,
    early_stopping_rounds: int = 3,
    min_improvement: float = 0.01,
    taiwan_evaluator: bool = True,
    taiwan_evaluator_weight: float = 0.7
) -> Dict[str, Any]:
    """
    優化會議記錄的主函數
    
    Args:
        reference_dir: 包含參考會議記錄的目錄
        output_dir: 輸出目錄
        model_name: 使用的模型名稱
        generation_model: 生成模型名稱
        stability_threshold: 穩定性閾值
        quality_threshold: 質量閾值
        max_iterations: 最大迭代次數
        batch_size: 每批生成的樣本數
        warmup_iterations: 預熱迭代次數
        early_stopping_rounds: 早停輪數
        min_improvement: 最小改進閾值
    
    Returns:
        優化結果字典
    """
    # 設置日誌
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 創建文件處理器
    log_dir = Path(output_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 設置日誌格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加處理器到日誌記錄器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"優化器已初始化，使用生成模型: {generation_model}")
    logger.info(f"評估和優化模型: {model_name}")
    
    # 讀取參考會議記錄
    references = []
    reference_path = Path(reference_dir)
    for ref_file in reference_path.glob("*.txt"):
        try:
            with open(ref_file, 'r', encoding='utf-8') as f:
                content = f.read()
                references.append({
                    'content': content,
                    'file': str(ref_file.name)
                })
            logger.info(f"已載入參考檔案: {ref_file.name}")
        except Exception as e:
            logger.error(f"讀取參考檔案 {ref_file} 時出錯: {str(e)}")
    
    if not references:
        raise ValueError("未找到有效的參考會議記錄檔案")
    
    logger.info(f"已載入 {len(references)} 個參考會議記錄")
    
    try:
        # 初始化優化器
        optimizer = StabilityOptimizer(
            model_name=model_name,
            stability_threshold=stability_threshold,
            quality_threshold=quality_threshold,
            max_iterations=max_iterations,
            batch_size=batch_size,
            warmup_iterations=warmup_iterations,
            early_stopping_rounds=early_stopping_rounds,
            min_improvement=min_improvement,
            output_dir=output_dir,
            generation_model=generation_model,
        )
        
        template = (
            "[會議記錄]\n"
            "會議主題: {topic}\n"
            "與會人員: {participants}\n"
            "會議時間: {time}\n\n"
            "討論要點:\n\n"
            "決議事項:\n"
            "{decisions}\n\n"
            "行動項目:\n"
            "- {action_items}"
        )
        
        # 執行優化
        reference_texts = [ref['content'] for ref in references]
        results = optimizer.optimize_template(template, reference_texts)
        
        print(f"優化完成！結果已保存至 {output_dir}")
        if isinstance(results, dict) and 'best_score' in results:
            print(f"最佳分數: {results['best_score']:.4f}")
        if isinstance(results, dict) and 'best_params' in results:
            print("最佳參數:", results['best_params'])
        
        return results
    except Exception as e:
        logger.error(f"優化過程中發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="會議記錄優化工具")
    parser.add_argument("reference_dir", type=str, help="包含參考會議記錄的目錄")
    parser.add_argument("-o", "--output-dir", default="optimized_results",
                      help="輸出目錄（默認：optimized_results）")
    parser.add_argument("--model", 
                      default="gemma3:12b",
                      help="使用的模型名稱（默認：gemma3:12b）")
    parser.add_argument("--generation-model",
                      default="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                      help="生成模型名稱（默認：cwchang/llama3-taide-lx-8b-chat-alpha1:latest）")
    parser.add_argument("--stability-threshold", type=float, default=0.65,
                      help="穩定性閾值（默認：0.65）")
    parser.add_argument("--quality-threshold", type=float, default=0.6,
                      help="質量閾值（默認：0.6）")
    parser.add_argument("--max-iterations", type=int, default=10,
                      help="最大迭代次數（默認：10）")
    parser.add_argument("--batch-size", type=int, default=3,
                      help="每批生成的樣本數（默認：3）")
    parser.add_argument("--warmup-iterations", type=int, default=2,
                      help="預熱迭代次數（默認：2）")
    parser.add_argument("--early-stopping-rounds", type=int, default=3,
                      help="早停輪數（默認：3）")
    parser.add_argument("--min-improvement", type=float, default=0.01,
                      help="最小改進閾值（默認：0.01）")
    parser.add_argument("--taiwan-evaluator", type=int, default=1,
                      help="是否啟用台灣會議記錄評估器（1為啟用，0為禁用，默認：1）")
    parser.add_argument("--taiwan-evaluator-weight", type=float, default=0.7,
                      help="台灣評估器在綜合評分中的權重（0-1，默認：0.7）")

    args = parser.parse_args()

    try:
        results = optimize_meeting_minutes(
            reference_dir=args.reference_dir,
            output_dir=args.output_dir,
            model_name=args.model,
            generation_model=args.generation_model,
            stability_threshold=args.stability_threshold,
            quality_threshold=args.quality_threshold,
            max_iterations=args.max_iterations,
            batch_size=args.batch_size,
            warmup_iterations=args.warmup_iterations,
            early_stopping_rounds=args.early_stopping_rounds,
            min_improvement=args.min_improvement,
            taiwan_evaluator=bool(args.taiwan_evaluator),
            taiwan_evaluator_weight=args.taiwan_evaluator_weight
        )
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meeting Minutes Optimizer Script
"""
import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"Python path: {sys.path}")

# 嘗試導入 MeetingEvaluator
try:
    try:
        import sklearn
        from scripts.evaluation.evaluator import MeetingEvaluator
        print("Successfully imported MeetingEvaluator with scikit-learn support")
    except ImportError as e:
        print(f"Warning: scikit-learn is not available, disabling advanced evaluation features: {str(e)}")
        from scripts.evaluation.evaluator import MeetingEvaluator as _BaseEvaluator
        # 創建一個簡化版的 MeetingEvaluator
        class MeetingEvaluator(_BaseEvaluator):
            def evaluate(self, *args, **kwargs):
                print("Warning: Using dummy evaluator because scikit-learn is not available")
                return {"overall_score": 0.0, "status": "sklearn_not_available"}
        print("Created dummy MeetingEvaluator")
except Exception as e:
    print(f"Warning: Could not import MeetingEvaluator, stability evaluation will be disabled: {str(e)}")
    MeetingEvaluator = None

class StrategyConfig:
    """Strategy configuration"""
    def __init__(self, name: str, description: str, components: Dict[str, Any], 
                 format_requirements: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.components = components
        self.format_requirements = format_requirements or {}

class MeetingOptimizer:
    """Meeting minutes optimizer"""
    
    def __init__(self, model_name: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest", 
                 output_dir: Optional[str] = None,
                 strategy_config_path: Optional[Path] = None):
        """Initialize the meeting optimizer"""
        self.model_name = model_name
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "optimized_results"
        self.evaluator = MeetingEvaluator() if MeetingEvaluator else None
        self.logger = logging.getLogger(__name__)
        self.strategies: Dict[str, StrategyConfig] = {}
        
        # 創建輸出目錄
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加載策略配置
        self._load_strategies(strategy_config_path or (project_root / "config" / "improvement_strategies.json"))
        self.logger.info(f"使用 Ollama 模型: {model_name}")
        
        # 初始化默認模板
        self.default_template = """[會議記錄]
會議主題: {topic}
與會人員: {participants}
會議時間: {time}

討論要點:
{key_points}

決議事項:
{decisions}

行動項目:
{action_items}"""
    
    def _load_strategies(self, config_path: Path):
        """Load strategies from configuration file"""
        if not config_path.exists():
            self.logger.warning(f"策略配置文件 {config_path} 未找到，使用默認策略")
            self._load_default_strategies()
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                strategies_data = json.load(f)
            
            if not isinstance(strategies_data, dict):
                raise ValueError(f"配置文件中應為字典，但找到 {type(strategies_data).__name__}")
                
            loaded_count = 0
            for strategy_id, strategy_data in strategies_data.items():
                # 跳過 metadata 部分
                if strategy_id == 'metadata':
                    continue
                    
                try:
                    if not isinstance(strategy_data, dict):
                        self.logger.warning(f"跳過策略 {strategy_id}: 應為字典，但找到 {type(strategy_data).__name__}")
                        continue
                        
                    required_fields = ['name', 'description', 'components']
                    for field in required_fields:
                        if field not in strategy_data:
                            raise ValueError(f"策略 {strategy_id} 中缺少必要字段 '{field}'")
                    
                    self.strategies[strategy_id] = StrategyConfig(
                        name=str(strategy_data['name']),
                        description=str(strategy_data['description']),
                        components=dict(strategy_data['components']),
                        format_requirements=dict(strategy_data.get('format_requirements', {}))
                    )
                    loaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"加載策略 {strategy_id} 時出錯: {str(e)}")
                    continue
                    
            self.logger.info(f"已從 {config_path} 加載 {loaded_count} 個策略")
            
        except Exception as e:
            self.logger.error(f"從 {config_path} 加載策略失敗: {str(e)}")
            self._load_default_strategies()
    
    def _load_default_strategies(self):
        """Load default strategies when config file is not available"""
        self.strategies = {
            "default": StrategyConfig(
                name="默認策略",
                description="默認優化策略",
                components={
                    "summarization": {"enabled": True, "max_length": 500},
                    "key_points": {"enabled": True, "count": 5},
                    "action_items": {"enabled": True}
                },
                format_requirements={"required_sections": ["標準化術語表"]}
            ),
            "structured": StrategyConfig(
                name="結構化摘要",
                description="將會議記錄依議題、決議、待辦事項等分類，提升可讀性。",
                components={
                    "format": "markdown",
                    "sections": ["議題", "討論內容", "決議事項", "待辦事項"]
                },
                format_requirements={"required_sections": ["議題", "決議事項"]}
            )
        }
        self.logger.info("已加載默認策略")
    
    def optimize(self, matched_data: List[Dict], max_iterations: int = 100, batch_size: int = 3,
                warmup_iterations: int = 2, early_stopping: int = 30, min_improvement: float = 0.01) -> Tuple[str, Dict, float]:
        """
        執行完整的優化流程
        
        Args:
            matched_data: 匹配的逐字稿和參考會議記錄列表
            max_iterations: 最大迭代次數
            batch_size: 每批處理的數據量
            warmup_iterations: 預熱迭代次數
            early_stopping: 早停輪數
            min_improvement: 最小改進閾值
            
        Returns:
            tuple: (最佳模板, 最佳策略, 最佳分數)
        """
        self.logger.info(f"開始優化流程，共 {len(matched_data)} 組數據")
        
        # 初始化最佳結果
        best_template = self.default_template
        best_strategy = {}
        best_score = 0.0
        
        # 迭代優化
        for iteration in range(max_iterations):
            self.logger.info(f"\n=== 迭代 {iteration + 1}/{max_iterations} ===")
            
            # 1. 生成會議記錄
            generated = self._generate_minutes_batch(
                matched_data[:batch_size], 
                best_template,
                best_strategy
            )
            
            # 2. 評估生成的會議記錄
            scores = self._evaluate_minutes_batch(
                generated, 
                [d['reference'] for d in matched_data[:batch_size]]
            )
            
            # 3. 更新最佳結果
            current_score = sum(scores.values()) / len(scores) if scores else 0.0
            if current_score > best_score + min_improvement:
                best_score = current_score
                self.logger.info(f"發現新的最佳分數: {best_score:.4f}")
                
                # 保存最佳模板和策略
                self._save_best_template(best_template, best_strategy, best_score)
            
            # 4. 檢查早停條件
            if iteration > warmup_iterations and (iteration - warmup_iterations) >= early_stopping:
                self.logger.info(f"達到早停條件，停止優化")
                break
        
        return best_template, best_strategy, best_score
    
    def _generate_minutes_batch(self, data: List[Dict], template: str, strategy: Dict) -> List[str]:
        """批量生成會議記錄"""
        # 這裡應該是調用模型生成會議記錄的代碼
        # 簡化示例：直接返回模板
        return [template for _ in data]
    
    def _evaluate_minutes_batch(self, generated: List[str], references: List[str]) -> Dict[str, float]:
        """批量評估會議記錄"""
        if not self.evaluator:
            self.logger.warning("評估器不可用，跳過評估")
            return {}
            
        try:
            # 這裡應該是調用評估器的代碼
            # 簡化示例：返回隨機分數
            import random
            return {'score': random.uniform(0.5, 1.0) for _ in generated}
        except Exception as e:
            self.logger.error(f"評估會議記錄時出錯: {str(e)}")
            return {}
    
    def _save_best_template(self, template: str, strategy: Dict, score: float) -> None:
        """保存最佳模板和策略"""
        try:
            # 保存模板
            template_file = self.output_dir / "best_template.txt"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template)
            
            # 保存策略
            strategy_file = self.output_dir / "best_strategy.json"
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(strategy, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"已保存最佳模板和策略到 {self.output_dir}")
            
        except Exception as e:
            self.logger.error(f"保存最佳模板和策略時出錯: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Meeting Minutes Optimizer")
    
    # Add arguments
    parser.add_argument("--input", type=str, required=True, help="Input file path")
    parser.add_argument("--output", type=str, help="Output directory (default: ./output)")
    parser.add_argument("--model", type=str, default="gemma3:4b", help="Ollama model name (default: gemma3:4b)")
    parser.add_argument("--strategy", type=str, default="all", help="Optimization strategy to use (comma-separated)")
    parser.add_argument("--num-candidates", type=int, default=3, help="Number of candidates to generate (default: 3)")
    parser.add_argument("--stability-threshold", type=float, default=0.8, 
                        help="Stability threshold for evaluation (default: 0.8)")
    parser.add_argument("--max-iterations", type=int, default=5, 
                        help="Maximum number of optimization iterations (default: 5)")
    parser.add_argument("--list-strategies", action="store_true", 
                        help="List available strategies and exit")
    parser.add_argument("--strategy-config", type=str, 
                        help="Path to strategy configuration file")
    
    args = parser.parse_args()
    
    # Initialize logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create optimizer
    optimizer = MeetingOptimizer(
        model_name=args.model,
        strategy_config_path=Path(args.strategy_config) if args.strategy_config else None
    )
    
    # List strategies if requested
    if args.list_strategies:
        print("\nAvailable optimization strategies:")
        for strategy_id, strategy in optimizer.strategies.items():
            print(f"\nID: {strategy_id}")
            print(f"Name: {strategy.name}")
            print(f"Description: {strategy.description}")
        return
    
    # Process input file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Optimize content
        optimized_content, metrics = optimizer.optimize(
            text=content,
            strategy=args.strategy,
            num_candidates=args.num_candidates,
            stability_threshold=args.stability_threshold,
            max_iterations=args.max_iterations
        )
        
        # Save result
        output_dir = Path(args.output) if args.output else Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"optimized_{timestamp}_{Path(args.input).name}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        
        # Save metrics if available
        if metrics:
            metrics_file = output_file.with_suffix('.metrics.json')
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"\nOptimization complete!")
        print(f"Output file: {output_file}")
        if metrics:
            print(f"Evaluation metrics: {metrics_file}")
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

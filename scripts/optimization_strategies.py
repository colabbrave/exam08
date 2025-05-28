"""
優化策略定義

定義用於提示詞優化的各種策略。
"""
from typing import Dict, List, Any, Optional, Callable, Union
import random
import re
from dataclasses import dataclass, field
from enum import Enum

class OptimizationTarget(str, Enum):
    """優化目標枚舉"""
    FORMAT = "format"
    CONTENT = "content"
    STYLE = "style"
    ALL = "all"

@dataclass
class OptimizationStrategy:
    """優化策略基類"""
    name: str
    description: str
    target: OptimizationTarget = OptimizationTarget.ALL
    weight: float = 1.0
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def apply(self, prompt: str, **kwargs) -> str:
        """應用策略到提示詞"""
        raise NotImplementedError("子類必須實現此方法")

class FormatOptimizationStrategy(OptimizationStrategy):
    """格式優化策略"""
    
    def __init__(self):
        super().__init__(
            name="format_optimization",
            description="優化提示詞的格式要求，確保生成結構化的輸出",
            target=OptimizationTarget.FORMAT
        )
        self.format_templates = [
            "請確保輸出使用Markdown格式，包含清晰的標題層級。",
            "請使用結構化格式，包含以下部分：\n- 會議概述\n- 主要討論點\n- 決策事項\n- 行動項目",
            "輸出應包含：\n## 會議資訊\n## 與會人員\n## 討論摘要\n## 決議事項\n## 後續行動"
        ]
    
    def apply(self, prompt: str, **kwargs) -> str:
        """添加格式要求到提示詞"""
        format_instruction = random.choice(self.format_templates)
        return f"{prompt}\n\n{format_instruction}"

class ContentOptimizationStrategy(OptimizationStrategy):
    """內容優化策略"""
    
    def __init__(self):
        super().__init__(
            name="content_optimization",
            description="優化提示詞的內容要求，確保涵蓋關鍵信息",
            target=OptimizationTarget.CONTENT
        )
        self.content_instructions = [
            "請確保記錄所有決策及其背後的思考過程。",
            "請特別注意記錄行動項目、負責人和截止日期。",
            "請總結討論的要點，並標記出需要跟進的事項。"
        ]
    
    def apply(self, prompt: str, **kwargs) -> str:
        """添加內容要求到提示詞"""
        content_instruction = random.choice(self.content_instructions)
        return f"{prompt}\n\n{content_instruction}"

class StyleOptimizationStrategy(OptimizationStrategy):
    """風格優化策略"""
    
    def __init__(self):
        super().__init__(
            name="style_optimization",
            description="優化提示詞的語言風格要求",
            target=OptimizationTarget.STYLE
        )
        self.style_templates = [
            "請使用專業且正式的語言風格。",
            "請使用簡潔明瞭的語言，避免冗長。",
            "請使用親切且易於理解的語言風格。"
        ]
    
    def apply(self, prompt: str, **kwargs) -> str:
        """添加風格要求到提示詞"""
        style_instruction = random.choice(self.style_templates)
        return f"{prompt}\n\n{style_instruction}"

class ExampleBasedOptimizationStrategy(OptimizationStrategy):
    """基於範例的優化策略"""
    
    def __init__(self, examples: List[Dict[str, str]] = None):
        super().__init__(
            name="example_based_optimization",
            description="基於範例優化提示詞",
            target=OptimizationTarget.ALL
        )
        self.examples = examples or []
    
    def add_example(self, input_text: str, output_text: str):
        """添加範例"""
        self.examples.append({"input": input_text, "output": output_text})
    
    def apply(self, prompt: str, **kwargs) -> str:
        """添加範例到提示詞"""
        if not self.examples:
            return prompt
            
        examples_section = "\n\n## 範例\n"
        
        for i, example in enumerate(self.examples[:2]):  # 最多使用兩個範例
            examples_section += f"\n### 範例 {i+1}\n"
            examples_section += f"輸入:\n```\n{example['input']}\n```\n\n"
            examples_section += f"輸出:\n```\n{example['output']}\n```\n"
        
        return f"{prompt}{examples_section}"

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, OptimizationStrategy] = {}
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """初始化預設策略"""
        self.add_strategy(FormatOptimizationStrategy())
        self.add_strategy(ContentOptimizationStrategy())
        self.add_strategy(StyleOptimizationStrategy())
    
    def add_strategy(self, strategy: OptimizationStrategy):
        """添加策略"""
        self.strategies[strategy.name] = strategy
    
    def get_strategy(self, name: str) -> Optional[OptimizationStrategy]:
        """獲取指定策略"""
        return self.strategies.get(name)
    
    def get_strategies_by_target(self, target: Union[OptimizationTarget, str]) -> List[OptimizationStrategy]:
        """根據目標獲取策略列表"""
        if isinstance(target, str):
            target = OptimizationTarget(target)
        
        return [
            strategy for strategy in self.strategies.values()
            if strategy.enabled and (strategy.target == target or strategy.target == OptimizationTarget.ALL)
        ]
    
    def apply_strategies(self, prompt: str, target: Union[OptimizationTarget, str] = OptimizationTarget.ALL) -> str:
        """應用所有符合條件的策略到提示詞"""
        strategies = self.get_strategies_by_target(target)
        
        optimized_prompt = prompt
        for strategy in strategies:
            try:
                optimized_prompt = strategy.apply(optimized_prompt)
            except Exception as e:
                print(f"應用策略 {strategy.name} 時出錯: {e}")
        
        return optimized_prompt

# 使用示例
if __name__ == "__main__":
    # 創建策略管理器
    manager = StrategyManager()
    
    # 添加範例
    example_strategy = ExampleBasedOptimizationStrategy()
    example_strategy.add_example(
        "會議討論了專案進度...",
        "# 專案進度會議\n## 與會人員\n- 張三\n- 李四\n\n## 討論摘要\n- 專案進度落後...\n\n## 決議事項\n- 延長開發時間兩週\n\n## 行動項目\n- [ ] 張三：更新專案時間表"
    )
    manager.add_strategy(example_strategy)
    
    # 應用策略
    base_prompt = "請整理以下會議記錄："
    
    print("=== 原始提示詞 ===\n")
    print(base_prompt)
    
    # 應用格式優化
    print("\n=== 格式優化後 ===\n")
    formatted = manager.apply_strategies(base_prompt, OptimizationTarget.FORMAT)
    print(formatted)
    
    # 應用內容優化
    print("\n=== 內容優化後 ===\n")
    content_optimized = manager.apply_strategies(base_prompt, OptimizationTarget.CONTENT)
    print(content_optimized)
    
    # 應用所有優化
    print("\n=== 全部優化後 ===\n")
    fully_optimized = manager.apply_strategies(base_prompt, OptimizationTarget.ALL)
    print(fully_optimized)

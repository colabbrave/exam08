"""
提示詞工具函數

提供處理和生成提示詞的實用函數。
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import json
import random

# 提示詞組件模板
PROMPT_COMPONENTS = {
    'role_definition': [
        "你是一個專業的會議記錄整理專家。",
        "你擅長將雜亂的會議內容整理成結構化的會議記錄。"
    ],
    'format_guidelines': [
        "請使用Markdown格式輸出。",
        "包含會議時間、地點、參與者等基本資訊。",
        "使用清晰的標題和子標題組織內容。",
        "重要決議和行動項目使用粗體或清單標記。"
    ],
    'content_guidelines': [
        "準確記錄會議中的關鍵點和決策。",
        "保持內容簡潔明瞭，避免冗長。",
        "突出行動項目和負責人。"
    ],
    'style_guidelines': [
        "使用專業但易於理解的語言。",
        "保持一致的格式和風格。",
        "使用項目符號或編號列表提高可讀性。"
    ]
}

def load_prompt_components(config_path: Optional[str] = None) -> Dict[str, List[str]]:
    """
    從配置檔案載入提示詞組件
    
    Args:
        config_path: 配置檔案路徑，如果為None則使用預設組件
        
    Returns:
        提示詞組件字典
    """
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"警告: 無法載入提示詞組件配置: {e}，使用預設組件")
    
    return PROMPT_COMPONENTS

def assemble_prompt(components: Dict[str, List[str]], 
                   include_sections: Optional[List[str]] = None) -> str:
    """
    組裝提示詞組件為完整的提示詞
    
    Args:
        components: 提示詞組件字典
        include_sections: 要包含的組件部分，None表示包含所有
        
    Returns:
        組裝後的提示詞字串
    """
    if include_sections is None:
        include_sections = list(components.keys())
    
    prompt_parts = []
    
    # 添加角色定義（如果存在）
    if 'role_definition' in include_sections and 'role_definition' in components:
        prompt_parts.append("\n".join(components['role_definition']))
    
    # 添加格式指南
    if 'format_guidelines' in include_sections and 'format_guidelines' in components:
        prompt_parts.append("\n\n## 格式要求\n" + "\n".join([f"- {g}" for g in components['format_guidelines']]))
    
    # 添加內容指南
    if 'content_guidelines' in include_sections and 'content_guidelines' in components:
        prompt_parts.append("\n\n## 內容要求\n" + "\n".join([f"- {g}" for g in components['content_guidelines']]))
    
    # 添加風格指南
    if 'style_guidelines' in include_sections and 'style_guidelines' in components:
        prompt_parts.append("\n\n## 風格要求\n" + "\n".join([f"- {g}" for g in components['style_guidelines']]))
    
    return "\n\n".join(prompt_parts)

def generate_prompt_variations(base_prompt: str, 
                             variation_type: str = "all",
                             num_variations: int = 3) -> List[str]:
    """
    生成提示詞變體
    
    Args:
        base_prompt: 基礎提示詞
        variation_type: 變體類型，可選值：'format', 'content', 'style', 'all'
        num_variations: 要生成的變體數量
        
    Returns:
        提示詞變體列表
    """
    variations = []
    
    # 確保至少返回一個變體
    if num_variations < 1:
        num_variations = 1
    
    # 生成格式變體
    if variation_type in ['format', 'all']:
        formats = [
            "請使用Markdown格式輸出，包含清晰的標題層級。",
            "請使用結構化格式，包含章節標題和項目符號。",
            "請使用簡潔的段落格式，避免過多的標題層級。"
        ]
        variations.extend([f"{base_prompt}\n\n{fmt}" for fmt in formats[:num_variations]])
    
    # 生成內容變體
    if variation_type in ['content', 'all'] and len(variations) < num_variations:
        contents = [
            "請著重記錄會議中的決策和行動項目。",
            "請詳細記錄討論過程和各方意見。",
            "請重點記錄會議結論和後續步驟。"
        ]
        variations.extend([f"{base_prompt}\n\n{cont}" for cont in contents[:num_variations-len(variations)]])
    
    # 生成風格變體
    if variation_type in ['style', 'all'] and len(variations) < num_variations:
        styles = [
            "請使用正式且專業的語言風格。",
            "請使用簡潔明瞭的語言風格。",
            "請使用親切且易於理解的語言風格。"
        ]
        variations.extend([f"{base_prompt}\n\n{style}" for style in styles[:num_variations-len(variations)]])
    
    # 如果變體不足，使用基礎提示詞填充
    while len(variations) < num_variations:
        variations.append(base_prompt)
    
    return variations[:num_variations]

def extract_components_from_examples(examples: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """
    從範例中提取提示詞組件
    
    Args:
        examples: 範例列表，每個範例應包含'input'和'output'鍵
        
    Returns:
        提取的提示詞組件字典
    """
    components = {
        'format_guidelines': set(),
        'content_guidelines': set(),
        'style_guidelines': set()
    }
    
    for example in examples:
        # 分析輸出格式
        if 'output' in example:
            output = example['output']
            
            # 檢測Markdown格式
            if any(mark in output for mark in ['# ', '## ', '- [ ]', '1. ']):
                components['format_guidelines'].add("使用Markdown格式進行結構化輸出")
            
            # 檢測結構化內容
            if any(sec in output.lower() for sec in ['## 與會人員', '## 會議議程', '## 決議事項']):
                components['format_guidelines'].add("包含標準章節：與會人員、會議議程、決議事項等")
            
            # 檢測行動項目
            if any(mark in output for mark in ['- [ ]', '行動項目', '待辦事項']):
                components['content_guidelines'].add("明確標記行動項目和負責人")
    
    # 轉換為列表並添加預設值
    result = {}
    for key, items in components.items():
        result[key] = list(items) if items else PROMPT_COMPONENTS.get(key, [])
    
    # 添加角色定義
    result['role_definition'] = PROMPT_COMPONENTS['role_definition']
    
    return result

def save_prompt_components(components: Dict[str, List[str]], output_path: str):
    """
    保存提示詞組件到檔案
    
    Args:
        components: 提示詞組件字典
        output_path: 輸出檔案路徑
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(components, f, ensure_ascii=False, indent=2)
        print(f"提示詞組件已保存到: {output_path}")
    except Exception as e:
        print(f"保存提示詞組件時出錯: {e}")

# 使用示例
if __name__ == "__main__":
    # 載入預設組件
    components = load_prompt_components()
    
    # 組裝提示詞
    prompt = assemble_prompt(components)
    print("=== 生成的提示詞 ===\n")
    print(prompt)
    
    # 生成變體
    print("\n=== 提示詞變體 ===\n")
    variations = generate_prompt_variations("請整理以下會議記錄：", num_variations=2)
    for i, var in enumerate(variations, 1):
        print(f"變體 {i}:\n{var}\n")

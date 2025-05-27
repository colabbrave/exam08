#!/usr/bin/env python3
"""
會議記錄優化改進腳本

實現策略組合優化：
1. 補充省略資訊
2. 明確標註發言者
3. 結構化摘要
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
import torch
from transformers import pipeline

# 初始化模型
def init_model(model_name: str = "cwchang/llama3-taide-lx-8b-chat-alpha1_latest"):
    """初始化語言模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipeline(
        "text-generation",
        model=model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device=device
    )
    return pipe

# 生成提示詞模板
def generate_prompt(strategy: str, text: str) -> str:
    """根據不同策略生成提示詞"""
    prompts = {
        "supplement": (
            "請補充以下會議記錄中可能省略的資訊，"
            "包括但不限於：\n"
            "1. 未明確說出的主語、受詞等\n"
            "2. 省略的專業術語全稱\n"
            "3. 背景資訊補充\n\n"
            f"原始記錄：\n{text}\n\n"
            "補充後的記錄："
        ),
        "speaker": (
            "請為以下會議記錄明確標註發言者，"
            "並保持原始內容不變：\n\n"
            f"{text}\n\n"
            "標註發言者後的記錄："
        ),
        "structure": (
            "請將以下會議記錄轉換為結構化格式，"
            "包含以下部分：\n"
            "1. 會議基本信息（時間、地點、與會人員）\n"
            "2. 討論議題\n"
            "3. 決議事項\n"
            "4. 行動項目（負責人、截止日期）\n\n"
            f"原始記錄：\n{text}\n\n"
            "結構化記錄："
        )
    }
    return prompts.get(strategy, text)

# 優化會議記錄
def optimize_minutes(
    model, 
    text: str, 
    strategies: List[str] = ["supplement", "speaker", "structure"],
    max_length: int = 1024
) -> str:
    """應用多種策略優化會議記錄"""
    optimized_text = text
    
    for strategy in strategies:
        prompt = generate_prompt(strategy, optimized_text)
        response = model(
            prompt,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        optimized_text = response[0]['generated_text'].replace(prompt, "").strip()
    
    return optimized_text

# 主函數
def main():
    parser = argparse.ArgumentParser(description="會議記錄優化工具")
    parser.add_argument("input_file", help="輸入文件路徑")
    parser.add_argument("-o", "--output-dir", default="optimized", 
                       help="輸出目錄（默認：optimized）")
    parser.add_argument("--model", default="cwchang/llama3-taide-lx-8b-chat-alpha1_latest",
                       help="模型名稱或路徑")
    parser.add_argument("--max-length", type=int, default=2048,
                       help="生成文本的最大長度")
    args = parser.parse_args()

    # 準備輸出目錄
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加載模型
    print(f"正在加載模型: {args.model}...")
    model = init_model(args.model)


    # 讀取輸入文件
    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 優化會議記錄
    print("正在優化會議記錄...")
    optimized_text = optimize_minutes(
        model,
        text,
        max_length=args.max_length
    )

    # 保存結果
    output_file = output_dir / f"optimized_{Path(args.input_file).name}"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(optimized_text)

    print(f"優化完成！結果已保存至: {output_file}")

if __name__ == "__main__":
    main()

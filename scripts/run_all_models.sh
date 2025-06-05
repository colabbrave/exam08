#!/bin/bash

# 定義要使用的模型列表
MODELS=(
    "gemma3:4b"
    "gemma3:12b"
    "gemma3:12b"
    "llama3.1:8b"
    "jcai/llama3-taide-lx-8b-chat-alpha1:Q4_K_M"
    "cwchang/llama3-taide-lx-8b-chat-alpha1:latest"
)

# 為每個模型運行優化
for model in "${MODELS[@]}"; do
    echo "=================================================="
    echo "正在使用模型: $model"
    echo "=================================================="
    python scripts/optimize.py --model "$model"
    echo "模型 $model 的優化已完成"
    echo ""
done

echo "所有模型優化流程完成！"

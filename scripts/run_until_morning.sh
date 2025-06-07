#!/bin/bash

# 切換到專案根目錄
cd "$(dirname "$0")/.."

# 計算到明天早上七點的秒數
tomorrow_7am=$(date -v+1d -v7H -v0M -v0S +%s)
now=$(date +%s)
duration=$((tomorrow_7am - now))

echo "腳本將執行到明天早上七點（還有 $duration 秒）"

# 執行優化腳本，並在指定時間後停止
timeout $duration ./scripts/run_optimization.sh

echo "執行時間已到，腳本已停止" 
#!/bin/bash
# 專案維護便捷腳本
# 提供快速存取各種維護工具的入口

echo "🔧 專案維護工具選單"
echo "========================================"
echo "1. 專案結構驗證"
echo "2. 深度清理"
echo "3. 月度維護"
echo "4. 類型檢查"
echo "5. 測試執行"
echo "6. 顯示專案狀態"
echo "========================================"

read -p "請選擇選項 (1-6): " choice

case $choice in
    1)
        echo "🔍 執行專案結構驗證..."
        ./scripts/maintenance/verify_structure_new.sh
        ;;
    2)
        echo "🧹 執行深度清理..."
        ./scripts/maintenance/deep_cleanup.sh
        ;;
    3)
        echo "📅 執行月度維護..."
        ./scripts/maintenance/monthly_maintenance.sh
        ;;
    4)
        echo "🔍 執行類型檢查..."
        echo "檢查核心模組..."
        python -m mypy scripts/optimization/stability_optimizer.py --ignore-missing-imports
        python -m mypy scripts/evaluation/taiwan_meeting_evaluator.py --ignore-missing-imports
        python -m mypy scripts/evaluation/evaluator.py --ignore-missing-imports
        ;;
    5)
        echo "🧪 執行測試..."
        python -m pytest tests/ -v
        ;;
    6)
        echo "📊 專案狀態..."
        echo "根目錄項目數: $(ls -1 | wc -l | tr -d ' ')"
        echo "腳本數量: $(find scripts/ -name "*.py" | wc -l | tr -d ' ')"
        echo "測試數量: $(find tests/ -name "test_*.py" | wc -l | tr -d ' ')"
        echo "文檔數量: $(find docs/ -name "*.md" | wc -l | tr -d ' ')"
        echo "最近修改: $(ls -lt | head -2 | tail -1 | awk '{print $6, $7, $8, $9}')"
        ;;
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

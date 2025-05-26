import subprocess
import sys

def load_model(model_name: str, prompt: str = "你好") -> None:
    """
    載入指定模型並測試是否可用。
    :param model_name: Ollama 模型名稱
    :param prompt: 測試用提示詞
    """
    try:
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"模型 {model_name} 已成功載入並回應：{result.stdout.strip()}")
        else:
            print(f"載入模型 {model_name} 失敗：{result.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"載入模型時發生錯誤：{e}", file=sys.stderr)

def switch_model(model_name: str) -> None:
    """
    切換至指定模型（實際上是重新載入）。
    :param model_name: Ollama 模型名稱
    """
    print(f"切換至模型 {model_name} ...")
    load_model(model_name)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ollama 模型管理工具")
    parser.add_argument("action", choices=["load", "switch"], help="載入或切換模型")
    parser.add_argument("--model", type=str, required=True, help="模型名稱")
    args = parser.parse_args()

    if args.action == "load":
        load_model(args.model)
    elif args.action == "switch":
        switch_model(args.model)
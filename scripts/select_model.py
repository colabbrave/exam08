import subprocess
import sys
import argparse

def list_models():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        print("找不到 ollama 指令，請確認已安裝並設定於 PATH。", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("執行 ollama list 失敗，錯誤訊息如下：", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    
    models = []
    lines = result.stdout.strip().split("\n")
    for line in lines:
        # 跳過標頭與空行
        if not line.strip() or line.startswith("NAME"):
            continue
        # 取第一欄為模型名稱
        name = line.split()[0]
        models.append(name)
    return models

def select_model(interactive=True, default_model=None):
    models = list_models()
    if not models:
        print("找不到任何模型，請先用 ollama pull 下載模型。", file=sys.stderr)
        sys.exit(1)
    
    # 如果指定了默認模型且存在，則直接返回
    if default_model and default_model in models:
        return default_model
    
    # 非交互模式，返回第一個模型
    if not interactive or not sys.stdin.isatty():
        print("使用非交互模式，自動選擇第一個可用模型...", file=sys.stderr)
        return models[0]
    
    # 交互模式
    print("請選擇要使用的模型：", file=sys.stderr)
    for idx, model in enumerate(models, 1):
        print(f"{idx}. {model}", file=sys.stderr)
    
    while True:
        try:
            print("請輸入模型編號：", end='', file=sys.stderr, flush=True)
            choice = input().strip()
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                return models[int(choice)-1]
            print("請輸入有效的編號。", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            print("\n操作已中斷，使用第一個可用模型。", file=sys.stderr)
            return models[0]
        except Exception as e:
            print(f"發生錯誤: {e}", file=sys.stderr)
            return models[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='選擇 Ollama 模型')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式，自動選擇第一個可用模型')
    parser.add_argument('--default', type=str, help='指定默認模型名稱')
    args = parser.parse_args()
    
    try:
        model = select_model(interactive=not args.non_interactive, default_model=args.default)
        print(model)
    except Exception as e:
        print(f"錯誤: {str(e)}", file=sys.stderr)
        sys.exit(1)
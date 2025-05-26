# Python 3.11 slim base image
FROM python:3.11-slim

WORKDIR /app

# 建議使用 uv 或 venv 虛擬環境
# RUN pip install uv

COPY . /app

# 如有 requirements.txt 可取消註解
# RUN pip install -r requirements.txt

CMD ["python3"]

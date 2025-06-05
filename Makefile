.PHONY: install test lint format clean

install:
	pip install -r config/requirements.txt
	pip install -r config/requirements-dev.txt
	pre-commit install

test:
	pytest tests/ --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/
	mypy src/ tests/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

setup: install format lint test 
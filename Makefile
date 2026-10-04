IMAGE_NAME ?= python-mcp-template
IMAGE_TAG  ?= latest

.PHONY: install dev test run clean docker-build
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

run:
	PYTHONPATH=src python src/main.py

docker-build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ *.egg-info .pytest_cache

FROM python:3.11-slim

WORKDIR /app

# poetry-core builds from src/, so it must be present at install time
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

ENV PYTHONPATH=src

CMD ["python", "src/main.py"]

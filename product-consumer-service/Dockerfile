FROM python:3.11-slim

WORKDIR /workspace/product-consumer-service

COPY pyproject.toml .
RUN pip install --upgrade pip --quiet \
 && pip install --quiet ".[dev]"

COPY src/ src/
COPY tests/ tests/

EXPOSE 3000

ENV PYTHONPATH=/workspace/product-consumer-service/src

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

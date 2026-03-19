FROM python:3.11-slim

WORKDIR /workspace/product-provider-service

COPY pyproject.toml .
RUN pip install --upgrade pip --quiet \
 && pip install --quiet ".[dev]"

COPY src/ src/
COPY tests/ tests/

EXPOSE 3001

ENV PYTHONPATH=/workspace/product-provider-service/src

CMD ["uvicorn", "api.server:create_app", "--host", "0.0.0.0", "--port", "3001", "--reload", "--factory"]

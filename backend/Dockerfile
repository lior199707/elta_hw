# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable


FROM --platform=linux/amd64 python:3.13-slim AS final

RUN useradd --no-create-home --shell /bin/false appuser \
 && mkdir /data \
 && chown appuser /data

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

USER appuser
EXPOSE 8000
CMD ["uvicorn", "doc_checker.main:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY *.py *.sql README.md Procfile ./
COPY materialised_views/ ./materialised_views/
COPY pages/ ./pages/
COPY apps/ ./apps/
COPY content/ ./content/
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["sh", "-c", "uv run streamlit run hello.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --browser.gatherUsageStats=false"]

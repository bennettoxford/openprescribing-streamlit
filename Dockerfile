FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app.py README.md ./
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["sh", "-c", "uv run streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --browser.gatherUsageStats=false"]

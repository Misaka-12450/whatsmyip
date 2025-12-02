FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT [ \
    "uv", \
    "run", \
    "streamlit", \
    "run", \
    "streamlit_app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0" \
    ]
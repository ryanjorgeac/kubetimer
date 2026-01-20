FROM python:3.14-slim-trixie

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .

COPY README.md .

RUN uv pip install --system --no-cache .

COPY kubetimer/ ./kubetimer/

EXPOSE 8080

CMD ["uv", "run", "kubetimer/main.py"] 
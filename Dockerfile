FROM python:3.14-slim-trixie

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .

RUN uv pip install --system --no-cache --no-dev .

COPY kubetimer/ ./kubetimer/

EXPOSE 8080

CMD ["kopf", "run", "kubetimer/main.py", "--standalone", "--liveness=http://0.0.0.0:8080/healthz"] 
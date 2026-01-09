FROM python:3.14-slim-trixie

RUN pip install kubernetes kopf

COPY operator_sync.py /app/main.py

CMD ["kopf", "run", "/app/main.py", "--liveness", "http://0.0.0.0:8080/healthz", "--standalone"] 
FROM python:3.9-slim

RUN pip install kubernetes kopf

COPY operator-test.py /app/main.py

CMD ["kopf", "run", "/app/main.py", "--verbose", "--standalone"]
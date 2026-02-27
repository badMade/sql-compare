FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src src/

RUN pip install --no-cache-dir .

CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} sql_compare.web:app"]

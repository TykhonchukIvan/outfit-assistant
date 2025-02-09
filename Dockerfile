FROM python:3.11.8-alpine AS builder

RUN pip install --upgrade pip && \
    pip install poetry

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

RUN ls -lah /app && cat /app/pyproject.toml

COPY . .

RUN poetry install --no-interaction --no-ansi --no-cache || \
    cat /root/.cache/pypoetry/logs/*.log

FROM python:3.11.8-alpine AS server

WORKDIR /app

RUN pip install --upgrade pip && pip install poetry

COPY --from=builder /app /app

CMD ["poetry", "run", "python", "src/main.py"]

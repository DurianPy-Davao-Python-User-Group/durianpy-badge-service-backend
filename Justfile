default:
    @just --list

run-local-api:
    PYTHONPATH=. uv run fastapi dev src/presentation/api/main.py

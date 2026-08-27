default:
    @just --list

run-local-api:
    PYTHONPATH=. uv run fastapi dev src/presentation/api/main.py

prepare-pre-commit:
    uv run prek install --hook-type pre-commit --hook-type commit-msg --prepare-hooks

default:
    @just --list

run-local-api:
    PYTHONPATH=. uv run fastapi dev src/presentation/api/main.py

prepare-pre-commit:
    uv run prek install --hook-type pre-commit --hook-type commit-msg --prepare-hooks

generate-env stage="dev":
    @rm -f .env
    @echo "CLOUDFRONT_URL=$(aws ssm get-parameter --name /durianpy-badge-system/backend/cloudfront-url-{{stage}} --region ap-southeast-1 --query Parameter.Value --output text)" >> .env

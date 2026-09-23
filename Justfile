export AWS_REGION := "ap-southeast-1"
export AWS_DEFAULT_REGION := "ap-southeast-1"

default:
    @just --list

# Initialize and install git pre-commit and commit-msg hooks (run this first and foremost)
prepare-pre-commit:
    uv run prek install --hook-type pre-commit --hook-type commit-msg --prepare-hooks

run-local-api:
    PYTHONPATH=. uv run fastapi dev src/presentation/api/main.py

run-unit-test:
    uv run pytest

generate-env stage="dev":
    @rm -f .env
    @echo "CLOUDFRONT_URL=$(aws ssm get-parameter --name /durianpy-badge-system/backend/cloudfront-url-{{ replace(replace(stage, 'stage=', ''), 'env=', '') }} --region ap-southeast-1 --query Parameter.Value --output text)" >> .env
    @echo "COGNITO_USER_POOL_ID=$(aws ssm get-parameter --name /durianpy-badge-system/backend/cognito-user-pool-id-{{ replace(replace(stage, 'stage=', ''), 'env=', '') }} --region ap-southeast-1 --with-decryption --query Parameter.Value --output text)" >> .env
    @echo "COGNITO_APP_CLIENT_ID=$(aws ssm get-parameter --name /durianpy-badge-system/backend/cognito-app-client-id-{{ replace(replace(stage, 'stage=', ''), 'env=', '') }} --region ap-southeast-1 --with-decryption --query Parameter.Value --output text)" >> .env
    @echo "TECHTIX_API_BASE_URL=$(aws ssm get-parameter --name /durianpy-badge-system/backend/techtix-api-base-url-{{ replace(replace(stage, 'stage=', ''), 'env=', '') }} --region ap-southeast-1 --query Parameter.Value --output text)" >> .env

# Build Lambda dependency layer if missing or manifests changed
build-layer:
    bash terraform/modules/lambda/scripts/build_layer.sh . terraform/modules/lambda/.build python3.12 x86_64

# Preview Terraform deployment plan for target stage (defaults to dev)
plan-deploy stage="dev": build-layer
    terraform -chdir=terraform init
    terraform -chdir=terraform plan -var="environment={{ replace(replace(stage, 'stage=', ''), 'env=', '') }}"

# Deploy backend application and infrastructure via Terraform to target stage (defaults to dev)
deploy stage="dev": build-layer
    terraform -chdir=terraform init
    terraform -chdir=terraform apply -var="environment={{ replace(replace(stage, 'stage=', ''), 'env=', '') }}"

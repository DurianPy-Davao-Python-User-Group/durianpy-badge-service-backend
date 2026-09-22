# AWS Dev Environment Deployment Guide (Terraform & AWS SSO)

This guide documents the end-to-end process for deploying the DurianPy Badge System Backend to the AWS `dev` environment using Terraform. Deploying to `dev` enables developers to test, validate, and debug their feature changes directly against real AWS infrastructure (including Amazon API Gateway, AWS Lambda, Amazon DynamoDB, AWS Systems Manager, Amazon CloudFront, and AWS Cognito) prior to submitting pull requests or promoting changes to production.


## 1. Prerequisites

Before deploying, ensure you have the following tools installed and accounts provisioned:

- **AWS CLI (v2)**: Installed on your host workstation or within the Dev Container.
- **Terraform CLI (>= 1.5.0)**: Installed on your system.
- **uv**: Fast Python package manager used by the Lambda packaging script to compile and vendor production dependencies.
- **AWS SSO Invitation**: An invitation to the DurianPy AWS IAM Identity Center (AWS SSO) organization.
- **Terraform Cloud / HCP Terraform Invitation**: An invitation sent to your email to join the DurianPy Terraform organization.


## 2. Step 1: Log in to Terraform (HCP Terraform)

All developers deploying infrastructure will be invited to the DurianPy organization on HCP Terraform (formerly Terraform Cloud). The project uses HCP Terraform as a centralized remote state backend with automatic state locking to prevent concurrent deployment drift.

### 2.1 Workspace Configuration
- **Organization**: `durianpy`
- **Workspace Prefix**: `durianpy-badge-system-backend-`
- **Workspace Mapping**:
  - `dev` stage maps to `durianpy-badge-system-backend-dev`
  - `prod` stage maps to `durianpy-badge-system-backend-prod`
  - Any `<env>` stage maps to `durianpy-badge-system-backend-<env>`
- **Execution Mode**: **Local** (`Settings > General > Execution Mode > Local`). Each workspace in HCP Terraform must be set to Local execution mode because deployments run locally on developer workstations utilizing AWS SSO temporary credentials and vendoring Lambda dependencies via `uv`.

### 2.2 Accept Organization Invitation
1. Check your email inbox for an invitation from HCP Terraform / Terraform Cloud to join the DurianPy organization.
2. Follow the email link to accept the invitation and set up your account if you do not already have one.

### 2.3 Authenticate CLI via `terraform login`
Run the following command in your terminal:

```bash
terraform login
```

1. When prompted: `Do you want to proceed?`, type `yes` and press Enter.
2. Terraform will automatically launch your default browser to generate an API token, or provide a URL:
   ```
   https://app.terraform.io/app/settings/tokens?source=terraform-login
   ```
3. In the browser, provide a token description (e.g., `durianpy-dev-<your-name>`) and click **Generate API token**.
4. Copy the generated token, paste it into your terminal prompt, and press Enter.
5. Terraform will save your credentials locally to `~/.terraform.d/credentials.tfrc.json`.

You will see:
```text
Success! Terraform has obtained and saved an API token.
```

### 2.4 Select or Create Environment Workspace (Manual Setup)
Workspaces are managed manually via the Terraform CLI. When working with or switching target environments:

```bash
terraform -chdir=terraform init
terraform -chdir=terraform workspace select -or-create dev
```

For other environments such as `prod`:
```bash
terraform -chdir=terraform workspace select -or-create prod
```

Ensure your active workspace matches your intended deployment environment before running `just plan-deploy` or `just deploy`.

### 2.5 Migrate Local State (One-time for Existing State)
If you have an existing local `terraform.tfstate` file for `dev`:
1. Ensure the active workspace is `dev`:
   ```bash
   terraform -chdir=terraform workspace select -or-create dev
   ```
2. Initialize and migrate:
   ```bash
   terraform -chdir=terraform init -migrate-state
   ```
3. When prompted `Do you want to copy existing state to the new backend?`, type `yes`. Terraform transfers state to `durianpy-badge-system-backend-dev`.




## 3. Step 2: Log in to AWS via AWS SSO

AWS IAM Identity Center (AWS SSO) provides role-based temporary credentials for interacting with the AWS `dev` account.

### 3.1 Configure AWS SSO Profile (One-time Setup)
If you have not configured your local AWS SSO profile yet, run:

```bash
aws configure sso
```

Provide the requested configuration details:
- **SSO session name**: `durianpy`
- **SSO start URL**: `https://durianpy-root.awsapps.com/start/#`
- **SSO region**: `ap-southeast-1`
- **SSO registration scopes**: `sso:account:access`
- **CLI default client Region**: `ap-southeast-1`
- **CLI default output format**: `json`
- **CLI profile name**: `durianpy-dev`

Alternatively, you can add or verify the profile entry in your `~/.aws/config`:

```ini
[profile durianpy-dev]
sso_session = durianpy
sso_account_id = <target-account-id>
sso_role_name = <assigned-role-name>
region = ap-southeast-1
output = json

[sso-session durianpy]
sso_start_url = https://durianpy-root.awsapps.com/start/#
sso_region = ap-southeast-1
sso_registration_scopes = sso:account:access
```



### 3.2 Authenticate AWS SSO Session
Whenever your credentials expire or prior to deploying, initiate the SSO authentication flow:

```bash
aws sso login --profile durianpy-dev
```

This opens your web browser. Confirm the authentication code and authorize access in the AWS SSO portal.

### 3.3 Set Active Environment Variables
Set your active terminal session to use the authenticated profile:

```bash
export AWS_PROFILE=durianpy-dev
```

> **Note**: The AWS region defaults to `ap-southeast-1` automatically across `Justfile` and `terraform/variables.tf`. You do not need to manually export `AWS_REGION`.

### 3.4 Verify Active AWS Credentials
Confirm that your AWS session is active and assumes the expected role:

```bash
aws sts get-caller-identity
```

Ensure the output reflects the target AWS account ID and your assumed SSO user role.

### 3.5 Generate Local Environment Variables (`just generate-env`)
Once authenticated against AWS SSO, generate or refresh your local `.env` file with configuration values stored in AWS Systems Manager (SSM) Parameter Store:

```bash
just generate-env dev
```

This retrieves the CloudFront distribution URL, Cognito User Pool ID, and Cognito App Client ID for the `dev` stage, enabling your local development server (`just run-local-api`) and test verification scripts to connect to live dev cloud resources.



## 4. Step 3: Deploy to Dev Environment

With both Terraform and AWS SSO authenticated, you can deploy your application changes.

### Option A: Using Just Recipes (Recommended)

From the project root directory:

```bash
# Preview execution plan (runs terraform -chdir=terraform init + plan -var="environment=dev")
just plan-deploy

# Apply deployment to dev (runs terraform -chdir=terraform init + apply -var="environment=dev")
just deploy
```

> **Note**: Both recipes default to `stage="dev"`. You can explicitly target another stage if needed, for example `just deploy prod` or `just plan-deploy prod`.

### Option B: Using Direct Terraform CLI Commands

If you prefer executing Terraform commands manually without `just`, you can run them directly from the project root using `-chdir=terraform`:

#### 1. Initialize Terraform Working Directory
Run `terraform init` to download required providers (`hashicorp/aws`, `hashicorp/archive`) and initialize local modules (`lambda`, `apigw`, `event-bridge`):

```bash
terraform -chdir=terraform init
```

#### 2. Review Execution Plan
Generate and inspect an execution plan before applying changes:

```bash
terraform -chdir=terraform plan -var="environment=dev"
```

> **Note**: The `environment` variable defaults to `dev` in `variables.tf`, so specifying `-var="environment=dev"` makes the target environment explicit.

What Terraform evaluates during planning:
- Packages application source code from `src/` into `.build/dev-durianpy-badge-system-api.zip` (ignoring tests, dev caches, and virtual environments).
- Executes `build_layer.sh` via `local-exec` to export production dependencies (`uv export --no-dev`) and install them into the Lambda dependencies layer structure for Linux `x86_64`.
- Compares API Gateway route definitions, Lambda environment variables, and IAM permissions against the existing AWS state.

#### 3. Apply Deployment
Execute the deployment to AWS `dev`:

```bash
terraform -chdir=terraform apply -var="environment=dev"
```

Review the planned changes displayed in the terminal. When prompted:
```text
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

Type `yes` and hit Enter. Terraform will build the layer, upload the ZIP archives to AWS, update the Lambda function, configure the HTTP API Gateway, and output resource endpoints.


## 5. Step 4: Verify Your Deployment

Testing your changes in `dev` validates that all cloud integrations, permissions, and dependencies operate correctly in the real AWS Lambda runtime.

### 5.1 Review Outputs
Upon successful completion, Terraform displays outputs defined in `outputs.tf`:

```text
Apply complete! Resources: X added, Y changed, Z destroyed.

Outputs:

api_endpoint = "https://<api-id>.execute-api.ap-southeast-1.amazonaws.com"
api_id = "<api-id>"
lambda_function_arn = "arn:aws:lambda:ap-southeast-1:<account-id>:function:dev-durianpy-badge-system-api"
lambda_function_name = "dev-durianpy-badge-system-api"
lambda_layer_arn = "arn:aws:lambda:ap-southeast-1:<account-id>:layer:dev-durianpy-badge-system-api-dependencies:1"
lambda_role_arn = "arn:aws:iam::<account-id>:role/dev-durianpy-badge-system-api-lambda-role"
warmer_rule_arn = "arn:aws:events:ap-southeast-1:<account-id>:rule/dev-durianpy-badge-system-warmer"
```

Take note of the `api_endpoint` URL.

### 5.2 Smoke Test Endpoints

1. **Health Check Endpoint**:
   ```bash
   curl -i https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/health
   ```
   Expected response: `HTTP/1.1 200 OK` with body `"OK"`.

2. **Public Catalog Endpoint**:
   ```bash
   curl -i https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/api/catalog/designs
   ```
   Expected response: `HTTP/1.1 200 OK` with a JSON payload of published badge designs.

3. **Interactive Swagger Documentation**:
   Open the following URL in your web browser:
   ```
   https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/docs
   ```
   The `dev` documentation route is protected by HTTP Basic Auth. Enter the credentials retrieved from AWS SSM Parameter Store:
   - Username parameter: `/durianpy-badge-system/backend/swagger-basic-auth-username-dev`
   - Password parameter: `/durianpy-badge-system/backend/swagger-basic-auth-password-dev`

   You can inspect these values using the AWS CLI:
   ```bash
   aws ssm get-parameter --name /durianpy-badge-system/backend/swagger-basic-auth-username-dev --query Parameter.Value --output text
   aws ssm get-parameter --name /durianpy-badge-system/backend/swagger-basic-auth-password-dev --with-decryption --query Parameter.Value --output text
   ```

### 5.3 Inspect Live CloudWatch Logs
To observe application execution logs, debug errors, or monitor incoming requests in real time:

```bash
aws logs tail /aws/lambda/dev-durianpy-badge-system-api --follow
```

### 5.4 Refresh Local Environment (`just generate-env`)
After deploying changes or whenever backend SSM parameters change, refresh your local `.env` configuration to ensure your local workstation and tests stay in sync with the dev cloud environment:

```bash
just generate-env dev
```



## 6. Architecture & Resource Reference

The `dev` deployment provisions and manages the following AWS resources:

| Resource | Identifier / Name | Description |
|---|---|---|
| **AWS Lambda** | `dev-durianpy-badge-system-api` | Python 3.12 (`x86_64`) running FastAPI via Mangum adapter (`src.presentation.api.mangum_handler.handler`). |
| **Lambda Layer** | `dev-durianpy-badge-system-api-dependencies` | Bundled Python production dependencies generated from `pyproject.toml` using `uv`. |
| **HTTP API Gateway** | `dev-durianpy-badge-system-http-api` | HTTP API proxying requests to the backend Lambda function with auto-deploy on stage `$default`. |
| **EventBridge Warmer** | `dev-durianpy-badge-system-warmer` | Scheduled rule triggering the Lambda function every 10 minutes to minimize cold starts. |
| **IAM Execution Role** | `dev-durianpy-badge-system-api-lambda-role` | Least-privilege role granting permissions to DynamoDB, SSM parameters, and CloudWatch logging. |


## 7. Troubleshooting & FAQ

### Expired AWS SSO Token
- **Error**: `The security token included in the request is expired` or `ExpiredToken`.
- **Solution**: Re-authenticate your AWS SSO session:
  ```bash
  aws sso login --profile durianpy-dev
  ```

### Unauthorized Terraform Cloud Error
- **Error**: `Error: Unauthorized` or `401 Unauthorized` during `terraform init` or remote state access.
- **Solution**: Re-authenticate with Terraform Cloud:
  ```bash
  terraform login
  ```
  Ensure you have accepted the email invitation to the DurianPy organization on HCP Terraform.

### Missing `uv` in Environment
- **Error**: `build_layer.sh: line 18: uv: command not found`.
- **Solution**: Install `uv` on your host or execute the deployment from within the Dev Container:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  ```

### DynamoDB or SSM Permission Denied
- **Error**: `AccessDeniedException` when fetching parameters or querying DynamoDB.
- **Solution**: Confirm that your AWS SSO user has been assigned the appropriate dev access permission set. Verify your caller identity with:
  ```bash
  aws sts get-caller-identity
  ```

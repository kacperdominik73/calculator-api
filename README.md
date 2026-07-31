# Calculator API

A simple REST API for arithmetic operations, deployed to AWS ECS Fargate via GitHub Actions and Terraform.

## Architecture

```
Internet → ALB (port 80) → ECS Fargate (port 8000) → ECR (container images)
                                    ↓
                             CloudWatch Logs
```

## Project Structure

```
├── app/                    # FastAPI application
├── infra/                  # Infrastructure config and task definition
│   ├── task-definition.json
│   └── terraform/          # AWS infrastructure (Terraform)
├── tests/                  # Test suite
├── Dockerfile
├── requirements.txt        # Runtime dependencies
└── requirements-dev.txt    # Dev/test dependencies
```

## Prerequisites

- AWS account with admin access
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.7
- [GitHub CLI](https://cli.github.com/) (`gh`) — logged in via `gh auth login`

## Setup (first-time)

Run once when setting up a new environment:

```bash
# 1. Create GitHub repo
gh repo create <your-org>/calculator-api --public

# 2. Apply infrastructure (VPC, ECS, ALB, ECR, OIDC, IAM deploy role)
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform apply

# 3. Set GitHub Actions secret and workflow permissions
DEPLOY_ROLE=$(terraform -chdir=infra/terraform output -raw deploy_role_arn)
gh secret set AWS_ROLE_ARN --body "$DEPLOY_ROLE" --repo <your-org>/calculator-api
gh api repos/<your-org>/calculator-api/actions/permissions/workflow \
  -X PUT -f default_workflow_permissions=write

# 4. Push code (triggers CI/CD and creates main branch)
git checkout -b main
git remote add origin https://github.com/<your-org>/calculator-api.git
git push -u origin main

```

`terraform apply` creates:
- VPC, subnets, internet gateway
- ECR repository
- ECS cluster, task definition, service
- Application Load Balancer
- CloudWatch log group and alarms
- GitHub OIDC provider in AWS
- IAM role for GitHub Actions (set as `AWS_ROLE_ARN` secret via `gh`)

## CI/CD

| Event | Workflow | Jobs |
|-------|----------|------|
| Pull Request | `ci-cd.yml` | Test → Build → Trivy CVE Scan |
| Merge to main | `ci-cd.yml` | Test → Build → Trivy → Push to ECR → Deploy → Release |
| Manual | `deploy.yml` | Build/push image and update ECS manually |

> **Note:** Terraform is managed locally only — there are no Terraform workflows in CI/CD.

## Manual Deploy

To deploy without going through the CI/CD pipeline (e.g. for hotfixes or first-time image push):

```bash
# 1. Authenticate to AWS
export AWS_PROFILE=<your-profile>   # Linux/macOS
$env:AWS_PROFILE = "<your-profile>" # Windows PowerShell

# 2. Login to ECR
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  <aws-account-id>.dkr.ecr.eu-central-1.amazonaws.com

# 3. Build and push image
REGISTRY=<aws-account-id>.dkr.ecr.eu-central-1.amazonaws.com
docker build -t $REGISTRY/calculator-api:latest .
docker push $REGISTRY/calculator-api:latest

# 4. Deploy to ECS
aws ecs update-service \
  --cluster calculator-api-cluster \
  --service calculator-api-service \
  --force-new-deployment \
  --region eu-central-1
```

Alternatively, trigger the **Build & Deploy** workflow manually from the GitHub Actions tab.

## API Usage

```bash
BASE_URL=http://<alb-dns-name>

# Health check
curl $BASE_URL/health

# Version
curl $BASE_URL/version

# Calculate
curl -X POST $BASE_URL/calculate \
  -H "Content-Type: application/json" \
  -d '{"operation": "add", "a": 10, "b": 5}'

# Available operations: add, sub, mul, div
```

## Known Issues

### GitHub OIDC sub claim format (repos created after 2026-07-15)

GitHub changed the OIDC `sub` claim format for all repositories created after July 15, 2026. New repos emit an immutable format that includes numeric owner/repo IDs:

```
# Old format (repos created before 2026-07-15)
repo:kacperdominik73/calculator-api:ref:refs/heads/main

# New format (repos created after 2026-07-15)
repo:kacperdominik73@<owner-id>/calculator-api@<repo-id>:ref:refs/heads/main
```

The IAM role trust policy in `iam.tf` must use the new format or OIDC authentication will fail with `Not authorized to perform sts:AssumeRoleWithWebIdentity`. Get the IDs with:

```bash
gh api users/<your-org> --jq '.id'           # owner ID
gh api repos/<your-org>/calculator-api --jq '.id'  # repo ID
```

Then set the `sub` condition in `iam.tf` to:

```
repo:<your-org>@<owner-id>/calculator-api@<repo-id>:*
```

## Local Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=app

# Run app locally
uvicorn app.main:app --reload --port 8000
```

# aMeetingFlow

A cloud-native email parsing and meeting automation service built with AWS SAM, Lambda, SES, and Terraform.

This project automates the extraction of meeting details from incoming emails and integrates with AWS services for scalable, secure, and maintainable infrastructure. It is designed for easy deployment, configuration, and teardown using modern DevOps best practices.

# Deployment and Teardown Instructions

## Prerequisites
- AWS CLI installed and configured
- AWS SAM CLI installed
- Terraform installed
- IAM permissions to assume roles and manage resources
## IAM Role Setup for Deployment

Before deploying with Terraform and AWS SAM, you need to create an IAM role that both tools can assume. This role should have:

- A trust policy allowing your IAM user (or group/role) and the AWS CloudFormation service principal (`cloudformation.amazonaws.com`) to assume the role (see example in Deployment Steps).
- Permissions required for deploying and managing resources (see below).

### How to Create the IAM Role

1. **Go to the AWS IAM Console** and create a new role.
2. **Set the trusted entities** (trust policy) as described above.
3. **Attach the following policies to the role:**
   - `AdministratorAccess` (for full access, recommended for development/testing) ***DANGER***
   - Or, for production, a custom policy with permissions for:
     - CloudFormation
     - Lambda
     - IAM (to create/update roles for Lambda)
     - S3 (for SAM deployment artifacts)
     - SES (for email receipt and domain verification)
     - Any other AWS services you use in your stack

**Example minimum permissions for SAM/Terraform deployment:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "iam:PassRole",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "s3:*",
        "ses:*"
      ],
      "Resource": "*"
    }
  ]
}
```

For production, restrict `Resource` to only those resources needed.

Once the role is created, use its ARN in your `samconfig.toml` and trust policy setup as described in the deployment steps.


## Quick Start (Semi-Automated)

For semi-automated setup and deployment using the included Makefile:

```bash
# 1. Set up configuration files from templates
make setup

# 2. Edit sam/samconfig.toml with your settings:
# - Update role_arn with your AWS account number
# - Add resolve_s3 = true for automatic S3 bucket creation
# - Update parameter_overrides with your email source

# 3. Deploy SAM stack first to get Lambda ARN
make sam-deploy

# 4. Edit terraform/terraform.tfvars with:
# - Your domain name (same as in samconfig.toml)
# - AWS account number in assume_role_arn
# - Lambda function ARN from SAM deployment output

# Example configurations:
# sam/samconfig.toml:
# parameter_overrides = "EmailSource=receive@yourdomain.com"
# 
# terraform/terraform.tfvars:
# ses_domain = "yourdomain.com"
# ses_recipient_email = "receive@yourdomain.com"

# 5. Deploy everything (SAM + Terraform)
make deploy

# 6. Add DNS records from Terraform output to your DNS provider:
# - DKIM CNAME records (3 records)
# - DMARC TXT record
# - MX record
# - Domain verification TXT record
```

## Teardown

To destroy all AWS resources and clean up:

```bash
make teardown
```

**After teardown, manually remove DNS records from your DNS provider:**
- Delete the 3 DKIM CNAME records
- Delete the DMARC TXT record
- Delete the MX record
- Delete the domain verification TXT record

## Day/Night Control

To control when the system processes emails:

```bash
# Turn off email processing at night
make deactivate

# Turn on email processing in the morning
make activate
```

This allows you to disable email processing during off-hours while keeping the infrastructure running.

## Updating Lambda Function

After successful initial deployment, to update the Lambda function code:

```bash
# 1. Edit your code in src/lambda_function.py
# 2. Deploy changes
make deploy
```

## Available Makefile Targets

### Setup and Teardown
- `make setup` - Copy configuration templates and set up project
- `make teardown` - Destroy all AWS resources and clean up configuration
- `make activate` - Activate email processing (turn on for day)
- `make deactivate` - Deactivate email processing (turn off for night)

### Development
- `make install` - Install development dependencies (ruff, mypy)
- `make format` - Format code with ruff
- `make lint` - Run linting and type checking
- `make fix` - Auto-fix issues and format code
- `make check` - Run all validation checks

### SAM Deployment
- `make build` - Build SAM application (includes linting)
- `make sam-deploy` - Deploy SAM stack
- `make sam-force-deploy` - Force redeploy SAM stack

### Terraform Deployment
- `make terraform-plan` - Show Terraform changes
- `make terraform-apply` - Apply Terraform changes (with confirmation)
- `make terraform-auto-deploy` - Apply Terraform changes (no confirmation)

### Combined Deployment
- `make deploy` - Full deployment (SAM + Terraform, automated)

## Manual Deployment

For detailed manual deployment steps and troubleshooting, see [docs/manual-deployment.md](docs/manual-deployment.md).

## Troubleshooting
- If you see an S3 bucket error, run `sam deploy --guided` to set up the bucket.
- If you get a role assumption error, check your IAM trust policy and permissions.
- Environment variables set for role assumption only affect the current shell session.

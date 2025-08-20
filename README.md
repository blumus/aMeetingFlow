# aMeetingFlow

A cloud-native email parsing and meeting automation service built with AWS SAM, Lambda, SES, and Terraform.

This project automates the extraction of meeting details from incoming emails and integrates with AWS services for scalable, secure, and maintainable infrastructure. It is designed for easy deployment, configuration, and teardown using modern DevOps best practices.

# Deployment and Teardown Instructions

## Quick Start (Automated)

For automated deployment using the included Makefile:

```bash
# Run all checks (linting, validation)
make check

# Deploy everything (SAM + Terraform)
make deploy
```

## Available Makefile Targets

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

## Manual Deployment (Alternative)

If you prefer manual deployment or need more control:

## Prerequisites
-
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
- AWS CLI installed and configured
- AWS SAM CLI installed
- Terraform installed
- IAM permissions to assume roles and manage resources

## Manual Deployment Steps

**Note:** You can use `make deploy` for automated deployment after configuration. The manual steps below are provided for reference and troubleshooting.

### 0. IAM Role Trust Policy Setup (Best Practice)


To allow both Terraform and AWS SAM to assume the deployment role automatically, set the IAM role's trust policy to include both your IAM user (or role) and the AWS CloudFormation service principal. Replace the example ARN below with your actual IAM user or role ARN:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/example-deployment-user"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudformation.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Explanation:**
- Replace `arn:aws:iam::123456789012:user/example-deployment-user` with your actual IAM user or role ARN that Terraform uses for deployment.
- The CloudFormation service principal (`cloudformation.amazonaws.com`) is required for AWS SAM deployments.

This enables Terraform to assume the role as your IAM user or role, and SAM to assume the role via CloudFormation.

### 1. Configure SAM

- Copy the template config:
  ```bash
  cp sam/samconfig.toml.template sam/samconfig.toml
  ```
- Edit `sam/samconfig.toml` as needed (stack name, region, etc.).
- To allow SAM to assume your deployment role automatically, set the `role_arn` parameter in `sam/samconfig.toml`:
  ```toml
  role_arn = "arn:aws:iam::your_aws_account_number:role/YourDeploymentRole"
  ```
  Replace `your_aws_account_number` and `YourDeploymentRole` with your actual AWS account number and role name. This should match the role you configured in the IAM trust policy above.
- Run `sam deploy --guided` for the first deployment to set up the S3 bucket. Future deployments will use the bucket saved in `samconfig.toml`.

### 2. Deploy SAM

- Build SAM:
  ```bash
  cd sam
  sam build
  ```
- Deploy SAM:
  ```bash
  sam deploy
  ```

### 3. Configure Terraform

- Copy the template tfvars:
  ```bash
  cd ../terraform
  cp terraform.tfvars.template terraform.tfvars
  ```
- Edit `terraform.tfvars` with your domain, email, AWS region, and Lambda ARN.
- Set `assume_role_arn` to your deployment role ARN, using `your_aws_account_number` as a placeholder. Example:
  ```hcl
  assume_role_arn     = "arn:aws:iam::your_aws_account_number:role/ExampleTerraformRole"
  lambda_function_arn = "arn:aws:lambda:eu-west-1:your_aws_account_number:function:example_lambda"
  ```

### 4. Deploy Terraform

- Deploy Terraform:
  ```bash
  terraform apply -var-file=terraform.tfvars
  ```

### 5. DNS Setup

After running `terraform apply`, you will see outputs similar to:

```
dkim_cname_dns_records = [
  {
    "name" = "<dkim-token-1>._domainkey.<your-domain>"
    "type" = "CNAME"
    "value" = "<dkim-token-1>.dkim.amazonses.com"
  },
  {
    "name" = "<dkim-token-2>._domainkey.<your-domain>"
    "type" = "CNAME"
    "value" = "<dkim-token-2>.dkim.amazonses.com"
  },
  {
    "name" = "<dkim-token-3>._domainkey.<your-domain>"
    "type" = "CNAME"
    "value" = "<dkim-token-3>.dkim.amazonses.com"
  },
]
dmarc_dns_record = {
  "name" = "_dmarc.<your-domain>"
  "type" = "TXT"
  "value" = "v=DMARC1; p=none;"
}
```

**Add these DNS records to your DNS provider:**
- For each DKIM CNAME record, create a CNAME record with the given name and value.
- For DMARC, create a TXT record with the given name and value.

This enables DKIM signing and DMARC policy for your domain. Do not use the sample values above; use the actual values output by Terraform for your deployment.

### 6. Check Verification

- Use AWS CLI to check SES domain and DKIM verification:
  ```bash
  aws ses get-identity-verification-attributes --identities <your-domain>
  aws ses get-identity-dkim-attributes --identities <your-domain>
  ```

---

## Undo/Teardown Steps

### Option 1: Manual Teardown

- Delete SAM stack:
  ```bash
  cd sam
  sam delete
  ```
- Destroy Terraform resources:
  ```bash
  cd terraform
  terraform destroy -var-file=terraform.tfvars
  ```

### Option 2: Using Terraform Only

If you used `make deploy`, you can destroy Terraform resources with:
```bash
cd terraform
terraform destroy -var-file=terraform.tfvars
```

Note: SAM stack deletion still needs to be done manually as shown above.

### Continue with cleanup:

- Remove configuration files:
  ```bash
  rm terraform/terraform.tfvars
  rm sam/samconfig.toml
  ```

### 2. Remove DNS Records

- Delete DKIM CNAME, and DMARC TXT records from your DNS provider.

### 3. Unset Temporary AWS Credentials

- Run:
  ```bash
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY
  unset AWS_SESSION_TOKEN
  ```

## Troubleshooting
- If you see an S3 bucket error, run `sam deploy --guided` to set up the bucket.
- If you get a role assumption error, check your IAM trust policy and permissions.
- Environment variables set for role assumption only affect the current shell session.

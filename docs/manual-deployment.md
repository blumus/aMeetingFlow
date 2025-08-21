# Manual Deployment Guide

This guide provides detailed manual deployment steps for users who prefer more control over the deployment process or need to troubleshoot issues.

**Note:** For most users, the automated `make deploy` approach in the main README is recommended.

## Manual Deployment Steps

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

## Manual Teardown Steps

### Option 1: Complete Manual Teardown

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

### Remove DNS Records

- Delete DKIM CNAME, and DMARC TXT records from your DNS provider.

## Troubleshooting

- If you see an S3 bucket error, run `sam deploy --guided` to set up the bucket.
- If you get a role assumption error, check your IAM trust policy and permissions.
- Environment variables set for role assumption only affect the current shell session.
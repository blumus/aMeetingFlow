# Output Lambda function ARN for use in other systems
output "lambda_function_arn" {
  value = local.lambda_function_arn
  description = "The ARN of the Lambda function for SES invocation."
}
# SES Domain Verification Output (TXT record)
output "ses_domain_identity_verification_token" {
  value = aws_ses_domain_identity.example_domain.verification_token
  description = "TXT record value for SES domain verification"
}

# SES DKIM CNAME records
resource "aws_ses_domain_dkim" "dkim" {
  domain = var.ses_domain
}

output "ses_domain_dkim_tokens" {
  value = aws_ses_domain_dkim.dkim.dkim_tokens
  description = "CNAME record values for SES DKIM verification"
}
# Sensitive value variables
variable "ses_domain" {
  description = "SES domain to verify and use for email receipt"
  type        = string
}

variable "ses_recipient_email" {
  description = "SES recipient email address for receipt rule"
  type        = string
}

variable "aws_account" {
  description = "AWS account ID"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
  default     = "email_parser"
}

locals {
  lambda_function_arn = "arn:aws:lambda:${var.aws_region}:${var.aws_account}:function:${var.lambda_function_name}"
}
# This file provisions the foundational AWS infrastructure using Terraform.
# It sets up the S3 bucket for SAM artifacts, the IAM role for the Lambda
# function, and the SES configuration to trigger the function.


# Parameterize AWS region
variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "eu-west-1"
}

# Configure the AWS provider
provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# AWS S3 Bucket for SAM Deployment Artifacts
# This bucket is used by the AWS SAM CLI to store packaged application code.
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "sam_artifacts_bucket" {
  bucket = "email-parser-sam-artifacts-${random_pet.bucket_name.id}"
  # Prevent accidental deletion of the bucket
  force_destroy = false
  tags = {
    Name = "Email Parser SAM Artifacts"
  }
  depends_on = [random_pet.bucket_name]
}

# Generate a unique suffix for the bucket name to avoid conflicts
resource "random_pet" "bucket_name" {
  length = 2
}

# -----------------------------------------------------------------------------
# AWS IAM Role for Lambda Execution
# This role grants the necessary permissions for the Lambda function to run,
# be invoked by SES, and write logs to CloudWatch.
# -----------------------------------------------------------------------------
resource "aws_iam_role" "email_parser_lambda_role" {
  name = "email_parser_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
      }
    ]
  })
}

# Attach a policy to the role to allow Lambda to write logs to CloudWatch
resource "aws_iam_role_policy" "lambda_logging_policy" {
  name = "lambda_logging_policy"
  role = aws_iam_role.email_parser_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
  depends_on = [aws_iam_role.email_parser_lambda_role]
}

# -----------------------------------------------------------------------------
# AWS SES Configuration
# This sets up the domain identity and the receipt rule to trigger the Lambda.
# You must first verify your domain or email identity in AWS SES.
# -----------------------------------------------------------------------------
resource "aws_ses_domain_identity" "example_domain" {
  domain = var.ses_domain
}

resource "aws_ses_receipt_rule_set" "main_rule_set" {
  rule_set_name = "main-rule-set"
}

resource "aws_ses_receipt_rule" "email_parser_rule" {
  name          = "email-parser-rule"
  rule_set_name = aws_ses_receipt_rule_set.main_rule_set.rule_set_name
  recipients    = [var.ses_recipient_email]

  lambda_action {
    function_arn = local.lambda_function_arn
    position     = 1
    topic_arn    = ""
    invocation_type = "Event"
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set, aws_iam_role.email_parser_lambda_role]
}

# -----------------------------------------------------------------------------
# Output important values for the SAM deployment
# -----------------------------------------------------------------------------
output "lambda_iam_role_arn" {
  value = aws_iam_role.email_parser_lambda_role.arn
  description = "The ARN of the IAM role for the Lambda function."
}

output "sam_artifacts_bucket_name" {
  value = aws_s3_bucket.sam_artifacts_bucket.bucket
  description = "The name of the S3 bucket for SAM artifacts."
}

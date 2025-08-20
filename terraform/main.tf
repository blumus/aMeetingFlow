# This file provisions the foundational AWS infrastructure using Terraform.
# It sets up the S3 bucket for SAM artifacts, the IAM role for the Lambda
# function, and the SES configuration to trigger the function.

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "eu-west-1"
}

variable "ses_domain" {
  description = "SES domain to verify and use for email receipt"
  type        = string
}

variable "ses_recipient_email" {
  description = "SES recipient email address for receipt rule"
  type        = string
}

variable "assume_role_arn" {
  description = "The ARN of the IAM role to assume for Terraform operations"
  type        = string
}

variable "lambda_function_arn" {
  description = "The ARN of the Lambda function deployed by SAM. Copy this from the SAM deployment output."
  type        = string
}

variable "sam_stack_name" {
  description = "Name of the SAM stack to import S3 bucket from"
  type        = string
  default     = "meeting-automation-service"
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  common_tags = {
    Project    = "meeting-automation-service"
    DeployedBy = "terraform"
  }
}

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "TerraformSession"
  }

  default_tags {
    tags = local.common_tags
  }
}

# =============================================================================
# DATA SOURCES
# =============================================================================

# Import S3 bucket created by SAM
data "aws_cloudformation_export" "email_storage_bucket" {
  name = "${var.sam_stack_name}-EmailStorageBucketName"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# =============================================================================
# RESOURCES
# =============================================================================

# S3 Event Notification to trigger Lambda when email arrives
resource "aws_s3_bucket_notification" "email_notification" {
  bucket = data.aws_cloudformation_export.email_storage_bucket.value

  lambda_function {
    lambda_function_arn = var.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.s3_invoke_lambda]
}

# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "s3_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${data.aws_cloudformation_export.email_storage_bucket.value}"
}

# AWS SES Configuration
# This sets up the domain identity and the receipt rule to store emails in S3.
resource "aws_ses_domain_identity" "meeting_flow_domain" {
  domain = var.ses_domain
}

resource "aws_ses_domain_dkim" "dkim" {
  domain = var.ses_domain
}

resource "aws_ses_receipt_rule_set" "main_rule_set" {
  rule_set_name = "main-rule-set"
}

resource "aws_ses_receipt_rule" "email_parser_rule" {
  name          = "email-parser-rule"
  rule_set_name = aws_ses_receipt_rule_set.main_rule_set.rule_set_name
  recipients    = [var.ses_recipient_email]
  enabled       = true

  s3_action {
    bucket_name = data.aws_cloudformation_export.email_storage_bucket.value
    position    = 1
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set]
}

# Activate the SES receipt rule set after apply
resource "null_resource" "activate_rule_set" {
  provisioner "local-exec" {
    command = "aws ses set-active-receipt-rule-set --rule-set-name main-rule-set || exit 1"
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set]
}

# Tag SES domain identity using SES v2 API (workaround for Terraform provider limitation)
resource "null_resource" "tag_ses_domain" {
  provisioner "local-exec" {
    command = "aws sesv2 tag-resource --resource-arn arn:aws:ses:${var.aws_region}:${data.aws_caller_identity.current.account_id}:identity/${var.ses_domain} --tags Key=Project,Value=${local.common_tags.Project} Key=DeployedBy,Value=${local.common_tags.DeployedBy} || exit 1"
  }
  depends_on = [aws_ses_domain_identity.meeting_flow_domain]
}

# =============================================================================
# OUTPUTS
# =============================================================================

# Output Lambda function ARN for use in other systems
output "lambda_function_arn" {
  value       = var.lambda_function_arn
  description = "The ARN of the Lambda function for SES invocation."
}

# SES Domain Verification Output (TXT record)
output "ses_domain_identity_verification_token" {
  value       = aws_ses_domain_identity.meeting_flow_domain.verification_token
  description = "TXT record value for SES domain verification"
}

# SES DKIM CNAME records
output "ses_domain_dkim_tokens" {
  value       = aws_ses_domain_dkim.dkim.dkim_tokens
  description = "CNAME record values for SES DKIM verification"
}

output "dkim_cname_dns_records" {
  value = [
    for token in aws_ses_domain_dkim.dkim.dkim_tokens : {
      type  = "CNAME"
      name  = "${token}._domainkey.${var.ses_domain}"
      value = "${token}.dkim.amazonses.com"
    }
  ]
  description = "DNS CNAME records for SES DKIM. Add these to your DNS."
}

# DMARC DNS record output
output "dmarc_dns_record" {
  value = {
    type  = "TXT"
    name  = "_dmarc.${var.ses_domain}"
    value = "v=DMARC1; p=none;"
  }
  description = "DNS record for DMARC policy. Add this TXT record to your DNS."
}

# Output for SES MX record DNS configuration
output "ses_mx_record" {
  description = "Add this MX record to your DNS to enable SES email receiving."
  value = {
    name     = "${var.ses_domain}"
    type     = "MX"
    priority = 10
    value    = "inbound-smtp.${var.aws_region}.amazonaws.com"
  }
}

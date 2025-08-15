# Output Lambda function ARN for use in other systems
output "lambda_function_arn" {
  value = var.lambda_function_arn
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
# Sensitive value variables
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

    assume_role {
      role_arn     = var.assume_role_arn
      session_name = "TerraformSession"
    }
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
    function_arn = var.lambda_function_arn
    position     = 1
    topic_arn    = ""
    invocation_type = "Event"
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set]
}

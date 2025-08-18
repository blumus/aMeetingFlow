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

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "TerraformSession"
  }
}

# =============================================================================
# RESOURCES
# =============================================================================

# AWS SES Configuration
# This sets up the domain identity and the receipt rule to trigger the Lambda.
# You must first verify your domain or email identity in AWS SES.
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

  lambda_action {
    function_arn    = var.lambda_function_arn
    position        = 1
    topic_arn       = ""
    invocation_type = "Event"
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set]
}

# Activate the SES receipt rule set after apply
resource "null_resource" "activate_rule_set" {
  provisioner "local-exec" {
    command = "aws ses set-active-receipt-rule-set --rule-set-name main-rule-set"
  }
  depends_on = [aws_ses_receipt_rule_set.main_rule_set]
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

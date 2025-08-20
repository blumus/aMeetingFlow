# Meeting Automation Service - Development Commands

# Default target - show help
help:
	@echo "📋 Available commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make setup     - Set up configuration files"
	@echo "  make deploy    - Deploy everything (SAM + Terraform)"
	@echo "  make teardown  - Destroy all resources"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make install   - Install dev dependencies"
	@echo "  make check     - Run all validation checks"
	@echo "  make format    - Format code"
	@echo "  make lint      - Run linting"
	@echo ""
	@echo "☁️  Deployment:"
	@echo "  make sam-deploy       - Deploy SAM only"
	@echo "  make terraform-plan   - Show Terraform changes"
	@echo "  make terraform-apply  - Apply Terraform changes"
	@echo ""
	@echo "🌙 Day/Night Control:"
	@echo "  make activate    - Turn on email processing"
	@echo "  make deactivate  - Turn off email processing"
	@echo ""
	@echo "📊 Status:"
	@echo "  make check-deploy - Check deployment status"

default: help

# Install development dependencies
install:
	@pip install ruff mypy

# Format code
format:
	@ruff format src/

# Lint code (must pass before build)
lint:
	@ruff check src/
	@mypy src/

# Fix auto-fixable issues and format
fix:
	@ruff check --fix src/
	@ruff format src/

# Validate SAM template
validate:
	@cd sam && sam validate

# Validate SAM template with linting
validate-lint:
	@cd sam && sam validate --lint

# Build SAM (runs lint first)
build: lint validate-lint
	@cd sam && sam build

# SAM Deploy (runs lint → build → deploy SAM only)
sam-deploy: build
	@cd sam && sam deploy --no-confirm-changeset

# Force SAM Deploy (redeploys even if no changes)
sam-force-deploy: build
	@cd sam && sam deploy --no-confirm-changeset --force-upload

# Terraform Format (formats .tf files)
terraform-fmt:
	@cd terraform && terraform fmt

# Terraform Validate (validates configuration)
terraform-validate:
	@cd terraform && terraform validate

# Terraform Plan (shows what changes will be made)
terraform-plan:
	@cd terraform && terraform plan -var-file=terraform.tfvars

# Terraform Apply (applies changes with confirmation)
terraform-apply:
	@cd terraform && terraform apply -var-file=terraform.tfvars

# Terraform Deploy (runs plan then apply with confirmation)
terraform-deploy: terraform-plan terraform-apply

# Terraform Auto Deploy (runs plan and apply without confirmation)
terraform-auto-deploy: terraform-plan
	@echo "⚠️  Auto-applying Terraform changes without confirmation"
	@cd terraform && terraform apply -auto-approve -var-file=terraform.tfvars

# Combined Deploy (runs lint → build → deploy SAM → deploy Terraform)
deploy: build
	@cd sam && sam deploy --no-confirm-changeset 2>sam_error.log; error=$$?; \
	if [ $$error -ne 0 ]; then \
		if grep -q "No changes to deploy" sam_error.log; then \
			echo "SAM: No changes detected, continuing to Terraform..."; \
		else \
			cat sam_error.log; rm -f sam_error.log; exit $$error; \
		fi; \
	fi; \
	rm -f sam_error.log
	@$(MAKE) terraform-auto-deploy

# Setup automation (copy templates and configure)
setup:
	@echo "🔧 Setting up project configuration..."
	@if [ ! -f sam/samconfig.toml ]; then \
		cp sam/samconfig.toml.template sam/samconfig.toml; \
		echo "✅ Created sam/samconfig.toml from template"; \
	else \
		echo "⚠️  sam/samconfig.toml already exists, skipping"; \
	fi
	@if [ ! -f terraform/terraform.tfvars ]; then \
		cp terraform/terraform.tfvars.template terraform/terraform.tfvars; \
		echo "✅ Created terraform/terraform.tfvars from template"; \
	else \
		echo "⚠️  terraform/terraform.tfvars already exists, skipping"; \
	fi
	@echo "📝 Please edit sam/samconfig.toml and terraform/terraform.tfvars with your settings"

# Teardown automation (destroy infrastructure and clean up)
teardown:
	@echo "🗑️  Tearing down infrastructure..."
	@echo "⚠️  This will destroy all AWS resources. Press Ctrl+C to cancel."
	@sleep 5
	@set -e; \
	terraform_success=false; \
	sam_success=false; \
	echo "🧹 Emptying S3 buckets first..."; \
	aws s3 rm s3://meeting-automation-service-email-storage --recursive 2>/dev/null || echo "Email storage bucket not found or already empty"; \
	echo "🚫 Deactivating SES rule set..."; \
	aws ses set-active-receipt-rule-set 2>/dev/null || echo "No active rule set to deactivate"; \
	echo "🔄 Destroying Terraform resources..."; \
	if [ -f terraform/terraform.tfvars ]; then \
		if (cd terraform && terraform destroy -auto-approve -var-file=terraform.tfvars); then \
			terraform_success=true; \
		fi; \
	else \
		echo "terraform.tfvars not found, skipping Terraform destroy"; \
		terraform_success=true; \
	fi; \
	echo "🔄 Deleting SAM stack..."; \
	if [ -f sam/samconfig.toml ]; then \
		if (cd sam && sam delete --no-prompts); then \
			sam_success=true; \
		fi; \
	else \
		echo "sam/samconfig.toml not found, skipping SAM delete"; \
		sam_success=true; \
	fi; \
	if [ "$$terraform_success" = "true" ] && [ "$$sam_success" = "true" ]; then \
		echo "🧹 Cleaning up configuration files..."; \
		rm -f sam/samconfig.toml terraform/terraform.tfvars; \
		echo "✅ Teardown complete"; \
		echo "📝 Don't forget to manually remove DNS records from your DNS provider:"; \
		echo "   - Delete the 3 DKIM CNAME records"; \
		echo "   - Delete the DMARC TXT record"; \
		echo "   - Delete the MX record"; \
		echo "   - Delete the domain verification TXT record"; \
	else \
		echo "⚠️  Teardown completed with errors. Config files preserved for retry."; \
	fi

# Activate email processing (turn on for day)
activate:
	@echo "🔆 Activating email processing..."
	@aws ses set-active-receipt-rule-set --rule-set-name main-rule-set
	@echo "✅ Email processing activated"

# Deactivate email processing (turn off for night)
deactivate:
	@echo "🚫 Deactivating email processing..."
	@aws ses set-active-receipt-rule-set
	@echo "✅ Email processing deactivated"

# Check deployment status
check-deploy:
	@echo "🔍 Checking deployment status..."
	@domain=$$(grep ses_domain terraform/terraform.tfvars | cut -d'"' -f2); \
	echo "📧 SES Domain Verification:"; \
	status=$$(aws ses get-identity-verification-attributes --identities $$domain --query 'VerificationAttributes.*.VerificationStatus' --output text 2>/dev/null || echo "Failed"); \
	echo "  Status: $$status"; \
	if [ "$$status" = "Pending" ]; then \
		token=$$(aws ses get-identity-verification-attributes --identities $$domain --query 'VerificationAttributes.*.VerificationToken' --output text 2>/dev/null); \
		echo "  📝 DNS TXT record: $$domain = \"$$token\""; \
	fi; \
	echo "🔐 SES DKIM Verification:"; \
	dkim_status=$$(aws ses get-identity-dkim-attributes --identities $$domain --query 'DkimAttributes.*.DkimVerificationStatus' --output text 2>/dev/null || echo "Failed"); \
	echo "  Status: $$dkim_status"; \
	if [ "$$dkim_status" = "Pending" ]; then \
		echo "  📝 DNS CNAME records:"; \
		aws ses get-identity-dkim-attributes --identities $$domain --query 'DkimAttributes.*.DkimTokens[]' --output text 2>/dev/null | while read token; do \
			echo "    $$token._domainkey.$$domain = $$token.dkim.amazonses.com"; \
		done; \
	fi; \
	echo "⚡ Lambda Function:"; \
	email_source=$$(aws lambda get-function --function-name email_parser --query 'Configuration.Environment.Variables.EMAIL_SOURCE' --output text 2>/dev/null || echo "Failed"); \
	echo "  EMAIL_SOURCE: $$email_source"; \
	echo "📬 Email Processing:"; \
	active_ruleset=$$(aws ses describe-active-receipt-rule-set --query 'Metadata.Name' --output text 2>/dev/null || echo "None"); \
	if [ "$$active_ruleset" = "main-rule-set" ]; then \
		echo "  Status: 🔆 ACTIVE (processing emails)"; \
	elif [ "$$active_ruleset" = "None" ]; then \
		echo "  Status: 🚫 INACTIVE (not processing emails)"; \
	else \
		echo "  Status: ⚠️  Unknown rule set: $$active_ruleset"; \
	fi; \
	echo "✅ Deployment status check complete"

# Run all checks
check: lint validate-lint terraform-validate
	@echo "🔍 Checking Makefile syntax..."
	@make --dry-run --silent > /dev/null && echo "✅ Makefile syntax OK" || (echo "❌ Makefile syntax error" && exit 1)
	@echo "✅ All checks passed!"

.PHONY: help default install format lint fix validate validate-lint build sam-deploy sam-force-deploy terraform-fmt terraform-validate terraform-plan terraform-apply terraform-deploy terraform-auto-deploy deploy setup teardown activate deactivate check-deploy check
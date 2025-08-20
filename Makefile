# Meeting Automation Service - Development Commands

# Install development dependencies
install:
	pip install ruff mypy

# Format code
format:
	ruff format src/

# Lint code (must pass before build)
lint:
	ruff check src/
	mypy src/

# Fix auto-fixable issues and format
fix:
	ruff check --fix src/
	ruff format src/

# Validate SAM template
validate:
	cd sam && sam validate

# Validate SAM template with linting
validate-lint:
	cd sam && sam validate --lint

# Build SAM (runs lint first)
build: lint validate-lint
	cd sam && sam build

# SAM Deploy (runs lint → build → deploy SAM only)
sam-deploy: build
	cd sam && sam deploy --no-confirm-changeset

# Force SAM Deploy (redeploys even if no changes)
sam-force-deploy: build
	cd sam && sam deploy --no-confirm-changeset --force-upload

# Terraform Format (formats .tf files)
terraform-fmt:
	cd terraform && terraform fmt

# Terraform Validate (validates configuration)
terraform-validate:
	cd terraform && terraform validate

# Terraform Plan (shows what changes will be made)
terraform-plan:
	cd terraform && terraform plan -var-file=terraform.tfvars

# Terraform Apply (applies changes with confirmation)
terraform-apply:
	cd terraform && terraform apply -var-file=terraform.tfvars

# Terraform Deploy (runs plan then apply with confirmation)
terraform-deploy: terraform-plan terraform-apply

# Terraform Auto Deploy (runs plan and apply without confirmation)
terraform-auto-deploy: terraform-plan
	@echo "⚠️  Auto-applying Terraform changes without confirmation"
	cd terraform && terraform apply -auto-approve -var-file=terraform.tfvars

# Combined Deploy (runs lint → build → deploy SAM → deploy Terraform)
deploy: build
	cd sam && sam deploy --no-confirm-changeset 2>sam_error.log; error=$$?; \
	if [ $$error -ne 0 ]; then \
		if grep -q "No changes to deploy" sam_error.log; then \
			echo "SAM: No changes detected, continuing to Terraform..."; \
		else \
			cat sam_error.log; rm -f sam_error.log; exit $$error; \
		fi; \
	fi; \
	rm -f sam_error.log
	$(MAKE) terraform-auto-deploy

# Run all checks
check: lint validate-lint terraform-validate
	@echo "✅ All checks passed!"

.PHONY: install format lint fix validate validate-lint build sam-deploy sam-force-deploy terraform-fmt terraform-validate terraform-plan terraform-apply terraform-deploy terraform-auto-deploy deploy check
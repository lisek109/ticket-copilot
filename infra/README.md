# Azure (Terraform) - Container Apps deployment

## Prereqs
- Azure subscription
- Azure CLI: `az login`
- Terraform

## Deploy
From `infra/`:

1) Init
```bash
terraform init
Plan

terraform plan -out tfplan
Apply

terraform apply tfplan
```

Push Docker image to ACR
After apply, Terraform outputs acr_login_server.

Example flow:

az acr login --name <acrName>

docker tag ticket-email-copilot-api:latest <loginServer>/ticket-email-copilot-api:latest

docker push <loginServer>/ticket-email-copilot-api:latest

Then set container_image in terraform.tfvars (or keep default :latest) and re-apply.
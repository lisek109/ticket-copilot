
locals {
  acr_name = "${replace(lower(var.prefix), "/[^a-z0-9]/", "")}projectacr"
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# Logs for Container Apps (recommended)
resource "azurerm_log_analytics_workspace" "law" {
  name                = "${var.prefix}-law"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "cae" {
  name                       = "${var.prefix}-cae"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
}

# Container Registry to store our Docker image
resource "azurerm_container_registry" "acr" {
  name                = "${var.prefix}projectacr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true # Simple for MVP; switch to managed identity later
}

# Container App running the API
resource "azurerm_container_app" "api" {
  name                         = local.acr_name
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  # Public ingress: exposes the app on HTTPS
  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    #Added that but dont know why it needs to be here if revision_mode = "Single". Azure requires it.
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  template {
    container {
      name   = "api"
      image  = var.container_image != "" ? var.container_image : "${azurerm_container_registry.acr.login_server}/ticket-email-copilot-api:latest"
      cpu    = 0.5
      memory = "1Gi"

      # Example env vars (add more later)
      env {
        name  = "FAISS_DIR"
        value = "faiss_store"
      }
    }

    min_replicas = 0
    max_replicas = 1
  }
}

# Budget + notification on the RESOURCE GROUP 
# Note: notifications trigger emails when thresholds are exceeded. :contentReference[oaicite:2]{index=2}
resource "azurerm_consumption_budget_resource_group" "budget" {
  name              = "${var.prefix}-rg-budget"
  resource_group_id = azurerm_resource_group.rg.id
  amount            = var.budget_amount_eur
  time_grain        = "Monthly"

  time_period {
    start_date = "2026-02-01T00:00:00Z"
    # end_date is optional-- omit for ongoing budget
  }

  notification {
    enabled        = true
    threshold      = 80.0
    operator       = "GreaterThan"
    threshold_type = "Actual"

    contact_emails = var.budget_email != "" ? [var.budget_email] : []
  }

  notification {
    enabled        = true
    threshold      = 100.0
    operator       = "GreaterThan"
    threshold_type = "Actual"

    contact_emails = var.budget_email != "" ? [var.budget_email] : []
  }
}

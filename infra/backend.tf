terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-weu"
    storage_account_name = "stticketcopilottfstate"
    container_name       = "tfstate"
    key                  = "ticket-email-copilot.tfstate"
  }
}

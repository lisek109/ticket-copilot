output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  value = azurerm_container_registry.acr.admin_username
}

output "container_app_latest_revision_fqdn" {
  # Terraform exposes the latest revision FQDN. :contentReference[oaicite:3]{index=3}
  value = azurerm_container_app.api.latest_revision_fqdn
}

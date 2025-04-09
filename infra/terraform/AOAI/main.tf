resource "azurerm_cognitive_account" "aoai" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  kind     = "OpenAI"
  sku_name = var.sku_name

}

resource "azurerm_cognitive_deployment" "model" {
  for_each = var.deployments

  name                 = each.value.deployment_name
  cognitive_account_id = azurerm_cognitive_account.aoai.id

  model {
    format  = "OpenAI"
    name    = each.value.model_name
    version = each.value.model_version
  }

  sku {
    name = each.value.scale_type  # e.g. "Standard"
  }
}

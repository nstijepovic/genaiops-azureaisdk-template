resource "random_string" "aoai_suffix" {
  for_each = var.azure_openai

  length  = 7
  lower   = true
  numeric = true
  upper   = false
  special = false
}

module "aoai" {
  for_each            = var.azure_openai
  source              = "./AOAI"
  name                = "aoai-${each.key}-${random_string.aoai_suffix[each.key].result}"
  location            = var.resource_group_location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = each.value.sku_name

  deployments         = lookup(var.azure_openai_deployments, each.key, {})
}

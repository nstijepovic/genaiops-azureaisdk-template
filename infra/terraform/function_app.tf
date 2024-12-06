resource "azurerm_storage_account" "simpleapp_storage" {
  name                     = "simpleappstorageaccount"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_application_insights" "ai" {
  name                = "${azurerm_resource_group.rg.name}ai"
  location            =azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}


// we will use consumption plan
resource "azurerm_service_plan" "simpleapp_service_plan" {
  name                = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku_name            = "P0v3"
  os_type             = "Linux"
}
resource "azurerm_linux_function_app" "simpleapp_app" {
  name                        = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  service_plan_id             = azurerm_service_plan.simpleapp_service_plan.id
  storage_account_name        = azurerm_storage_account.simpleapp_storage.name
  storage_uses_managed_identity  = true
  functions_extension_version = "~4"
  https_only                  = true
  identity {
    type = "SystemAssigned"
  }
  site_config {
    application_stack {
      node_version = 20
    }
  }
  app_settings = {
    APPLICATIONINSIGHTS_CONNECTION_STRING = "${azurerm_application_insights.ai.connection_string}"
  }
  // Ignore changes to these app settings to prevent Terraform from overwriting them
  // after the function app code is deployed. These settings reference the code location.
  lifecycle { 
    ignore_changes = [      app_settings["WEBSITE_RUN_FROM_PACKAGE"], 
      app_settings["WEBSITE_ENABLE_SYNC_UPDATE_SITE"]
    ] 
  }
}

resource "azurerm_role_assignment" "function_app_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.simpleapp_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.simpleapp_app.identity.0.principal_id
}



output "simpleapp_app_url" {
  value = azurerm_linux_function_app.simpleapp_app.default_hostname
}
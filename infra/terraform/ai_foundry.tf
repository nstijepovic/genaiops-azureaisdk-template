
resource "random_pet" "rg_name" { 
  prefix = var.resource_group_name_prefix
}

// RESOURCE GROUP
resource "azurerm_resource_group" "rg" {
  location = var.resource_group_location
  name     = random_pet.rg_name.id
}

data "azurerm_client_config" "current" {
}

// STORAGE ACCOUNT
resource "azurerm_storage_account" "default" {
  name                            = "${var.prefix}storage${random_string.suffix.result}"
  location                        = azurerm_resource_group.rg.location
  resource_group_name             = azurerm_resource_group.rg.name
  account_tier                    = "Standard"
  account_replication_type        = "GRS"
  allow_nested_items_to_be_public = false
}

// KEY VAULT
resource "azurerm_key_vault" "default" {
  name                     = "${var.prefix}keyvault${random_string.suffix.result}"
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = false
}

resource "azurerm_application_insights" "default" {
  name                = "${var.prefix}appinsights${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

// CONTAINER REGISTRY
resource "azurerm_container_registry" "default" {
  name                     = "${var.prefix}contreg${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  sku                      = "Standard"
  admin_enabled            = true
}

resource "azapi_resource" "AIServicesResource" {
  type = "Microsoft.CognitiveServices/accounts@2024-10-01"
  name = "AIServicesResourcecustom"
  location = azurerm_resource_group.rg.location
  parent_id = azurerm_resource_group.rg.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    name = "AIServicesResourcecustom"
    kind = "AIServices"
    sku = {
      name = var.sku
    }
    properties = {
      customSubDomainName = "${random_pet.rg_name.id}domain"
      apiProperties = {
        statisticsEnabled = false
      }
    }
  }

  response_export_values = ["*"]
}

// Azure AI Hub
resource "azapi_resource" "hub" {
  type = "Microsoft.MachineLearningServices/workspaces@2024-07-01-preview"
  name = "${random_pet.rg_name.id}-aih"
  location = azurerm_resource_group.rg.location
  parent_id = azurerm_resource_group.rg.id

  identity {
    type = "SystemAssigned"
  }

body = {
    properties = {
      description = "This is my Azure AI hub"
      friendlyName = "My Hub"
      storageAccount = azurerm_storage_account.default.id
      keyVault = azurerm_key_vault.default.id
      applicationInsights = azurerm_application_insights.default.id
      containerRegistry = azurerm_container_registry.default.id
      systemDatastoresAuthMode = var.data_storage_access_type
    }
    kind = "hub"
}
}

// Azure AI Project
resource "azapi_resource" "project" {
  type = "Microsoft.MachineLearningServices/workspaces@2024-10-01"
  name = "my-ai-project${random_string.suffix.result}"
  location = azurerm_resource_group.rg.location
  parent_id = azurerm_resource_group.rg.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      description = "This is my Azure AI PROJECT"
      friendlyName = "My Project"
      hubResourceId = azapi_resource.hub.id
    }
    kind = "project"
}
}

// AzAPI AI Services Connection
resource "azapi_resource" "AIServicesConnection" {
  type = "Microsoft.MachineLearningServices/workspaces/connections@2024-10-01"
  name = "Default_AIServices${random_string.suffix.result}"
  parent_id = azapi_resource.hub.id

  body = {
    properties = {
      category = "AIServices"
      target = azapi_resource.AIServicesResource.output.properties.endpoint
      authType = "AAD"
      isSharedToAll = true
      metadata = {
        ApiType = "Azure"
        ResourceId = azapi_resource.AIServicesResource.id
      }
    }
  }
  response_export_values = ["*"]
}

resource "azurerm_role_assignment" "ai_project_owner" {
  scope                = azapi_resource.project.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.simpleapp_app.identity.0.principal_id
}

resource "azurerm_role_assignment" "ai_hub_contributor_storage" {
  scope                = azurerm_storage_account.default.id
  role_definition_name = "Contributor"
  principal_id         = azapi_resource.hub.identity[0].principal_id
}

resource "azurerm_role_assignment" "app_insights_hub_storage_blob_data_contributor" {
  scope                = azurerm_application_insights.default.id
  role_definition_name = "Contributor"
  principal_id         = azapi_resource.hub.identity[0].principal_id
}

resource "azurerm_role_assignment" "ai_project_contributor_storage" {
  scope                = azurerm_storage_account.default.id
  role_definition_name = "Contributor"
  principal_id         = azapi_resource.project.identity[0].principal_id
}



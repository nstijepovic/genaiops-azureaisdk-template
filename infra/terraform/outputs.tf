output "resource_group_id" {
  value = azurerm_resource_group.rg.id
}

output "project_id" {
    value = azapi_resource.project.id
}

output "endpoint" {
  value = azapi_resource.AIServicesResource.output
}
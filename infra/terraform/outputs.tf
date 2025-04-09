output "resource_group_id" {
  value = azurerm_resource_group.rg.id
}

output "project_id" {
    value = azapi_resource.project.id
}

output "endpoint" {
  value = azapi_resource.AIServicesResource.output
}

output "openai_deployments" {
  value = {
    for instance, aoai in module.aoai : instance => aoai.aoai_endpoint
  }
}
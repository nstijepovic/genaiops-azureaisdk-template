variable "name" {
  description = "The name of the Azure OpenAI resource."
  type        = string
}

variable "location" {
  description = "Location of the Azure OpenAI resource."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for Azure OpenAI."
  type        = string
}

variable "sku_name" {
  description = "SKU tier for Azure OpenAI (must be 'S0')."
  type        = string
  default     = "S0"
}

variable "deployments" {
  description = "Map of OpenAI model deployments."
  type = map(object({
    deployment_name = string
    model_name      = string
    model_version   = string
    scale_type      = string
  }))
  default = {}
}
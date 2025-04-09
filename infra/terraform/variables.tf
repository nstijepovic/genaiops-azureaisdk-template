variable "resource_group_location" {
  type        = string
  default     = "uaenorth"
  description = "Location of the resource group."
}

variable "resource_group_name_prefix" {
  type        = string
  default     = "rg"
  description = "Prefix of the resource group name that's combined with a random ID so name is unique in your Azure subscription."
}

variable "prefix" {
    type = string
    description="This variable is used to name the hub, project, and dependent resources."
    default = "ai"
}

variable "sku" {
    type        = string
    description = "The sku name of the AIServicesResource."
    default     = "S0"
}


resource "random_string" "suffix" {  
  length           = 4  
  special          = false  
  upper            = false  
} 

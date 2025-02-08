# Azure Infrastructure Setup

## Prerequisites

- Access to Azure Subscription with Contribution rights
- Azure CLI installed and configured
- Terraform installed (version 1.0 or later)
- Appropriate Azure permissions to create resources

## Infrastructure Overview

The infrastructure setup creates a public environment in Azure with the following components:

- Azure AI Foundry Hub Project
- Azure Container Registry
- Application Insights
- Storage Account
- Key Vault
- Function App with associated resources

## Terraform Files Structure

### variables.tf
Defines all input variables used across the Terraform configuration.
Add more variables to make the infra configuration more flexible:

- Resource naming 
- Resource azure region
- Service tiers and SKUs

### terraform.tf
Contains the Terraform configuration and provider settings:

- Required provider versions
- Backend configuration for state storage
- Provider-specific settings

### ai_foundry.tf
Manages Azure AI Foundry Hub resources:

- AI Foundry Hub and Project creation
- Associated Resources
- Associated permissions and roles

### function_app.tf
Defines the Function App and its dependencies:

- App Service Plan
- Function App settings
- Associated storage account
- Application Insights integration

### locals.tf
Contains local variables used for:

- It is empty and provided for modifying variables before usage

### outputs.tf
Defines the outputs exposed after infrastructure deployment:

- Resource IDs

### dev.tfvars
Environment-specific variable values for development environment:

- It is empty and provided for adding values for dev environment
- Similar file for each environment should be created

## Deployment Steps

### 1. Authentication

```bash
# Login to Azure
az login

# Verify your subscription
az account show
```

### 2. Initialize Terraform

```bash
# Navigate to the infrastructure directory
cd infra

# Initialize Terraform
terraform init
```

This step downloads required providers and initializes the backend.

### 3. Plan the Deployment

```bash
# Create execution plan
terraform plan
```

Review the plan output carefully for:

- Resources to be created
- Any changes to existing resources
- Potential issues or warnings

### 4. Apply the Changes

```bash
# Apply the plan
terraform apply
```

### 5. Verify Deployment

After deployment completes:

1. Check the Azure portal for the new resource group
2. Verify all resources are created successfully
3. Ensure there are no deployment errors in the activity log
4. Test resource connectivity and permissions

## Customization

To customize the infrastructure for your needs:

- Modify resource naming in `locals.tf`
- Adjust resource SKUs and tiers in `variables.tf`
- Add or modify resources in respective .tf files
- Update environment-specific values in `dev.tfvars`

> **Note: Public Environment**  
> This setup creates a public environment. For private environment setup (including private endpoints and network isolation), additional configuration will be needed. Links to private environment setup documentation will be added in future updates.

## Next Steps

- Setup Local environment for experimentation 
- Perform local Experimentation
- Setup Github Secrets
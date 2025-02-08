# GitHub Repository Setup Guide

## Prerequisites

- Azure CLI installed and configured
- GitHub account with repository access
- Azure subscription with appropriate permissions

## 1. Service Principal Creation

Create a service principal in Azure Entra ID:

```bash
# Login to Azure
az login

# Create service principal and use output
az ad sp create-for-rbac --name "your-sp-name" --role contributor \
    --scopes /subscriptions/your-subscription-id \
    --sdk-auth

# These credentials are used as Github environment secrets to access 
# Azure resources and services from Github workflows
```

The output should look like:

```json
{
    "clientId": "xxx",
    "clientSecret": "xxxx",
    "subscriptionId": "xxxx",
    "tenantId": "xxxx"
}
```

## 2. GitHub Environments Setup

Create the following environments in your GitHub repository:

1. Go to your repository settings
2. Navigate to Environments
3. Create environments for:
   - pr (Pull Request)
   - dev (Development)
   - any other needed environment

### Environment Variables

For each environment, set these variables (based on your .env file):

```yaml
# Required for all environments
AZURE_CREDENTIALS: |
    {
        "clientId": "xxx",
        "clientSecret": "xxxx",
        "subscriptionId": "xxxx",
        "tenantId": "xxxx"
    }

# OpenAI Configuration
AZURE_OPENAI_API_VERSION: "2024-02-01"
AZURE_AI_CHAT_ENDPOINT: "https://your-instance.openai.azure.com/"
AZURE_AI_CHAT_KEY: "your-chat-key"
AOAI_API_KEY: "your-api-key"
GPT4O_DEPLOYMENT_NAME: "your-deployment"
GPT4O_API_KEY: "your-gpt4-key"

# Project Configuration
SUBSCRIPTION_ID: "your-subscription"
RESOURCE_GROUP_NAME: "your-resource-group"
PROJECT_NAME: "your-project-name"
USER_CLIENT_ID: "your-client-id"
CONNECTION_STRING: "your-connection-string"
PROMPTY_FILE: "prompty.yaml"
```

## 3. Workflow Configurations

### PR Workflow (math_coding_pr_workflow.yaml)

Triggers on PR to dev or main for specific changes:

```yaml
name: Math Coding PR Workflow

on:
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'math_coding/**'
      - '.github/**'
      - 'llmops/**'

jobs:
  validate:
    uses: ./.github/workflows/platform_pr_dev_workflow.yaml
    with:
      config-file: experiment.pr.yaml
    secrets: inherit
```

### CI/CD Workflow (math_coding_ci_dev_workflow.yaml)

Executes on PR merge to main or dev:

```yaml
name: Math Coding CI/CD Workflow

on:
  push:
    branches: [ main, dev ]
    paths:
      - 'math_coding/**'
      - '.github/**'
      - 'llmops/**'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Evaluation
        run: |
          python -m experiment.run --config experiment.dev.yaml
      
      - name: Deploy Function
        uses: ./.github/workflows/platform_cd_function_deployment.yaml
        with:
          config-file: experiment.dev.yaml
        secrets: inherit
```

## 4. Workflow Details

### PR Validation Workflow

- Triggered by pull requests to dev or main
- Monitors changes in specific folders
- Uses experiment.pr.yaml for configuration
- Performs:
  - Unit testing
  - Code quality checks
  - Build validation

### CI/CD Development Workflow

- Triggered on PR merge to dev or main
- Uses environment-specific configuration (experiment.dev.yaml)
- Performs:
  - Evaluation with selected prompts
  - Model configuration testing
  - Logging to AI Foundry project
  - Function deployment

## 5. Making Changes

To trigger the PR workflow:

```bash
# Create and checkout feature branch
git checkout -b feature/math-enhancement

# Make changes to relevant files
# Example: Update math_coding/flows/math_code_generation/pure_python_flow.py

# Commit and push changes
git add .
git commit -m "Enhanced math coding functionality"
git push origin feature/math-enhancement

# Create PR to dev branch through GitHub interface
```

## Best Practices

- Keep sensitive information in GitHub Secrets
- Use different configuration files for different environments
- Implement proper branch protection rules
- Review workflow logs for debugging
- Maintain clear documentation for custom deployment workflows

## Troubleshooting

- Verify service principal permissions
- Check environment variable configuration
- Review GitHub Actions logs for errors
- Ensure branch protection rules don't block workflows
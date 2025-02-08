# Local Environment Setup with Conda

## Prerequisites

- Python 3.9 or higher
- Conda package manager
- Azure CLI installed
- Git installed

## Step 1: Using Conda Environment Manager

You can use Conda for managing your Python environment. This guide will focus on Conda setup.

### Conda Environment Setup

```bash
# Create a new conda environment with Python 3.9
conda create -n myenv python=3.9

# Activate the environment
conda activate myenv
```

## Step 2: Azure Authentication

```bash
# Login to Azure
az login

# Verify your login
az account show
```

## Step 3: Install Required Packages

```bash
# Install execution requirements
python -m pip install -r ./.github/requirements/execute_job_requirements.txt

# Install validation requirements
python -m pip install -r ./.github/requirements/build_validation_requirements.txt

# Install the package in editable mode
python -m pip install -e .
```

## Step 4: Environment Configuration

Create and configure your environment file:

```bash
# Create .env file from template
cp .env.sample .env
```

### Environment Variables Configuration

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| AZURE_OPENAI_API_VERSION | Azure OpenAI API version | Use the latest stable version from Azure OpenAI documentation e.g. 2024-02-15-preview |
| AZURE_AI_CHAT_ENDPOINT | Azure OpenAI Chat API endpoint | Found in Azure Portal → Azure OpenAI resource → Keys and Endpoint. e.g. https://your-resource.openai.azure.com/openai/deployments/your-deployed-model |
| AZURE_AI_CHAT_KEY | Azure OpenAI Chat API key | Found in Azure Portal → Azure OpenAI resource → Keys and Endpoint e.g. xxxxxx |
| AOAI_API_KEY | Azure OpenAI API key | Found in Azure Portal → Azure OpenAI resource → Keys and Endpoint e.g. xxxxxx |
| GPT4O_DEPLOYMENT_NAME | GPT-4 model deployment name | Found in Azure Portal → Azure OpenAI resource → Model Deployments |
| GPT4O_API_KEY | GPT-4 API key | Found in Azure Portal → Azure OpenAI resource → Keys and Endpoint |
| SUBSCRIPTION_ID | Azure subscription ID | Found in Azure Portal → Subscriptions |
| RESOURCE_GROUP_NAME | Resource group name | Name of your Azure resource group |
| PROJECT_NAME | AI Foundry project name | Name of your AI Foundry project in Azure |
| USER_CLIENT_ID | User-defined managed identity (Optional) | Used only for online evaluations. Create in Azure Portal → Managed Identities |
| CONNECTION_STRING | AI Foundry project connection string | Found in AI Foundry project settings (Must be enclosed in quotes) |
| PROMPTY_FILE | Path to prompt template file | Local path to your prompt template file |

### Example .env File

```ini
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_AI_CHAT_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/your-deployed-model
AZURE_AI_CHAT_KEY=your-chat-key
AOAI_API_KEY=your-openai-key
GPT4O_DEPLOYMENT_NAME=your-deployment-name
GPT4O_API_KEY=your-gpt4-key
SUBSCRIPTION_ID=your-subscription-id
RESOURCE_GROUP_NAME=your-resource-group
PROJECT_NAME=your-project-name
USER_CLIENT_ID=your-client-id
CONNECTION_STRING="your-connection-string"
PROMPTY_FILE=xxxxx.prompty
```

## Important Notes

- The CONNECTION_STRING value must be enclosed in quotes in the .env file
- The CONNECTION_STRING value is available from **project overview** page of Azure AI Foundry under **Project connection string**
- Ensure the PROMPTY_FILE value is correct and points to a valid file name. prompty files are available under math_coding/flows/math_code_generation folder
- USER_CLIENT_ID is optional and only required for online evaluations
- Keep your .env file secure and never commit it to version control
- Regularly update your API versions to ensure compatibility
- Multiple examples are shown by means of using different endpoint types.

## Verification

To verify your setup:

1. Ensure your conda environment is activated
2. Verify Azure login status
3. Test package installation by running a simple command
4. Check environment variables are loaded correctly

## Troubleshooting

- If packages fail to install, try updating pip: `python -m pip install --upgrade pip`
- For Azure login issues, clear your credentials and login again
- Check file permissions if you have issues creating the .env file
- Verify your Python version matches the requirements
# GenAIOps with AI Foundry

## Introduction

GenAIOps with AI Foundry is a template project that helps you implement and manage AI operations efficiently using Azure AI services. This documentation provides comprehensive guides for setting up, configuring, and using the template.

## Documentation Sections

### 1. Getting Started Guide
- [Getting Started Guide](guides/getting-started.md)
  - Initial repository setup
  - Basic configuration
  - Fork and clone instructions
  - GitHub actions setup

### 2. Infrastructure Setup
- [Cloud Infrastructure Setup](guides/setup-cloud-infra.md)
  - Azure resource provisioning
  - Terraform configuration
  - Infrastructure deployment steps
  - Environment verification

### 3. Local Development Environment
- [Local Setup with Conda](guides/local-setup-conda.md)
  - Conda environment configuration
  - Package installation
  - Environment variables setup
  - Local testing procedures

- [Local Setup with UV - coming soon]()
  - UV environment setup
  - Package management
  - Configuration steps
  - Testing procedures

### 4. Experimentation Guide
- [Experimentation Configuration](guides/experimentation-guide.md)
  - Experiment setup
  - Configuration files
  - Evaluator setup
  - Dataset management
  - Results analysis

### 5. GitHub Integration
- [GitHub Repository Setup](guides/setup-github-repo.md)
  - Service principal creation
  - Environment configuration
  - Workflow setup
  - CI/CD pipeline management
  - Security best practices

## Quick Links

### Setup and Configuration
- [Prerequisites](guides/getting-started.md#prerequisites)
- [Environment Variables](guides/local-setup-conda.md#environment-variables-configuration)
- [Infrastructure Overview](guides/setup-cloud-infra.md#infrastructure-overview)
- [GitHub Workflows](guides/setup-github-repo.md#workflow-configurations)

### Development and Testing
- [Local Development](guides/local-setup-conda.md#verification)
- [Experiment Configuration](guides/experimentation-guide.md#configuration-files)
- [Deployment Steps](guides/setup-cloud-infra.md#deployment-steps)
- [Best Practices](guides/setup-github-repo.md#best-practices)

## Repo Structure

The repository has the following structure:

```
genaiops-azureaisdk-template/
├── .github/ # Contains github actions and workflows
├── docs/ # Contains documentation and guides
├── infra/ # Contains terraform code for building public infrastructure
├── llmops/ # Main scripts for running experiments
├── math_coding/ # sample use case folder
├── tests/ # Contains unit tests for llmops scripts
├── .gitignore # Contains files and folders to ignore
├── .env.sample # Sample environment variables file
├── README.md # Main documentation file
```

The repository has the following structure for each use case:

```
use_case_name/
├── data/ # Contains datasets for evaluation
├── flows/ # Contains flow definitions for experiments
├── evaluation/ # Contains evaluation logic and scripts
├── online-evaluations/ # Contains scripts for online evaluations
├── deployment/ # Contains deployment scripts and configurations
├── experiment.yaml # Main configuration file for the experiment
├── experiment.<env>.yaml # Environment-specific configuration files
```

## Getting Help

- Check the [Troubleshooting](guides/setup-github-repo.md#troubleshooting) section for common issues
- Review workflow logs for debugging information
- Ensure all environment variables are properly configured
- Verify Azure and GitHub permissions

## Development Workflow

1. Fork and clone the repository
2. Set up local development environment
3. Configure Azure infrastructure
4. Set up GitHub environments and secrets
5. Develop and test locally
6. Create pull requests for changes
7. Monitor CI/CD pipelines
8. Deploy to production

## Security Considerations

- Keep sensitive information in environment variables
- Use GitHub secrets for credentials
- Follow Azure security best practices
- Implement proper access controls
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. Follow code review process

## Next Steps

1. Start with the [Getting Started Guide](guides/getting-started.md)
2. Set up your [Development Environment](guides/local-setup-conda.md)
3. Configure [Azure Infrastructure](guides/setup-cloud-infra.md)
4. Begin [Experimentation](guides/experimentation-guide.md)
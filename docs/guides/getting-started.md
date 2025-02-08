# Getting Started - GenAIOps with AI Foundry

## Prerequisites

- A GitHub account
- Git installed on your local machine
- Visual Studio Code or similar development IDE

## 1. Fork the Repository

First, you'll need to fork the repository to your organization:

1. Navigate to the original repository at `https://github.com/microsoft/genaiops-azureaisdk-template/`
2. Click the "Fork" button in the top-right corner
3. Select your organization from the dropdown menu
4. Wait for the forking process to complete

## 2. Enable GitHub Actions

To enable GitHub Actions in your forked repository:

1. Go to your forked repository's settings
2. Click on "Actions" in the left sidebar
3. Under "Actions permissions", select "Allow all actions and reusable workflows"
4. Click "Save"

## 3. Clone the Repository Locally

Clone your forked repository to your local machine:

```bash
# Clone the repository
git clone https://github.com/your-org/genaiops-azureaisdk-template.git

# Navigate into the project directory
cd genaiops-azureaisdk-template
```

View your remote repositories:

```bash
# View your remote repositories
git remote -v

# Should show:
# origin    https://github.com/your-org/genaiops-azureaisdk-template.git (fetch)
# origin    https://github.com/your-org/genaiops-azureaisdk-template.git (push)
# upstream  https://github.com/original-org/genaiops-azureaisdk-template.git (fetch)
# upstream  https://github.com/original-org/genaiops-azureaisdk-template.git (push)
```

## 4. Create a Feature Branch

Before making changes, create a new feature branch:

```bash
# Ensure you're on the main branch and up-to-date
git checkout main

# Create and switch to a new feature branch
git checkout -b feature/your-feature-name

# Example:
git checkout -b feature/add-prompty-file
```

## Best Practices for Branch Names

When naming your feature branches, follow these conventions:

- Use the prefix `feature/` for new features
- Use the prefix `bugfix/` for bug fixes
- Use the prefix `hotfix/` for urgent fixes
- Use hyphens to separate words
- Keep names short but descriptive

Examples:
- `feature/user-authentication`
- `bugfix/login-validation`
- `hotfix/security-patch`

## Next Steps

Now that your development environment has code set up, you can:

- Setup Azure Infrastructure to experience the template
- Setup Local environment for experimentation
- Perform local Experimentation
- Setup Github Secrets
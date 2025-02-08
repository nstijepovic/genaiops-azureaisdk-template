# Experimentation Configuration Guide

## Overview

Each use case in the project contains its own experiment configuration and environment settings. This guide explains the structure and configuration of experiments using the `math_coding` use case as an example. The whole purpose of experimentation is to find the best prompt and model configuration. Add multiple prompty files and use them with different model configuration to find the best combination and then use the same before pushing changes as PR to the repo.

> **Important:** The `.env` file contains sensitive information and should never be committed to the repository. Make sure it's listed in `.gitignore`.

## Project Structure

```
use_cases/
└── math_coding/
    ├── experiment.yaml           # Base configuration
    ├── experiment.dev.yaml       # Development environment overrides
    ├── experiment.prod.yaml      # Production environment overrides
    ├── flows/
    │   └── math_code_generation/
    │       └── pure_python_flow.py
    ├── evaluators/
    │   ├── eval_f1_score.py
    │   └── eval_accuracy.py
    └── data/
        ├── math_data.jsonl
        └── advanced_math_data.jsonl
```

## Configuration Files

### Base Experiment Configuration (experiment.yaml)

```yaml
# Name of the experiment. Must match use case folder name
name: math_coding

# Description of what the experiment does
description: "This is a math coding experiment"

# Path to the flow definition file
flow: flows/math_code_generation

# Function to be called when flow starts
entry_point: pure_python_flow:get_math_response

# List of available connection configurations
connections:
  - name: aoai
    connection_type: AzureOpenAIConnection
    api_base: https://demoopenaiexamples.openai.azure.com/
    api_version: 2023-07-01-preview
    api_key: ${AOAI_API_KEY}
    api_type: azure
    deployment_name: ${GPT4O_DEPLOYMENT_NAME}
  
  - name: gpt4o
    connection_type: AzureOpenAIConnection
    api_base: https://demoopenaiexamples.openai.azure.com/
    api_version: 2023-07-01-preview
    api_key: ${GPT4O_API_KEY}
    api_type: azure
    deployment_name: ${GPT4O_DEPLOYMENT_NAME}

# Connections to use
connections_ref:
  - aoai
  - gpt4o

# Environment variables
env_vars:
  - PROMPTY_FILE: math_template.prompty
  - MODEL_MAX_TOKENS: "2000"
  - TEMPERATURE: "0.7"

# Evaluation configuration
evaluators:
  - name: eval_f1_score
    flow: evaluations
    entry_point: pure_python_flow:get_math_response
    connections_ref:
      - aoai
      - gpt4o
    env_vars:
      - ENABLE_TELEMETRY: True
    datasets:
      - name: math_coding_test
        source: data/math_data.jsonl
        description: "Basic math problem evaluation dataset"
        mappings:
          ground_truth: "${data.answer}"
          response: "${target.response}"
      - name: advanced_math_test
        source: data/advanced_math_data.jsonl
        description: "Advanced math problem evaluation dataset"
        mappings:
          ground_truth: "${data.answer}"
          response: "${target.response}"

  - name: eval_accuracy
    flow: evaluations
    entry_point: pure_python_flow:evaluate_accuracy
    connections_ref:
      - aoai
    env_vars:
      - ENABLE_TELEMETRY: True
    datasets:
      - name: math_coding_test
        source: data/math_data.jsonl
        description: "Accuracy evaluation dataset"
        mappings:
          ground_truth: "${data.expected}"
          response: "${target.actual}"
```

### Environment-Specific Configuration (experiment.dev.yaml)

Environment-specific files can override settings from the base configuration:

```yaml
# Override base settings for development
env_vars:
  - TEMPERATURE: "0.9"
  - DEBUG_MODE: True
  - LOG_LEVEL: "DEBUG"

# Use different dataset for development
evaluators:
  - name: eval_f1_score
    datasets:
      - name: math_coding_test_dev
        source: data/math_data_dev.jsonl
```

## Components Explanation

### Connections

Connections define how to interact with external services (like Azure OpenAI). They use environment variables for sensitive information:

- `name`: Unique identifier for the connection
- `connection_type`: Type of service connection
- `api_base`: Service endpoint URL
- `api_key`: Authentication key (from .env)

### Evaluators

Each evaluator represents a different evaluation method:

- Must have a corresponding Python file in the evaluators folder
- Can use multiple datasets for testing
- Can have its own environment variables and connections

### Datasets

Datasets are used for evaluation:

- Located in the data folder
- JSONL format for consistent data handling
- Mappings define how to match ground truth with responses

## Environment Variables

Add necessary secrets and configurations in .env file:

```bash
# Azure OpenAI Configuration
AOAI_API_KEY=your-api-key
GPT4O_DEPLOYMENT_NAME=your-deployment
GPT4O_API_KEY=your-gpt4-key

# Project Configuration
ENABLE_TELEMETRY=True
```

## Best Practices

- Never commit .env files to version control
- Use environment-specific files for different settings
- Keep sensitive information in environment variables
- Use descriptive names for evaluators and datasets
- Document mappings clearly in dataset configurations
- Maintain consistent naming conventions across files

## Executing Experiments

Once you've set up your configuration, you can run experiments using the Python CLI:

### 1. Basic Execution

```bash
# Run the experiment with dev configuration for math_coding use case
python -m llmops.eval_experiments --environment_name dev --base_path math_coding --report_dir .
```

### 2. Running with different experiment files

```bash
# Run any_experiment.dev.yaml experiment
python -m llmops.eval_experiments --environment_name dev --base_path math_coding --report_dir . experiment_config_file=any_experiment.dev.yaml
```

### Monitoring Execution

During execution, you'll see:

- Progress indicators for each evaluator
- Evaluation metrics and results
- Any errors or warnings
- Evaluation information is stored in AI Foundry

### Output and Results

Experiment results are typically stored in:

- Results file with timestamp-based directories
- Metrics and evaluation results in JSON format
- Detailed logs for debugging and analysis
- Summary reports for quick overview

### Actions

Find:

- Best prompty file among all
- Best Model configuration including temperature

> **Important:** Always verify that your .env file is properly configured before running experiments. Missing or incorrect environment variables can cause execution failures.

## Adding New Use Cases

To add a new use case:

1. Create a new top-level folder similar to math_coding
2. Copy and modify the experiment configuration structure
3. Update evaluators, flows and datasets for your specific needs
4. Ensure all required environment variables are documented

> **Note:** Each use case should follow this structure while maintaining its own specific configuration, evaluators, and datasets. The example shown is for math_coding, but the same structure applies to all use cases.
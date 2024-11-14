import os
import yaml
from typing import Dict, List, Optional
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import ResourceNotFoundError
import zipfile
import requests
import shutil
import sys
import logging
from dotenv import load_dotenv
from llmops.experiment import load_experiment


def get_function_apps(yaml_content) -> List[Dict]:
    """
    Parse YAML content and retrieve all items where type is 'function_app'
    
    Args:
        yaml_content (str): String containing YAML configuration
        
    Returns:
        List[Dict]: List of dictionaries containing function app configurations
        
    Raises:
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        if yaml_content.get('type') == 'function_app':
            return yaml_content
        return None
        
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None
        
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return []

def setup_logger():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('deployment.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def read_yaml_config(yaml_path):
    """Read configuration from YAML file"""
    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)

def create_function_app(
    subscription_id,
    env_name,
    orchestration_config,
    function_config,
    logger=None
):

    if logger is None:
        logger = logging.getLogger(__name__)
    function_app =   function_config['function_app']
    logger.info(f"Creating function app {function_app['app_name']}")
    
    # Initialize the credential object
    credential = DefaultAzureCredential()

    # Initialize the management clients
    web_client = WebSiteManagementClient(credential, subscription_id)

    # Get existing service plan
    logger.info(f"Retrieving service plan {function_app['app_name']}")

    service_plan = web_client.app_service_plans.get(
        function_app['resource_group'],
        function_app['service_name']
    )

    # Convert environment variables to Azure app settings format
    azure_app_settings = [
        {"name": key, "value": str(value)} 
        for key, value in orchestration_config.resolved_env_vars.items()
    ]

    # Add required Azure Function settings
    required_settings = [
        {
            "name": "FUNCTIONS_WORKER_RUNTIME",
            "value": function_app['runtime']
        }
    ]
    azure_app_settings.extend(required_settings)

    azure_app_settings_secerets = [
        {"name": var, "value": str(os.getenv(var))} 
        for var in function_app['env_vars'] if os.getenv(var) is not None   
    ]

    azure_app_settings.extend(azure_app_settings_secerets)

    logger.info(f"Creating/updating function app with {len(azure_app_settings)} settings")
    # Create function app
    poller = web_client.web_apps.begin_create_or_update(
        function_app['resource_group'],
        function_app['app_name'],
        {
            "location": function_app['location'],
            "kind": "functionapp",
            "server_farm_id": service_plan.id,
            "site_config": {
                "linux_fx_version": f"{function_app['version']}",
                "app_settings": azure_app_settings
            }
        }
    )
    function_app_result = poller.result()
    logger.info(f"Function app {function_app['app_name']} created/updated successfully")
    
    return function_app_result

def zip_deploy_function(
    subscription_id,
    env_name,
    orchestration_config,
    function_config,
    logger=None
):
    zip_file_path = "."
    root_path = "genai_temp"
    function_app = function_config['function_app']
    if logger is None:
        logger = logging.getLogger(__name__)
    
    credential = DefaultAzureCredential()
    web_client = WebSiteManagementClient(credential, subscription_id)

    # Get publishing credentials
    logger.info("Retrieving publishing credentials")
    publish_creds = web_client.web_apps.begin_list_publishing_credentials(
        function_app['resource_group'],
        function_app['app_name']
    ).result()

    entry_point_file = f"{orchestration_config.entry_point.split(':')[0]}.py" # pure_python_flow.py
    flow_dir = orchestration_config.flow.split('/')[0] # orchestration
    full_path = os.path.join(orchestration_config.name, orchestration_config.flow, '*') # math_coding/orchestration/python/*
    print(f"Full path: {full_path}")
    
    # Create directory structure
    target_dir = os.path.join(root_path, orchestration_config.name, 'function_processor')
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy template files
    template_source = 'llmops/deployment/function_template/'
    template_dest = os.path.join(root_path, orchestration_config.name)
    shutil.copytree(template_source, template_dest, dirs_exist_ok=True)
    
    # Copy all files from full_path to function_processor
    for item in os.scandir(os.path.dirname(full_path)):
        if item.is_file():
            shutil.copy2(item.path, target_dir)
    
    # Copy orchestrator
    orchestrator_source = os.path.join(orchestration_config.name, 'deployment', 'function_orchestrator.py')
    orchestrator_dest = target_dir
    shutil.copy2(orchestrator_source, orchestrator_dest)

    # Create zip package if directory is provided
    if os.path.isdir(os.path.join(root_path, orchestration_config.name)):
        zip_file_path = os.path.join(root_path, orchestration_config.name)
        temp_zip = "function_app.zip"
        
        logger.info(f"Creating zip file from directory {zip_file_path}")
        
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(zip_file_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, zip_file_path)
                    zipf.write(file_path, arcname)
        zip_file_path = temp_zip

    # Upload zip file
    logger.info("Uploading zip package")
    with open(zip_file_path, 'rb') as f:
        zip_content = f.read()

    deployment_url = f"https://{function_app['app_name']}.scm.azurewebsites.net/api/zipdeploy"
    deployment_response = requests.post(
        deployment_url,
        auth=(publish_creds.publishing_user_name, publish_creds.publishing_password),
        headers={'Content-Type': 'application/zip'},
        data=zip_content
    )
    
    if deployment_response.status_code not in (200, 202):
        error_msg = f"Deployment failed with status {deployment_response.status_code}"
        logger.error(error_msg)
        raise Exception(error_msg)

    logger.info(f"Deployment completed with status {deployment_response.status_code}")
    return deployment_response.status_code

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy Azure Function App')
    parser.add_argument('--subscription-id', required=True, help='Azure subscription ID')
    parser.add_argument('--environment', required=True, help='environment like dev,test etc')
    parser.add_argument('--use_case_base_path', required=True, help='use case to deploy')
    parser.add_argument('--deployment_config', required=True, help='use case to deploy')
    parser.add_argument('--function-path', default='genai_temp', help='Path to function app code')
    return parser.parse_args()

def main():
    #args = parse_args()
    logger = setup_logger()

    try:
        # Create Function App
        load_dotenv()
        orchestration_config = load_experiment(
            filename=None, base_path="math_coding", env="dev"
        )

        deployment_config = read_yaml_config(os.path.join(orchestration_config.name, "deployment_config.yaml"))

        function_app = get_function_apps(deployment_config)
        if function_app is None:
            raise ValueError("No function app configuration found in YAML")
        
        logger.info("Starting function app deployment process")
        
        function_app_service = create_function_app(
            "f5772c02-4566-4154-a8d5-5b4658e5d310", # args.subscription_id,
            "dev", # args.environment,
            orchestration_config,
            function_app,
            logger
        )

        # Deploy the function code
        deployment_status = zip_deploy_function(
            "f5772c02-4566-4154-a8d5-5b4658e5d310", #args.subscription_id,
            "dev", # args.environment,
            orchestration_config,
            function_app,
            logger
        )

        logger.info(f"Deployment completed successfully with status: {deployment_status}")

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()


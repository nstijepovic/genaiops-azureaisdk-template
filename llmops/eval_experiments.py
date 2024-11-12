import argparse
import datetime
import json
import os
import pandas as pd
from dotenv import load_dotenv
from typing import Optional
import inspect
import importlib
import argparse
from azure.identity import DefaultAzureCredential
from llmops.experiment import load_experiment
from llmops.experiment_cloud_config import ExperimentCloudConfig

def prepare_and_execute(
    exp_filename: Optional[str] = None,
    base_path: Optional[str] = None,
    subscription_id: Optional[str] = None,
    build_id: Optional[str] = None,
    env_name: Optional[str] = None,
    report_dir: Optional[str] = None,
):
    """ 
    Prepare
    """
    load_dotenv()

    experiment = load_experiment(
        filename=exp_filename, base_path=base_path, env=env_name
    )
    experiment_name = experiment.name

    eval_flows = experiment.evaluators

    orchestration_path = os.path.join(
        base_path, experiment.flow
    )

    orchestration_entry_point = experiment.entry_point

    orchestration_connections = experiment.connections

    if report_dir:
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

    for evaluator in eval_flows:
        evaluator_path = os.path.join(
            base_path, evaluator.flow
        )
        evaluator_entry_point = evaluator.entry_point

        service_module = None
        for file in os.listdir(evaluator_path):
            if (
                file.endswith('.py') and
                file.lower().startswith('eval_')
            ):
                module_name = file[:-3]
                flow_components = evaluator_path.split('/')
                flow_formatted = '.'.join(flow_components)
                module_path = (
                    f'{flow_formatted}.'
                    f'{module_name}'
                )
                import sys
                dependent_modules_dir = os.path.join(
                    base_path, experiment.flow
                    )
                sys.path.append(dependent_modules_dir)
                current_dir = os.path.dirname(os.path.abspath(__file__))  # evaluations folder
                parent_dir = os.path.dirname(current_dir)  # math_coding folder
                sys.path.insert(0, parent_dir)
                service_module = importlib.import_module(
                    module_path
                    )

                module_names = dir(service_module)

                # Filter names to get functions defined in module
                function_names = [
                    name for name in module_names
                    if inspect.isfunction
                    (
                        getattr(
                            service_module,
                            name
                            )
                        )
                    ]

                for function_name in function_names:
                    if (
                        function_name.lower().startswith('eval_')
                    ):
                        service_function = getattr(
                            service_module,
                            function_name
                            )
                        for ds in evaluator.datasets:
                            
                            timestamp = datetime.datetime.now().strftime(
                                "%Y%m%d_%H%M%S"
                                )

                            result = service_function(
                                f"{experiment_name}_eval_{timestamp}",
                                os.path.join(
                                    base_path,
                                    ds.source
                                ),
                                ds.mappings,
                                report_dir
                            )


                            print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("config_parameters")
    parser.add_argument(
        "--environment_name",
        type=str,
        required=True,
        help="env_name from config.yaml",
    )
    parser.add_argument(
        "--base_path",
        type=str,
        required=True,
        help="use case folder path",
    )
    parser.add_argument(
        "--report_dir",
        type=str,
        required=True,
        help="output folder path",
    )
    parser.add_argument("--deploy_traces", default=False, action="store_true")
    parser.add_argument("--visualize", default=False, action="store_true")
    args = parser.parse_args()

    prepare_and_execute(
        base_path=args.base_path,
        env_name=args.environment_name,
        report_dir=args.report_dir
    )
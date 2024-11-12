import os
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import re
from dotenv import load_dotenv
from copy import deepcopy

@dataclass
class DatasetMapping:
    name: str
    source: str
    description: Optional[str] = None
    mappings: Dict[str, str] = field(default_factory=dict)

@dataclass
class Connection:
    name: str
    connection_type: str
    api_base: str
    api_version: str
    api_key: str
    api_type: str
    deployment_name: str

    def resolve_variables(self, env_vars: Dict[str, str]) -> None:
        """Resolve variables in connection properties using environment variables."""
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, str) and "${" in field_value:
                var_name = re.search(r'\${(.*)}', field_value).group(1)
                if var_name in env_vars:
                    setattr(self, field_name, env_vars[var_name])
                else:
                    raise ValueError(f"Environment variable {var_name} not found")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Connection':
        return cls(
            name=data['name'],
            connection_type=data['connection_type'],
            api_base=data['api_base'],
            api_version=data['api_version'],
            api_key=data['api_key'],
            api_type=data['api_type'],
            deployment_name=data['deployment_name']
        )

@dataclass
class Evaluator:
    name: str
    flow: str
    entry_point: str
    connections: List[Connection]  # Changed from List[str] to List[Connection]
    env_vars: List[Dict[str, str]]
    datasets: List[DatasetMapping]

    def resolve_variables(self) -> None:
        """Resolve all variables in the experiment configuration."""
        load_dotenv()
        env_vars = dict(os.environ)

        # Resolve connection variables in main experiment
        for conn in self.connections:
            conn.resolve_variables(env_vars)

        # Resolve experiment env vars
        self.resolved_env_vars = {}
        for env_var_dict in self.env_vars:
            for key, value in env_var_dict.items():
                if isinstance(value, str) and "${" in value:
                    var_name = re.search(r'\${(.*)}', value).group(1)
                    if var_name in env_vars:
                        self.resolved_env_vars[key] = env_vars[var_name]
                    else:
                        raise ValueError(f"Environment variable {var_name} not found")
                else:
                    self.resolved_env_vars[key] = value

    @classmethod
    def from_dict(cls, data: Dict[str, Any], connections_map: Dict[str, Connection]) -> 'Evaluator':
        # Expand connections from connection names to actual Connection objects
        expanded_connections = []
        for conn_name in data['connections']:
            if conn_name in connections_map:
                expanded_connections.append(deepcopy(connections_map[conn_name]))
            else:
                raise ValueError(f"Connection {conn_name} not found in connections map")

        return cls(
            name=data['name'],
            flow=data['flow'],
            entry_point=data['entry_point'],
            connections=expanded_connections,  # Using expanded connections
            env_vars=data['env_vars'],
            datasets=[
                DatasetMapping(
                    name=ds['name'],
                    source=ds['source'],
                    description=ds.get('description'),
                    mappings=ds.get('mappings', {})
                ) for ds in data.get('datasets', [])
            ]
        )

@dataclass
class Experiment:
    name: str
    flow: str
    entry_point: str
    connections: List[Connection]  # Changed from List[str] to List[Connection]
    env_vars: List[Dict[str, str]]
    description: Optional[str] = None
    evaluators: List[Evaluator] = field(default_factory=list)

    @staticmethod
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Experiment.deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # For lists, we'll merge by name if items are dictionaries with 'name' key
                if result[key] and isinstance(result[key][0], dict) and 'name' in result[key][0]:
                    merged_list = deepcopy(result[key])
                    override_map = {item['name']: item for item in value}
                    for i, item in enumerate(merged_list):
                        if item['name'] in override_map:
                            if isinstance(item, dict):
                                merged_list[i] = Experiment.deep_merge(item, override_map[item['name']])
                            else:
                                merged_list[i] = override_map[item['name']]
                    # Add new items from override that don't exist in base
                    for override_item in value:
                        if not any(item['name'] == override_item['name'] for item in merged_list):
                            merged_list.append(override_item)
                    result[key] = merged_list
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    @classmethod
    def load_config(cls, base_path: Union[str, Path], dev_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Load and merge configuration from base and dev YAML files."""
        with open(base_path, 'r') as f:
            base_config = yaml.safe_load(f)

        if dev_path:
            try:
                with open(dev_path, 'r') as f:
                    dev_config = yaml.safe_load(f) or {}
                return cls.deep_merge(base_config, dev_config)
            except FileNotFoundError:
                return base_config
        return base_config

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path], dev_yaml_path: Optional[Union[str, Path]] = None) -> 'Experiment':
        """Create an Experiment instance from YAML files."""
        config = cls.load_config(yaml_path, dev_yaml_path)

        # Create connections map from the connections section
        connections_config = config.get('connections', [])
        connections_map = {
            conn['name']: Connection.from_dict(conn)
            for conn in connections_config
        }

        # Expand connections in main experiment config
        expanded_connections = []
        for conn_name in config['connections']:
            if isinstance(conn_name, str):  # Handle case where connection might already be expanded
                if conn_name in connections_map:
                    expanded_connections.append(deepcopy(connections_map[conn_name]))
                else:
                    raise ValueError(f"Connection {conn_name} not found in connections map")
            else:  # Already expanded connection
                expanded_connections.append(Connection.from_dict(conn_name))

        # Create Evaluator objects with expanded connections
        evaluators_config = config.get('evaluators', [])
        evaluators = [
            Evaluator.from_dict(eval_config, connections_map)
            for eval_config in evaluators_config
        ]

        return cls(
            name=config['name'],
            description=config.get('description'),
            flow=config['flow'],
            entry_point=config['entry_point'],
            connections=expanded_connections,
            env_vars=config['env_vars'],
            evaluators=evaluators
        )

    def resolve_variables(self) -> None:
        """Resolve all variables in the experiment configuration."""
        load_dotenv()
        env_vars = dict(os.environ)

        # Resolve connection variables in main experiment
        for conn in self.connections:
            conn.resolve_variables(env_vars)

        # Resolve experiment env vars
        self.resolved_env_vars = {}
        for env_var_dict in self.env_vars:
            for key, value in env_var_dict.items():
                if isinstance(value, str) and "${" in value:
                    var_name = re.search(r'\${(.*)}', value).group(1)
                    if var_name in env_vars:
                        self.resolved_env_vars[key] = env_vars[var_name]
                    else:
                        raise ValueError(f"Environment variable {var_name} not found")
                else:
                    self.resolved_env_vars[key] = value


        # Resolve evaluator variables and their connection variables


    def get_evaluator(self, evaluator_name: str) -> Optional[Evaluator]:
        """Get evaluator configuration by name."""
        for evaluator in self.evaluators:
            if evaluator.name == evaluator_name:
                return evaluator
        return None

    def get_dataset(self, evaluator_name: str, dataset_name: str) -> Optional[DatasetMapping]:
        """Get dataset configuration by evaluator and dataset name."""
        evaluator = self.get_evaluator(evaluator_name)
        if evaluator:
            for dataset in evaluator.datasets:
                if dataset.name == dataset_name:
                    return dataset
        return None

def load_experiment(
    filename: Optional[str] = None,
    base_path: Optional[str] = None,
    env: Optional[str] = None
) -> Experiment:
    safe_base_path = base_path or ""
    experiment_file_name = filename or "experiment.yaml"
       # Validate the experiment file name
    file_parts = os.path.splitext(experiment_file_name)
    if len(file_parts) != 2:  # noqa: PLR2004
        raise ValueError(f"Invalid experiment file '{experiment_file_name}'")
    env_experiment_file_name = f"{file_parts[0]}.{env}{file_parts[1]}"

    exp_file_path = os.path.join(safe_base_path, experiment_file_name)
    if not os.path.exists(exp_file_path):
        raise ValueError(f"Could not open experiment file {exp_file_path}")
    
    env_exp_file_path = os.path.join(safe_base_path, env_experiment_file_name)

    # Load experiment configuration with optional dev override
    experiment = Experiment.from_yaml(
        exp_file_path,
        env_exp_file_path  # Optional dev config
    )
    
    # Resolve all variables
    experiment.resolve_variables()
    
    return experiment

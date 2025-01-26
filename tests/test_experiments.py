"""Tests for Experiment class."""
import pytest
import yaml

from llmops.experiment import Experiment, Connection, Evaluator, DatasetMapping


@pytest.fixture
def sample_connection():
    """Fixture providing a sample Connection object."""
    return Connection(
        name="test_conn",
        connection_type="azure",
        api_base="https://api.example.com",
        api_version="v1",
        api_key="secret",
        api_type="azure",
        deployment_name="deploy"
    )


@pytest.fixture
def sample_config(tmp_path):
    """Fixture providing sample experiment configurations."""
    base_config = {
        "name": "base_experiment",
        "flow": "base_flow",
        "entry_point": "base.py",
        "connections_ref": ["conn1"],
        "connections": [{
            "name": "conn1",
            "connection_type": "azure",
            "api_base": "https://base.example.com",
            "api_version": "v1",
            "api_key": "base_key",
            "api_type": "azure",
            "deployment_name": "base_deploy"
        }],
        "env_vars": [{"BASE_VAR": "base_value"}],
        "evaluators": [{
            "name": "base_evaluator",
            "flow": "eval_flow",
            "entry_point": "eval.py",
            "connections_ref": ["conn1"],
            "env_vars": [{"EVAL_VAR": "eval_value"}],
            "datasets": []
        }]
    }

    dev_config = {
        "name": "dev_experiment",
        "description": "Development config",
        "connections_ref": ["conn1", "conn2"],
        "connections": [{
            "name": "conn2",
            "connection_type": "aws",
            "api_base": "https://dev.example.com",
            "api_version": "v2",
            "api_key": "dev_key",
            "api_type": "aws",
            "deployment_name": "dev_deploy"
        }],
        "env_vars": [{"DEV_VAR": "dev_value"}],
        "evaluators": [{
            "name": "base_evaluator",
            "env_vars": [{"OVERRIDE_VAR": "overridden"}]
        }]
    }

    return base_config, dev_config, tmp_path


class TestDeepMerge:
    """Tests for deep_merge static method."""

    def test_simple_merge(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        merged = Experiment.deep_merge(base, override)
        assert merged == {"a": 1, "b": 3, "c": 4}

    def test_nested_dict_merge(self):
        """Test merging nested dictionaries."""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        merged = Experiment.deep_merge(base, override)
        assert merged == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_list_merge_by_name(self):
        """Test merging lists with name field."""
        base = {"items": [{"name": "a", "val": 1}, {"name": "b", "val": 2}]}
        override = {"items": [{"name": "a", "val": 3}, {"name": "c", "val": 4}]}
        merged = Experiment.deep_merge(base, override)
        assert merged["items"] == [
            {"name": "a", "val": 3},
            {"name": "b", "val": 2},
            {"name": "c", "val": 4}
        ]

    def test_non_dict_list_merge(self):
        """Test merging lists without name field."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        merged = Experiment.deep_merge(base, override)
        assert merged["items"] == [4, 5]


class TestLoadConfig:
    """Tests for load_config class method."""

    def test_load_base_only(self, sample_config, tmp_path):
        """Test loading base config file only."""
        base, _, tmp_path = sample_config
        base_path = tmp_path / "base.yaml"
        base_path.write_text(yaml.dump(base))

        config = Experiment.load_config(base_path)
        assert config["name"] == "base_experiment"
        assert len(config["connections"]) == 1

    def test_load_with_dev(self, sample_config, tmp_path):
        """Test loading base and development config files."""
        base, dev, tmp_path = sample_config
        base_path = tmp_path / "base.yaml"
        dev_path = tmp_path / "dev.yaml"
        base_path.write_text(yaml.dump(base))
        dev_path.write_text(yaml.dump(dev))

        config = Experiment.load_config(base_path, dev_path)
        assert config["name"] == "dev_experiment"
        assert len(config["connections"]) == 2
        assert len(config["evaluators"]) == 1

    def test_missing_dev_file(self, sample_config, tmp_path):
        """Test error handling for missing development config file."""
        base, _, tmp_path = sample_config
        base_path = tmp_path / "base.yaml"
        dev_path = tmp_path / "missing.yaml"
        base_path.write_text(yaml.dump(base))

        config = Experiment.load_config(base_path, dev_path)
        assert config["name"] == "base_experiment"


class TestFromYaml:
    """Tests for from_yaml class method."""
    
    def test_basic_creation(self, sample_config, tmp_path):
        """Test creation of Experiment object from YAML."""
        base, _, tmp_path = sample_config
        base_path = tmp_path / "base.yaml"
        base_path.write_text(yaml.dump(base))

        experiment = Experiment.from_yaml(base_path)
        assert experiment.name == "base_experiment"
        assert len(experiment.connections) == 1
        assert len(experiment.evaluators) == 1

    def test_connection_expansion(self, sample_config, tmp_path):
        """Test connection expansion from connection references."""
        base, dev, tmp_path = sample_config
        base_path = tmp_path / "base.yaml"
        dev_path = tmp_path / "dev.yaml"
        base_path.write_text(yaml.dump(base))
        dev_path.write_text(yaml.dump(dev))

        experiment = Experiment.from_yaml(base_path, dev_path)
        assert len(experiment.connections) == 2
        assert {c.name for c in experiment.connections} == {"conn1", "conn2"}

    def test_missing_connection(self, tmp_path):
        """Test error handling for missing connection reference."""
        config = {
            "name": "test",
            "flow": "flow",
            "entry_point": "entry.py",
            "connections_ref": ["missing_conn"],
            "connections": [],
            "env_vars": []
        }
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml.dump(config))

        with pytest.raises(ValueError, match="Connection missing_conn not found"):
            Experiment.from_yaml(config_path)


class TestResolveVariables:
    """Tests for resolve_variables method."""

    def test_env_var_resolution(self, monkeypatch):
        """Test resolution of environment variables."""
        monkeypatch.setenv("API_KEY", "resolved_key")
        experiment = Experiment(
            name="test",
            flow="flow",
            entry_point="entry.py",
            connections=[Connection(
                name="test_conn",
                connection_type="azure",
                api_base="https://example.com",
                api_version="v1",
                api_key="${API_KEY}",
                api_type="azure",
                deployment_name="deploy"
            )],
            env_vars=[{"TEST_VAR": "${ENV_VAR}"}],
            evaluators=[]
        )
        monkeypatch.setenv("ENV_VAR", "resolved_value")

        experiment.resolve_variables()

        assert experiment.connections[0].api_key == "resolved_key"
        assert experiment.resolved_env_vars["TEST_VAR"] == "resolved_value"

    def test_missing_env_var(self, sample_connection):
        """Test error handling for missing environment variable."""
        experiment = Experiment(
            name="test",
            flow="flow",
            entry_point="entry.py",
            connections=[sample_connection],
            env_vars=[{"MISSING": "${UNDEFINED}"}],
            evaluators=[]
        )

        with pytest.raises(ValueError, match="env var UNDEFINED not found"):
            experiment.resolve_variables()


class TestAccessorMethods:
    """Tests for get_evaluator and get_dataset methods."""

    def test_get_evaluator(self):
        """Test get_evaluator method."""
        evaluator = Evaluator(
            name="test_eval",
            flow="eval_flow",
            entry_point="eval.py",
            connections=[],
            env_vars=[],
            datasets=[]
        )
        experiment = Experiment(
            name="test",
            flow="flow",
            entry_point="entry.py",
            connections=[],
            env_vars=[],
            evaluators=[evaluator]
        )

        found = experiment.get_evaluator("test_eval")
        assert found == evaluator
        assert experiment.get_evaluator("missing") is None

    def test_get_dataset(self):
        """Test get_dataset method."""
        dataset = DatasetMapping(
            name="test_ds",
            source="source",
            description="Test dataset"
        )
        evaluator = Evaluator(
            name="test_eval",
            flow="flow",
            entry_point="entry.py",
            connections=[],
            env_vars=[],
            datasets=[dataset]
        )
        experiment = Experiment(
            name="test",
            flow="flow",
            entry_point="entry.py",
            connections=[],
            env_vars=[],
            evaluators=[evaluator]
        )

        found = experiment.get_dataset("test_eval", "test_ds")
        assert found == dataset
        assert experiment.get_dataset("missing", "test_ds") is None
        assert experiment.get_dataset("test_eval", "missing") is None


# Edge Case Tests
def test_empty_experiment():
    """Test creation of an empty experiment."""
    experiment = Experiment(
        name="empty",
        flow="",
        entry_point="",
        connections=[],
        env_vars=[],
        evaluators=[]
    )

    assert experiment.name == "empty"
    assert experiment.get_evaluator("any") is None


def test_multiple_env_vars():
    """Test resolution of multiple environment variables."""
    experiment = Experiment(
        name="test",
        flow="flow",
        entry_point="entry.py",
        connections=[],
        env_vars=[
            {"VAR1": "value1"},
            {"VAR2": "value2"},
            {"VAR1": "overridden"}
        ],
        evaluators=[]
    )

    experiment.resolve_variables()
    assert experiment.resolved_env_vars["VAR1"] == "overridden"
    assert experiment.resolved_env_vars["VAR2"] == "value2"

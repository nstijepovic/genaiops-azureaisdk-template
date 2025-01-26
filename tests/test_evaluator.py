import pytest
from copy import deepcopy

from llmops.experiment import Evaluator, Connection


@pytest.fixture
def sample_connection():
    """Fixture providing a Connection with placeholder values"""
    return Connection(
        name="${CONN_NAME}",
        connection_type="${CONN_TYPE}",
        api_base="${API_BASE}",
        api_version="v1",
        api_key="${API_KEY}",
        api_type="azure",
        deployment_name="deploy"
    )


@pytest.fixture
def connections_map(sample_connection):
    """Fixture providing a connections map"""
    return {"valid_conn": sample_connection}


def test_resolve_variables_resolves_connections_and_env(monkeypatch, sample_connection):
    """Test resolution of both connection and environment variables"""
    # Setup environment variables
    monkeypatch.setenv("CONN_NAME", "resolved_conn")
    monkeypatch.setenv("CONN_TYPE", "azure")
    monkeypatch.setenv("API_BASE", "https://api.example.com")
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.setenv("ENV_VAR", "resolved_value")

    evaluator = Evaluator(
        name="test",
        flow="test_flow",
        entry_point="entry.py",
        connections=[deepcopy(sample_connection)],
        env_vars=[{"TEST_VAR": "${ENV_VAR}"}],
        datasets=[]
    )

    evaluator.resolve_variables()

    # Verify connection resolution
    conn = evaluator.connections[0]
    assert conn.name == "resolved_conn"
    assert conn.connection_type == "azure"
    assert conn.api_base == "https://api.example.com"
    assert conn.api_key == "secret"

    # Verify environment resolution
    assert evaluator.resolved_env_vars["TEST_VAR"] == "resolved_value"


def test_resolve_variables_handles_multiple_env_vars(monkeypatch):
    """Test environment variable resolution with multiple entries"""
    monkeypatch.setenv("VAR1", "val1")
    monkeypatch.setenv("VAR2", "val2")

    evaluator = Evaluator(
        name="test",
        flow="flow",
        entry_point="entry.py",
        connections=[],
        env_vars=[
            {"KEY1": "static_val"},
            {"KEY2": "${VAR1}"},
            {"KEY3": "${VAR2}"}
        ],
        datasets=[]
    )

    evaluator.resolve_variables()

    assert evaluator.resolved_env_vars == {
        "KEY1": "static_val",
        "KEY2": "val1",
        "KEY3": "val2"
    }


def test_resolve_variables_raises_on_missing_env_var():
    """Test error handling for missing environment variables"""
    evaluator = Evaluator(
        name="test",
        flow="flow",
        entry_point="entry.py",
        connections=[],
        env_vars=[{"MISSING": "${UNDEFINED_VAR}"}],
        datasets=[]
    )

    with pytest.raises(ValueError, match="Environment variable UNDEFINED_VAR not found"):
        evaluator.resolve_variables()


def test_from_dict_expands_connections(connections_map):
    """Test connection expansion from connection references"""
    data = {
        "name": "test_eval",
        "flow": "test_flow",
        "entry_point": "entry.py",
        "connections_ref": ["valid_conn"],
        "env_vars": [],
        "datasets": []
    }

    evaluator = Evaluator.from_dict(data, connections_map)

    assert len(evaluator.connections) == 1
    assert evaluator.connections[0].name == "${CONN_NAME}"
    assert isinstance(evaluator.connections[0], Connection)


def test_from_dict_raises_missing_connection(connections_map):
    """Test error handling for missing connections in map"""
    data = {
        "name": "test_eval",
        "flow": "test_flow",
        "entry_point": "entry.py",
        "connections_ref": ["missing_conn"],
        "env_vars": [],
        "datasets": []
    }

    with pytest.raises(ValueError, match="Connection missing_conn not found"):
        Evaluator.from_dict(data, connections_map)


def test_from_dict_creates_datasets():
    """Test proper dataset object creation"""
    data = {
        "name": "test",
        "flow": "flow",
        "entry_point": "entry.py",
        "connections_ref": [],
        "env_vars": [],
        "datasets": [
            {
                "name": "test_ds",
                "source": "test_source",
                "description": "Test dataset",
                "mappings": {"input": "data"}
            }
        ]
    }

    evaluator = Evaluator.from_dict(data, {})

    assert len(evaluator.datasets) == 1
    dataset = evaluator.datasets[0]
    assert dataset.name == "test_ds"
    assert dataset.source == "test_source"
    assert dataset.description == "Test dataset"
    assert dataset.mappings == {"input": "data"}


def test_resolve_variables_overwrites_env_vars(monkeypatch):
    """Test that later env_vars entries overwrite earlier ones"""
    monkeypatch.setenv("VAR", "new_value")

    evaluator = Evaluator(
        name="test",
        flow="flow",
        entry_point="entry.py",
        connections=[],
        env_vars=[
            {"DUPLICATE": "initial"},
            {"DUPLICATE": "${VAR}"}
        ],
        datasets=[]
    )

    evaluator.resolve_variables()
    assert evaluator.resolved_env_vars["DUPLICATE"] == "new_value"


def test_non_string_env_vars_are_preserved():
    """Test handling of non-string environment values"""
    evaluator = Evaluator(
        name="test",
        flow="flow",
        entry_point="entry.py",
        connections=[],
        env_vars=[{"NUMERIC": 123}, {"BOOLEAN": True}],
        datasets=[]
    )

    evaluator.resolve_variables()
    assert evaluator.resolved_env_vars["NUMERIC"] == 123
    assert evaluator.resolved_env_vars["BOOLEAN"] is True

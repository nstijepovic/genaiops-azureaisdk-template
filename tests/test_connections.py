import pytest
from llmops.experiment import Connection


# Tests for resolve_variables method
def test_resolve_variables_replaces_single_placeholder():
    """ Test resolution of a single placeholder """
    conn = Connection(
        name="${NAME}",
        connection_type="type",
        api_base="base",
        api_version="version",
        api_key="key",
        api_type="type",
        deployment_name="deploy"
    )
    env_vars = {"NAME": "resolved_name"}
    conn.resolve_variables(env_vars)
    assert conn.name == "resolved_name"


def test_resolve_variables_replaces_multiple_placeholders():
    """ Test resolution of multiple placeholders """
    conn = Connection(
        name="${NAME}",
        connection_type="${TYPE}",
        api_base="${BASE}",
        api_version="${VERSION}",
        api_key="${KEY}",
        api_type="${API_TYPE}",
        deployment_name="${DEPLOY}"
    )
    env_vars = {
        "NAME": "resolved_name",
        "TYPE": "resolved_type",
        "BASE": "resolved_base",
        "VERSION": "resolved_version",
        "KEY": "resolved_key",
        "API_TYPE": "resolved_apitype",
        "DEPLOY": "resolved_deploy"
    }
    conn.resolve_variables(env_vars)
    assert conn.name == "resolved_name"
    assert conn.connection_type == "resolved_type"
    assert conn.api_base == "resolved_base"
    assert conn.api_version == "resolved_version"
    assert conn.api_key == "resolved_key"
    assert conn.api_type == "resolved_apitype"
    assert conn.deployment_name == "resolved_deploy"


def test_resolve_variables_raises_error_on_missing_env_var():
    """ Test error handling for missing environment variable """
    conn = Connection(
        name="test",
        connection_type="type",
        api_base="${BASE}",
        api_version="version",
        api_key="key",
        api_type="type",
        deployment_name="deploy"
    )
    with pytest.raises(ValueError) as exc_info:
        conn.resolve_variables({})
    assert "env var BASE not found" in str(exc_info.value)


def test_resolve_variables_ignores_non_placeholder_strings():
    """ Test that non-placeholder strings are not modified """
    original_api_base = "no_placeholder_here"
    conn = Connection(
        name="test",
        connection_type="type",
        api_base=original_api_base,
        api_version="version",
        api_key="key",
        api_type="type",
        deployment_name="deploy"
    )
    conn.resolve_variables({"SOME_VAR": "value"})
    assert conn.api_base == original_api_base


@pytest.mark.parametrize("field, var_name", [
    ("name", "NAME"),
    ("connection_type", "CONN_TYPE"),
    ("api_base", "API_BASE"),
    ("api_version", "API_VERSION"),
    ("api_key", "API_KEY"),
    ("api_type", "API_TYPE"),
    ("deployment_name", "DEPLOYMENT"),
])
def test_resolve_variables_all_fields(field, var_name):
    """ Test resolution of all fields """
    initial_data = {
        "name": "test",
        "connection_type": "type",
        "api_base": "base",
        "api_version": "version",
        "api_key": "key",
        "api_type": "type",
        "deployment_name": "deploy"
    }
    initial_data[field] = f"${{{var_name}}}"
    conn = Connection(**initial_data)
    env_vars = {var_name: "resolved_value"}
    conn.resolve_variables(env_vars)
    assert getattr(conn, field) == "resolved_value"


# Tests for from_dict classmethod
def test_from_dict_creates_instance_correctly():
    """ Test that Connection instance is created correctly from dict """
    data = {
        "name": "test_conn",
        "connection_type": "azure",
        "api_base": "https://api.azure.com",
        "api_version": "2023-05-15",
        "api_key": "azure_key",
        "api_type": "azure",
        "deployment_name": "deploy1"
    }
    conn = Connection.from_dict(data)
    assert conn.name == data["name"]
    assert conn.connection_type == data["connection_type"]
    assert conn.api_base == data["api_base"]
    assert conn.api_version == data["api_version"]
    assert conn.api_key == data["api_key"]
    assert conn.api_type == data["api_type"]
    assert conn.deployment_name == data["deployment_name"]


def test_from_dict_missing_key_raises_keyerror():
    """ Test error handling for missing key in input dict """
    incomplete_data = {
        "name": "test",
        "connection_type": "type",
        "api_base": "base",
        "api_version": "version",
        "api_key": "key",
        # Missing "api_type" and "deployment_name"
    }
    with pytest.raises(KeyError):
        Connection.from_dict(incomplete_data)

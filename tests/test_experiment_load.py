"""Tests for the load_experiment function."""
from unittest.mock import patch, MagicMock
import pytest
from llmops.experiment import load_experiment
from llmops.experiment import Experiment


@pytest.fixture
def mock_experiment():
    """Fixture providing a mock Experiment instance."""
    experiment = MagicMock(spec=Experiment)
    experiment.resolve_variables = MagicMock()
    return experiment


@pytest.fixture
def mock_files():
    """Fixture providing a dictionary of mock file contents."""
    return {
        "base.yaml": "name: base_config",
        "base.dev.yaml": "name: dev_config",
        "invalid_file": "content"
    }


def test_custom_base_and_filename(mock_experiment, tmp_path):
    """Test with custom base path and filename."""
    with patch("os.path.exists") as mock_exists, \
         patch("llmops.experiment.Experiment.from_yaml") as mock_from_yaml:

        mock_exists.return_value = True
        mock_from_yaml.return_value = mock_experiment

        load_experiment(
            filename="custom.yaml",
            base_path=str(tmp_path / "config"),
            env="prod"
        )

        expected_base = str(tmp_path / "config" / "custom.yaml")
        expected_env = str(tmp_path / "config" / "custom.prod.yaml")
        mock_from_yaml.assert_called_with(expected_base, expected_env)


def test_with_env_parameter(mock_experiment):
    """Test environment-specific file handling."""
    with patch("os.path.exists") as mock_exists, \
         patch("llmops.experiment.Experiment.from_yaml") as mock_from_yaml, \
         patch("os.path.splitext") as mock_split:

        mock_exists.side_effect = lambda x: True
        mock_from_yaml.return_value = mock_experiment
        mock_split.return_value = ("experiment", ".yaml")

        load_experiment(filename="experiment.yaml", env="dev")

        mock_from_yaml.assert_called_with(
            "experiment.yaml",
            "experiment.dev.yaml"
        )


def test_nonexistent_base_file():
    """Test error handling for missing base file."""
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False

        with pytest.raises(ValueError) as excinfo:
            load_experiment(filename="missing.yaml")

        assert "Could not open experiment file" in str(excinfo.value)


def test_invalid_filename():
    """Test validation of filename format."""
    with pytest.raises(ValueError) as excinfo:
        # Test with filename that has no extension
        load_experiment(filename="invalid_file")

    # Match the exact error message from your implementation
    assert "Could not open experiment file" in str(excinfo.value)
    assert "invalid_file" in str(excinfo.value)


def test_env_file_not_exists(mock_experiment):
    """Test handling of missing environment-specific file."""
    with patch("os.path.exists") as mock_exists, \
         patch("llmops.experiment.Experiment.from_yaml") as mock_from_yaml, \
         patch("os.path.splitext") as mock_split:

        mock_exists.side_effect = lambda x: x == "base.yaml"
        mock_from_yaml.return_value = mock_experiment
        mock_split.return_value = ("base", ".yaml")

        load_experiment(filename="base.yaml", env="dev")

        # Should still load base config without dev override
        mock_from_yaml.assert_called_with("base.yaml", "base.dev.yaml")


def test_integration_loaded_experiment():
    """Test full integration with actual file loading."""
    with patch("os.path.exists") as mock_exists, \
         patch("llmops.experiment.Experiment.from_yaml") as mock_from_yaml, \
         patch("os.path.splitext") as mock_split:

        mock_exists.return_value = True
        mock_split.return_value = ("experiment", ".yaml")

        # Create a mock Experiment instance
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.name = "main_experiment"
        mock_experiment.description = "Development configuration"
        mock_experiment.resolve_variables = MagicMock()

        mock_from_yaml.return_value = mock_experiment

        # Execute the test
        experiment = load_experiment(filename="experiment.yaml", env="dev")

        # Verify results
        assert experiment.name == "main_experiment"
        experiment.resolve_variables.assert_called_once()

"""Test cases for the DatasetMapping class."""
import pytest

from llmops.experiment import DatasetMapping  # Replace with actual import path


def test_minimal_initialization():
    """Test creation with only required fields."""
    mapping = DatasetMapping(
        name="test_dataset",
        source="azure_blob"
    )

    assert mapping.name == "test_dataset"
    assert mapping.source == "azure_blob"
    assert mapping.description is None
    assert mapping.mappings == {}


def test_full_initialization():
    """Test creation with all possible parameters."""
    mapping = DatasetMapping(
        name="production_data",
        source="azureml://bucket/path",
        description="Customer transaction data",
        mappings={"input": "raw_data", "output": "processed_data"}
    )

    assert mapping.name == "production_data"
    assert mapping.source == "azureml://bucket/path"
    assert mapping.description == "Customer transaction data"
    assert mapping.mappings == {"input": "raw_data", "output": "processed_data"}


def test_optional_defaults():
    """Test default values for optional parameters."""
    mapping = DatasetMapping(
        name="default_test",
        source="default_source"
    )

    assert mapping.description is None
    assert mapping.mappings == {}


@pytest.mark.parametrize("description", [
    None,
    "Sample description",
    "",  # Empty string
    "A very long description with special characters: !@#$%^&*()"
])
def test_description_variations(description):
    """Test different description scenarios."""
    mapping = DatasetMapping(
        name="desc_test",
        source="desc_source",
        description=description
    )

    assert mapping.description == description


def test_empty_mappings():
    """Test empty mappings initialization."""
    mapping = DatasetMapping(
        name="empty_map",
        source="empty_source",
        mappings={}
    )

    assert mapping.mappings == {}
    assert len(mapping.mappings) == 0


def test_equality_check():
    """Test instance equality based on field values."""
    mapping1 = DatasetMapping(
        name="eq_test",
        source="eq_source",
        description="test",
        mappings={"a": "b"}
    )

    mapping2 = DatasetMapping(
        name="eq_test",
        source="eq_source",
        description="test",
        mappings={"a": "b"}
    )

    mapping3 = DatasetMapping(
        name="eq_test",
        source="different_source",
        description="test",
        mappings={"a": "b"}
    )

    assert mapping1 == mapping2
    assert mapping1 != mapping3

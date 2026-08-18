from unittest.mock import patch

import pytest

from data_fetcher import extract_location_path, resolve_location_parent


def test_extract_location_path_from_v4_account_path():
    assert extract_location_path("accounts/123/locations/456") == "locations/456"


def test_extract_location_path_from_v1_path():
    assert extract_location_path("locations/456") == "locations/456"


def test_extract_location_path_from_bare_id():
    assert extract_location_path("456") == "locations/456"


def test_resolve_location_parent_keeps_full_v4_path():
    assert (
        resolve_location_parent(None, "accounts/1/locations/2") == "accounts/1/locations/2"
    )


def test_resolve_location_parent_joins_v1_path_with_account_name():
    assert (
        resolve_location_parent(None, "locations/2", "accounts/1")
        == "accounts/1/locations/2"
    )


def test_resolve_location_parent_joins_bare_id_with_account_name():
    assert resolve_location_parent(None, "2", "accounts/1") == "accounts/1/locations/2"


@patch("data_fetcher.get_account_for_location")
def test_resolve_location_parent_looks_up_account_for_v1_path(mock_lookup):
    mock_lookup.return_value = "accounts/9/locations/2"
    assert resolve_location_parent("creds", "locations/2") == "accounts/9/locations/2"
    mock_lookup.assert_called_once_with("creds", "locations/2")


@patch("data_fetcher.get_account_for_location")
def test_resolve_location_parent_looks_up_account_for_bare_id(mock_lookup):
    mock_lookup.return_value = "accounts/9/locations/2"
    assert resolve_location_parent("creds", "2") == "accounts/9/locations/2"
    mock_lookup.assert_called_once_with("creds", "locations/2")


@patch("data_fetcher.get_account_for_location")
def test_resolve_location_parent_requires_account_when_lookup_fails(mock_lookup):
    mock_lookup.return_value = "locations/2"
    with pytest.raises(ValueError, match="account_name"):
        resolve_location_parent("creds", "locations/2")

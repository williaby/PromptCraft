"""Smoke tests for the promptcraft package."""

import re

import pytest

import promptcraft


@pytest.mark.unit
def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+.*", promptcraft.__version__)

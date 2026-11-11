import os
from pathlib import Path

import pytest

os.environ.setdefault("POWERBI_MODE", "fixture")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")

from app.catalog import Catalog  # noqa: E402
from app.config import REPO_ROOT, Settings  # noqa: E402
from app.powerbi import FixtureBackend  # noqa: E402


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return Catalog.from_repo(REPO_ROOT / "dax")


@pytest.fixture
def settings() -> Settings:
    return Settings(powerbi_mode="fixture")


@pytest.fixture
def backend(settings) -> FixtureBackend:
    return FixtureBackend(Path(settings.fixture_path))

from pathlib import Path

import pytest

from ..errors import ConfigError
from ..settings import Settings, load_settings


def test_loads_valid_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text('max_age_days: 30\narchive_dir: archive\npatterns: ["*.log"]\n')

    assert load_settings(config) == Settings(
        max_age_days=30,
        archive_dir="archive",
        patterns=("*.log",),
    )


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config not found"):
        load_settings(tmp_path / "missing.yaml")


def test_wrong_type_names_the_key(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        'max_age_days: thirty\narchive_dir: archive\npatterns: ["*.log"]\n'
    )

    with pytest.raises(ConfigError, match="max_age_days"):
        load_settings(config)
